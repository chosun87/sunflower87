from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Transaction, Stock
from schemas import TransactionCreate, ErrorResponse
from portfolio_service import recalculate_portfolio_for_account

router = APIRouter(prefix="/api/transactions", tags=["Transaction"])


@router.get(
    "",
    summary="전체 매매 거래 내역 조회 API",
    description="데이터베이스에 기록된 모든 매수/매도 거래 이력을 거래일시 역순(date DESC)으로 조회하여 반환합니다.",
)
def get_transaction_history(db: Session = Depends(get_db)):
    """최근 거래일시 순(date DESC)으로 전체 매매 거래 내역을 반환합니다."""
    try:
        from database import Account

        # Outer join transaction with account to get account names
        results = (
            db.query(Transaction, Account)
            .outerjoin(Account, Transaction.acc_cd == Account.acc_cd)
            .order_by(Transaction.date.desc())
            .all()
        )
        data = []
        for t, acc in results:
            acc_name = acc.acc_nm if acc else "알 수 없는 계좌"
            acc_company = acc.acc_company_nm if acc else ""
            data.append(
                {
                    "id": t.id,
                    "date": t.date.isoformat(),
                    "type": t.type,
                    "code": t.code,
                    "name": t.name,
                    "quantity": t.quantity,
                    "price": t.price,
                    "acc_cd": t.acc_cd,
                    "acc_nm": acc_name,
                    "acc_company_nm": acc_company,
                    "account_alias": (
                        f"[{acc_company}] {acc_name}" if acc_company else acc_name
                    ),
                }
            )
        return {
            "status": "success",
            "data": data,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch transactions: {str(e)}",
        )


@router.post(
    "/add",
    summary="매매 거래 기록 추가 및 자산 실시간 재계산 API",
    description=(
        "신규 매수/매도 거래를 장부에 기록하고, 해당 계좌의 예수금 및 보유 주식 잔고를 "
        "연대기 순으로 무결성 안전하게 재산출하여 DB에 실시간 반영합니다."
    ),
    responses={
        400: {
            "model": ErrorResponse,
            "description": "매수 잔고(예수금) 부족 또는 과매도 수량 미달 등 유효성 실패",
        },
        404: {
            "model": ErrorResponse,
            "description": "해당 식별자의 계좌(Account)를 찾을 수 없음",
        },
    },
)
def add_transaction(tx_input: TransactionCreate, db: Session = Depends(get_db)):
    """매매 거래 기록을 추가하고 지정된 계좌의 자산을 연대기적으로 재계산합니다."""
    tx_type = tx_input.type.upper()
    if tx_type not in ["BUY", "SELL"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid transaction type. Only BUY or SELL are allowed.",
        )

    if tx_input.quantity <= 0 or tx_input.price <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity and price must be greater than zero.",
        )

    acc_cd = tx_input.acc_cd or "A001"

    try:
        # TransactionCreate validator에 의해 완벽히 정규화되어 들어온 날짜 파싱
        tx_date = datetime.strptime(tx_input.date, "%Y-%m-%d %H:%M:%S")

        # 1. account 테이블에서 해당 계좌를 찾아 예수금 잔고(cash_balance)를 보정/검증
        from database import Account

        account = db.query(Account).filter(Account.acc_cd == acc_cd).first()
        if not account:
            raise HTTPException(
                status_code=404,
                detail=f"Account with code '{acc_cd}' not found.",
            )

        cost = tx_input.quantity * tx_input.price
        if tx_type == "BUY":
            if account.cash_balance < cost:
                err_msg = (
                    f"Insufficient cash balance. Required: {cost:,.0f} KRW, "
                    f"Available: {account.cash_balance:,.0f} KRW."
                )
                raise HTTPException(
                    status_code=400,
                    detail=err_msg,
                )
            account.cash_balance -= cost

            # 2. stocks 테이블에서 WHERE acc_cd = :acc_cd AND code = :code
            # 조건으로 현재고 보정
            stock = (
                db.query(Stock)
                .filter(Stock.acc_cd == acc_cd, Stock.code == tx_input.code)
                .first()
            )
            if stock:
                new_qty = stock.quantity + tx_input.quantity
                new_avg = (stock.quantity * stock.avg_price + cost) / new_qty
                stock.quantity = new_qty
                stock.avg_price = round(new_avg, 2)
                stock.current_price = tx_input.price
            else:
                stock = Stock(
                    code=tx_input.code,
                    acc_cd=acc_cd,
                    name=tx_input.name,
                    quantity=tx_input.quantity,
                    avg_price=tx_input.price,
                    current_price=tx_input.price,
                )
                db.add(stock)
        elif tx_type == "SELL":
            # stocks 테이블에서 WHERE acc_cd = :acc_cd AND code = :code 조건으로 현재고 보정
            stock = (
                db.query(Stock)
                .filter(Stock.acc_cd == acc_cd, Stock.code == tx_input.code)
                .first()
            )
            if not stock or stock.quantity < tx_input.quantity:
                raise HTTPException(
                    status_code=400,
                    detail="Insufficient stock holdings for SELL transaction.",
                )
            account.cash_balance += cost
            if stock.quantity == tx_input.quantity:
                db.delete(stock)
            else:
                stock.quantity -= tx_input.quantity

        new_tx = Transaction(
            type=tx_type,
            code=tx_input.code,
            name=tx_input.name,
            quantity=tx_input.quantity,
            price=tx_input.price,
            acc_cd=acc_cd,
            date=tx_date,
        )
        db.add(new_tx)
        db.flush()

        # 자산 포트폴리오 연대기 재계산 수행으로 완벽한 데이터 무결성 보장
        recalculate_portfolio_for_account(db, acc_cd)

        db.commit()
        return {
            "status": "success",
            "message": (
                "Transaction recorded and portfolio recalculated " "successfully."
            ),
        }
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Database transaction failed: {str(e)}",
        )


@router.delete(
    "/{tx_id}",
    summary="거래 기록 삭제 및 자산 역산 복원 API",
    description=(
        "지정된 고유 ID의 거래 데이터를 장부에서 안전하게 제거하고, 기존 거래 내역을 처음부터 "
        "다시 누적 추적함으로써 해당 계좌의 자산을 거래 이전 상태로 역산하여 원상복귀시킵니다."
    ),
    responses={
        400: {
            "model": ErrorResponse,
            "description": (
                "삭제 후 역산 과정에서 자산이 마이너스가 되는 등의 역산 유효성 실패"
            ),
        },
        404: {
            "model": ErrorResponse,
            "description": "삭제 요청한 ID의 거래 기록을 찾을 수 없음",
        },
    },
)
def delete_transaction(tx_id: int, db: Session = Depends(get_db)):
    """지정된 거래를 삭제하고 해당 계좌의 포트폴리오를 역산(Rollback)하여 원상복귀시킵니다."""
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
    if not tx:
        raise HTTPException(
            status_code=404,
            detail=f"Transaction with ID {tx_id} not found.",
        )

    acc_cd = tx.acc_cd
    try:
        db.delete(tx)
        db.flush()

        # 거래가 제거된 상태로 해당 계좌의 자산을 연대기적 재계산하여 역산 수행
        recalculate_portfolio_for_account(db, acc_cd)

        db.commit()
        return {
            "status": "success",
            "message": ("Transaction deleted and portfolio reversed " "successfully."),
        }
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete transaction: {str(e)}",
        )


@router.put(
    "/{tx_id}",
    summary="거래 수정 및 포트폴리오 안전 재반영 API",
    description=(
        "기존 거래 내역 데이터를 완전히 수정하며, 기존 계좌와 신규 계좌의 예수금 및 "
        "주식 포트폴리오 자산을 분리하여 연대기적으로 완벽하게 재산출 및 복원 처리합니다."
    ),
    responses={
        400: {
            "model": ErrorResponse,
            "description": (
                "수정 후 기존/신규 계좌의 자산이 마이너스가 되는 등의 역산 유효성 실패"
            ),
        },
        404: {
            "model": ErrorResponse,
            "description": "수정 요청한 ID의 거래 기록 또는 관련 계좌를 찾을 수 없음",
        },
    },
)
def update_transaction(
    tx_id: int, tx_input: TransactionCreate, db: Session = Depends(get_db)
):
    """기존 거래 데이터를 변경하고, 기존 계좌와 신규 계좌의 포트폴리오를 트랜잭션 안전하게 동시 역산 및 재반영합니다."""
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
    if not tx:
        raise HTTPException(
            status_code=404,
            detail=f"Transaction with ID {tx_id} not found.",
        )

    old_acc_cd = tx.acc_cd
    new_acc_cd = tx_input.acc_cd or "A001"

    tx_type = tx_input.type.upper()
    if tx_type not in ["BUY", "SELL"]:
        raise HTTPException(
            status_code=400,
            detail="Invalid transaction type. Only BUY or SELL are allowed.",
        )

    if tx_input.quantity <= 0 or tx_input.price <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity and price must be greater than zero.",
        )

    try:
        # TransactionCreate validator에 의해 완벽히 정규화되어 들어온 날짜 파싱
        tx_date = datetime.strptime(tx_input.date, "%Y-%m-%d %H:%M:%S")

        # 데이터 업데이트
        tx.type = tx_type
        tx.code = tx_input.code
        tx.name = tx_input.name
        tx.quantity = tx_input.quantity
        tx.price = tx_input.price
        tx.acc_cd = new_acc_cd
        tx.date = tx_date

        db.flush()

        # 이전 계좌와 새 계좌의 포트폴리오를 둘 다 안전하게 연대기 재산출
        recalculate_portfolio_for_account(db, old_acc_cd)
        if old_acc_cd != new_acc_cd:
            recalculate_portfolio_for_account(db, new_acc_cd)

        db.commit()
        return {
            "status": "success",
            "message": (
                "Transaction updated and portfolio recalculated " "successfully."
            ),
        }
    except HTTPException as he:
        db.rollback()
        raise he
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Failed to update transaction: {str(e)}",
        )

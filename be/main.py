import re
from pathlib import Path
from typing import Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# 모듈화된 계층 및 DB 관련 임포트
from git_service import commit_and_push_task
from database import init_db, get_db, Transaction, Stock

# 보안 지침: 환경변수 로드
load_dotenv()


# 기획자 MOON(무니)의 태스크 업로드 스펙 규격 정의
class TaskCreate(BaseModel):
    filename: str = Field(
        ...,
        description="저장할 마크다운 태스크 파일명 (예: TASK-04-SWAGGER_DOCUMENTATION_BE_R1.md)",
        examples=["TASK-04-SWAGGER_DOCUMENTATION_BE_R1.md"],
    )
    content: str = Field(
        ...,
        description="마크다운 태스크 파일에 기록할 상세 지침/내용",
        examples=["# TASK-04 상세..."],
    )


# 매매 거래 추가용 Pydantic 모델 정의
class TransactionCreate(BaseModel):
    type: str = Field(
        ...,
        description="매매 구분 (BUY: 매수, SELL: 매도)",
        examples=["BUY"],
    )
    code: str = Field(
        ...,
        description="종목/ETF 6자리 고유 코드",
        examples=["005930"],
    )
    name: str = Field(
        ...,
        description="종목/ETF 명칭",
        examples=["삼성전자"],
    )
    quantity: int = Field(
        ...,
        description="매매 수량 (양의 정수)",
        examples=[10],
    )
    price: int = Field(
        ...,
        description="매매 단가 (양의 정수)",
        examples=[77000],
    )
    acc_code: Optional[str] = Field(
        "",
        description="account 테이블의 acc_cd 참조 키 (acc_code, accCode, account_number 호환)",
        examples=["A001"],
    )
    date: Optional[str] = Field(
        None,
        description="거래일시 문자열 (포맷: YYYY-MM-DD HH:MM:SS 또는 ISO 8601)",
        examples=["2026-05-17 23:25:46"],
    )


# 에러 응답 규격용 Pydantic 모델 정의
class ErrorResponse(BaseModel):
    detail: str = Field(
        ...,
        description="에러 및 예외 상세 설명 메세지",
        examples=["Insufficient cash balance. Required: 770k, Available: 0."],
    )


app = FastAPI(
    title="sunflower87 API 코어",
    description="미래에셋 멀티 계좌 및 AI 주식 추천 시스템",
    version="0.1.0",
)

# 데이터베이스 테이블 초기화 (startup 시점에 안전하게 구동)
init_db()

# Phase 1: 로컬 개발 환경용 CORS 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_stocks_master():
    try:
        from pykrx import stock
        from datetime import datetime, timedelta

        # 최신 영업일을 찾기 위해 오늘부터 역산
        current_date = datetime.now()
        for i in range(10):
            date_str = (current_date - timedelta(days=i)).strftime("%Y%m%d")
            try:
                # 1. 일반 주식 (KOSPI/KOSDAQ) 마스터 가져오기
                kospi_dict = stock.get_market_ticker_and_name(date_str, market="KOSPI")
                kosdaq_dict = stock.get_market_ticker_and_name(
                    date_str, market="KOSDAQ"
                )

                # 2. ETF 마스터 가져오기 (TIGER, KODEX 등 누락 해결)
                etf_dict = stock.get_etf_ticker_and_name(date_str)

                if kospi_dict or kosdaq_dict or etf_dict:
                    integrated = {}
                    if kospi_dict:
                        integrated.update(kospi_dict)
                    if kosdaq_dict:
                        integrated.update(kosdaq_dict)
                    if etf_dict:
                        integrated.update(etf_dict)

                    print(
                        f"Loaded {len(integrated)} integrated stocks/ETFs "
                        f"from pykrx for date {date_str}"
                    )
                    return integrated
            except Exception as e:
                print(f"Failed to fetch integrated tickers for {date_str}: {e}")
                continue
    except Exception as e:
        print(f"Failed to load pykrx: {e}")

    print("Failed to fetch tickers from pykrx and no offline fallback master is used.")
    return {}


@app.get(
    "/api/stocks/search",
    tags=["Market Stock"],
    summary="종목 검색 자동완성 API",
    description=(
        "입력된 키워드(종목명 또는 종목코드)를 기반으로 매칭되는 주식/ETF 목록을 반환합니다. "
        "Cache Aside 패턴에 따라 DB 캐시 조회를 우선 수행합니다."
    ),
)
def search_stocks(keyword: str = "", db: Session = Depends(get_db)):
    """종목명을 기반으로 종목코드를 자동 검색합니다 (부분 일치).

    API 호출방식, 응답 예시 및 규격:
    - Method: GET
    - URL: /api/stocks/search
    - Query Parameters:
        - keyword (str): 검색할 종목명 또는 종목코드 일부 (예: "삼성")
    - 응답 규격 (성공 예시):
        {
            "status": "success",
            "results": [
                {"code": "005930", "name": "삼성전자"},
                {"code": "009150", "name": "삼성전기"}
            ]
        }
    - 응답 규격 (에러 예시):
        {
            "detail": "에러 내용 설명"
        }
    """
    if not keyword:
        return {"status": "success", "results": []}

    from database import CacheStock
    from sqlalchemy import func

    # [1단계] 로컬 DB 선검색 (Cache Hit 시도)
    keyword_lower = keyword.lower()
    db_results = (
        db.query(CacheStock)
        .filter(func.lower(CacheStock.stock_name).like(f"%{keyword_lower}%"))
        .all()
    )

    if db_results:
        results = [{"code": r.stock_code, "name": r.stock_name} for r in db_results]
        return {"status": "success", "results": results[:10]}

    # [2단계] 외부 데이터 로드 및 통합 (Cache Miss 대응)
    stocks_master = get_stocks_master()
    matched_stocks = []

    for code, name in stocks_master.items():
        if keyword_lower in name.lower() or keyword_lower in code:
            matched_stocks.append({"code": code, "name": name})

    # [3단계] 로컬 DB 적재 및 반환 (Cache Fill)
    if matched_stocks:
        for ms in matched_stocks:
            # 중복 방지를 위해 확인 후 INSERT
            existing = (
                db.query(CacheStock).filter(CacheStock.stock_code == ms["code"]).first()
            )
            if not existing:
                cache_item = CacheStock(stock_code=ms["code"], stock_name=ms["name"])
                db.add(cache_item)
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Failed to commit cached stocks: {e}")

    return {"status": "success", "results": matched_stocks[:10]}


def get_enriched_accounts_data(db: Session) -> dict:
    """SQLite 데이터베이스 account 및 stocks 테이블의 데이터를 로드하고
    실시간 수익률 및 평가액을 계산하여 프런트엔드 규격에 맞춰 반환합니다.
    """
    from database import Account, Stock

    # 1. 활성 계좌 목록 로드 (dt_deleted IS NULL, acc_order ASC)
    db_accounts = (
        db.query(Account)
        .filter(Account.dt_deleted.is_(None))
        .order_by(Account.acc_order.asc())
        .all()
    )

    # 2. 보유 주식 목록 로드
    db_stocks = db.query(Stock).all()

    # 계좌별 주식 분배 사전 초기화
    account_stocks_map = {acc.acc_cd: [] for acc in db_accounts}

    # DB에 존재하는 주식을 각각의 계좌 번호에 따라 올바르게 분배 및 계산
    for stock in db_stocks:
        acct_code = stock.acc_code or ""
        if acct_code not in account_stocks_map:
            account_stocks_map[acct_code] = []

        code = stock.code
        name = stock.name
        quantity = stock.quantity
        avg_price = stock.avg_price
        current_price = stock.current_price

        # 수익률 계산
        eval_profit_rate = (
            round(((current_price - avg_price) / avg_price) * 100, 2)
            if avg_price > 0
            else 0.0
        )

        account_stocks_map[acct_code].append(
            {
                "code": code,
                "name": name,
                "quantity": quantity,
                "avg_price": avg_price,
                "current_price": current_price,
                "eval_profit_rate": eval_profit_rate,
            }
        )

    accounts = []
    overall_total_eval = 0

    # 각 계좌별로 계산 및 DTO 조립
    for acc in db_accounts:
        stocks_list = account_stocks_map.get(acc.acc_cd, [])

        # 주식 평가액 계산
        stocks_purchase = sum(s["quantity"] * s["avg_price"] for s in stocks_list)
        stocks_eval = sum(s["quantity"] * s["current_price"] for s in stocks_list)

        # 총 평가금액 (주식 평가액 + 현금 잔고)
        total_eval = stocks_eval + acc.cash_balance
        # 총 매입금액 (주식 매입금액 + 현금 잔고)
        total_purchase = stocks_purchase + acc.cash_balance

        # 수익률 계산
        profit_rate = (
            round(((total_eval - total_purchase) / total_purchase) * 100, 2)
            if total_purchase > 0
            else 0.0
        )

        accounts.append(
            {
                "id": acc.acc_cd,
                "account_number": acc.acc_cd,
                "alias": f"[{acc.acc_company_nm}] {acc.acc_nm}",
                "balance": acc.cash_balance,  # 예수금 잔액 전달
                "total_eval": total_eval,  # 총 평가액
                "profit_rate": profit_rate,  # 계좌 총 수익률
                "stocks": stocks_list,
            }
        )
        overall_total_eval += total_eval

    return {
        "status": "success",
        "total_asset": overall_total_eval,
        "accounts": accounts,
    }


@app.get(
    "/api/accounts",
    tags=["Account"],
    summary="총자산 및 계좌별 세부 자산 현황 조회 API",
    description=(
        "SQLite 데이터베이스의 account 및 stocks 테이블을 통합 조회하여 "
        "총 자산 평가액, 계좌별 예수금, 주식 보유 내역 및 실시간 평가 수익률을 동적으로 계산해 반환합니다."
    ),
)
def get_miraeasset_accounts(db: Session = Depends(get_db)):
    """SQLite 데이터베이스 account 및 stocks 테이블을 기반으로 총자산 및 계좌별 세부 자산 현황을 반환합니다.

    API 호출방식, 응답 예시 및 규격:
    - Method: GET
    - URL: /api/accounts
    - 응답 규격 (성공 예시):
        {
            "status": "success",
            "total_asset": 39800000.0,
            "accounts": [
                {
                    "id": "A001",
                    "account_number": "A001",
                    "alias": "[미래에셋증권] 주식계좌 1",
                    "balance": 39800000.0,
                    "total_eval": 39800000.0,
                    "profit_rate": 0.0,
                    "stocks": []
                }
            ]
        }
    """
    return get_enriched_accounts_data(db)


@app.get(
    "/api/transactions",
    tags=["Transaction"],
    summary="전체 매매 거래 내역 조회 API",
    description="데이터베이스에 기록된 모든 매수/매도 거래 이력을 거래일시 역순(date DESC)으로 조회하여 반환합니다.",
)
def get_transaction_history(db: Session = Depends(get_db)):
    """최근 거래일시 순(date DESC)으로 전체 매매 거래 내역을 반환합니다.

    API 호출방식, 응답 예시 및 규격:
    - Method: GET
    - URL: /api/transactions
    - 응답 규격 (성공 예시):
        {
            "status": "success",
            "data": [
                {
                    "id": 1,
                    "date": "2026-05-17T23:25:46",
                    "type": "BUY",
                    "code": "005930",
                    "name": "삼성전자",
                    "quantity": 10,
                    "price": 77000.0,
                    "acc_code": "A001",
                    "accCode": "A001",
                    "account_number": "A001",
                    "acc_nm": "주식계좌 1",
                    "acc_company_nm": "미래에셋증권",
                    "account_alias": "[미래에셋증권] 주식계좌 1"
                }
            ]
        }
    """
    try:
        from database import Account

        # Outer join transaction with account to get account names
        results = (
            db.query(Transaction, Account)
            .outerjoin(Account, Transaction.acc_code == Account.acc_cd)
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
                    "acc_code": t.acc_code,
                    "accCode": t.acc_code,
                    "account_number": t.acc_code,
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
            detail=f"Failed to fetch transaction history: {str(e)}",
        )


def recalculate_portfolio_for_account(db: Session, acc_code: str):
    """지정된 계좌의 전체 거래 내역을 연대기순으로 처음부터 끝까지 추적해
    최종 보유 수량, 평단가 및 예수금 잔고(cash_balance)를 오차 없이 정밀 복원하고
    stocks 및 account 테이블에 동기화합니다.
    어느 시점이든 보유 수량이나 예수금 잔고가 마이너스가 되면 즉각 400 에러를 발생시킵니다.
    """
    from database import Account, Stock

    account = db.query(Account).filter(Account.acc_cd == acc_code).first()
    if not account:
        raise HTTPException(
            status_code=404, detail=f"Account with code '{acc_code}' not found."
        )

    # 1. 초기 자산 설정 (모든 계좌는 하드코딩 없이 현금 0원 및 보유 주식 없음 상태에서 시작합니다)
    holdings = {}
    initial_cash = 0.0

    cash_balance = initial_cash

    # 2. 해당 계좌의 모든 거래 기록을 연대기순으로 로드 (date 및 id 기준 오름차순 정렬)
    txs = (
        db.query(Transaction)
        .filter(Transaction.acc_code == acc_code)
        .order_by(Transaction.date.asc(), Transaction.id.asc())
        .all()
    )

    # 3. 거래 내역을 차례로 시뮬레이션 적용하여 평단가 및 예수금 역산
    for tx in txs:
        code = tx.code
        name = tx.name
        qty = tx.quantity
        price = tx.price
        cost = qty * price

        if tx.type == "BUY":
            # 매수 시 현금 차감 (예수금 부족 시 에러 유발)
            if cash_balance < cost:
                detail_err = (
                    f"Insufficient cash balance for BUY transaction. "
                    f"Required: {cost:,.0f} KRW, Available: {cash_balance:,.0f} KRW."
                )
                raise HTTPException(status_code=400, detail=detail_err)
            cash_balance -= cost

            # 주식 보유고 갱신
            if code in holdings:
                existing = holdings[code]
                total_qty = existing["quantity"] + qty
                weighted_avg = (
                    (existing["quantity"] * existing["avg_price"]) + cost
                ) / total_qty
                existing["quantity"] = total_qty
                existing["avg_price"] = round(weighted_avg, 2)
            else:
                holdings[code] = {
                    "name": name,
                    "quantity": qty,
                    "avg_price": price,
                }
        elif tx.type == "SELL":
            # 매도 시 현금 합산
            cash_balance += cost

            # 주식 보유고 갱신 (보유 주식 부족 시 에러 유발)
            if code not in holdings or holdings[code]["quantity"] < qty:
                detail_err = (
                    f"Insufficient stock holdings for SELL transaction. "
                    f"Holdings for {name} ({code}) falls below zero."
                )
                raise HTTPException(status_code=400, detail=detail_err)

            existing = holdings[code]
            remaining = existing["quantity"] - qty
            if remaining == 0:
                del holdings[code]
            else:
                existing["quantity"] = remaining

    # 4. DB 테이블 동기화 (예수금 잔고 반영 및 stocks 테이블 완전 청소 후 재생성)
    account.cash_balance = cash_balance

    db.query(Stock).filter(Stock.acc_code == acc_code).delete()

    for code, info in holdings.items():
        new_stock = Stock(
            code=code,
            acc_code=acc_code,
            name=info["name"],
            quantity=info["quantity"],
            avg_price=info["avg_price"],
            current_price=int(info["avg_price"]),
        )
        db.add(new_stock)


@app.post(
    "/api/transactions/add",
    tags=["Transaction"],
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
    """매매 거래 기록을 추가하고 지정된 계좌의 자산을 연대기적으로 재계산합니다.

    API 호출방식, 응답 예시 및 규격:
    - Method: POST
    - URL: /api/transactions/add
    - Request Body (Payload Schema):
        {
            "type": "BUY",                # 거래 종류 (BUY 또는 SELL)
            "code": "005930",             # 종목코드
            "name": "삼성전자",            # 종목명
            "quantity": 10,               # 거래 수량 (양의 정수)
            "price": 77000.0,             # 거래 단가 (양의 실수)
            "acc_code": "A001",           # 계좌 식별자 (acc_code 등 호환)
            "date": "2026-05-17 23:25:46"  # (선택) 거래일시
        }
    - 응답 규격 (성공 예시):
        {
            "status": "success",
            "message": "Transaction recorded and portfolio recalculated successfully."
        }
    - 응답 규격 (실패 예시 - 예수금/잔고 부족 등):
        HTTP 400 Bad Request
        {
            "detail": "Insufficient cash balance. Required: 770k, Available: 0."
        }
    """
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

    acc_code = (
        tx_input.acc_code or tx_input.accCode or tx_input.account_number or "A001"
    )

    try:
        # 거래일시 파싱 및 자동 복원
        if not tx_input.date:
            tx_date = datetime.now()
        else:
            try:
                tx_date = datetime.strptime(tx_input.date, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    cleaned_date = tx_input.date.replace("Z", "+00:00")
                    tx_date = datetime.fromisoformat(cleaned_date)
                except Exception:
                    tx_date = datetime.now()

        # 1. account 테이블에서 해당 계좌를 찾아 예수금 잔고(cash_balance)를 보정/검증
        from database import Account

        account = db.query(Account).filter(Account.acc_cd == acc_code).first()
        if not account:
            raise HTTPException(
                status_code=404, detail=f"Account with code '{acc_code}' not found."
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

            # 2. stocks 테이블에서 WHERE acc_code = :acc_code AND code = :code 조건으로 현재고 보정
            stock = (
                db.query(Stock)
                .filter(Stock.acc_code == acc_code, Stock.code == tx_input.code)
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
                    acc_code=acc_code,
                    name=tx_input.name,
                    quantity=tx_input.quantity,
                    avg_price=tx_input.price,
                    current_price=tx_input.price,
                )
                db.add(stock)
        elif tx_type == "SELL":
            # stocks 테이블에서 WHERE acc_code = :acc_code AND code = :code 조건으로 현재고 보정
            stock = (
                db.query(Stock)
                .filter(Stock.acc_code == acc_code, Stock.code == tx_input.code)
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
            acc_code=acc_code,
            date=tx_date,
        )
        db.add(new_tx)
        db.flush()

        # 자산 포트폴리오 연대기 재계산 수행으로 완벽한 데이터 무결성 보장
        recalculate_portfolio_for_account(db, acc_code)

        db.commit()
        return {
            "status": "success",
            "message": "Transaction recorded and portfolio recalculated successfully.",
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


@app.delete(
    "/api/transactions/{tx_id}",
    tags=["Transaction"],
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
    """지정된 거래를 삭제하고 해당 계좌의 포트폴리오를 역산(Rollback)하여 원상복귀시킵니다.

    API 호출방식, 응답 예시 및 규격:
    - Method: DELETE
    - URL: /api/transactions/{tx_id}
    - Path Parameters:
        - tx_id (int): 삭제할 거래 ID
    - 응답 규격 (성공 예시):
        {
            "status": "success",
            "message": "Transaction deleted and portfolio reversed successfully."
        }
    """
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
    if not tx:
        raise HTTPException(
            status_code=404,
            detail=f"Transaction with ID {tx_id} not found.",
        )

    acc_code = tx.acc_code
    try:
        db.delete(tx)
        db.flush()

        # 거래가 제거된 상태로 해당 계좌의 자산을 연대기적 재계산하여 역산 수행
        recalculate_portfolio_for_account(db, acc_code)

        db.commit()
        return {
            "status": "success",
            "message": "Transaction deleted and portfolio reversed successfully.",
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


@app.put(
    "/api/transactions/{tx_id}",
    tags=["Transaction"],
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
    """기존 거래 데이터를 변경하고, 기존 계좌와 신규 계좌의 포트폴리오를 트랜잭션 안전하게 동시 역산 및 재반영합니다.

    API 호출방식, 응답 예시 및 규격:
    - Method: PUT
    - URL: /api/transactions/{tx_id}
    - Path Parameters:
        - tx_id (int): 수정할 거래 ID
    - Request Body (Payload Schema):
        TransactionCreate와 동일 포맷
    - 응답 규격 (성공 예시):
        {
            "status": "success",
            "message": "Transaction updated and portfolio recalculated successfully."
        }
    """
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
    if not tx:
        raise HTTPException(
            status_code=404,
            detail=f"Transaction with ID {tx_id} not found.",
        )

    old_acc_code = tx.acc_code
    new_acc_code = (
        tx_input.acc_code or tx_input.accCode or tx_input.account_number or "A001"
    )

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
        if not tx_input.date:
            tx_date = datetime.now()
        else:
            try:
                tx_date = datetime.strptime(tx_input.date, "%Y-%m-%d %H:%M:%S")
            except ValueError:
                try:
                    cleaned_date = tx_input.date.replace("Z", "+00:00")
                    tx_date = datetime.fromisoformat(cleaned_date)
                except Exception:
                    tx_date = datetime.now()

        # 데이터 업데이트
        tx.type = tx_type
        tx.code = tx_input.code
        tx.name = tx_input.name
        tx.quantity = tx_input.quantity
        tx.price = tx_input.price
        tx.acc_code = new_acc_code
        tx.date = tx_date

        db.flush()

        # 이전 계좌와 새 계좌의 포트폴리오를 둘 다 안전하게 연대기 재산출
        recalculate_portfolio_for_account(db, old_acc_code)
        if old_acc_code != new_acc_code:
            recalculate_portfolio_for_account(db, new_acc_code)

        db.commit()
        return {
            "status": "success",
            "message": "Transaction updated and portfolio recalculated successfully.",
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


@app.get(
    "/api/recommendations",
    tags=["Market Stock"],
    summary="AI 추천 종목 조회 API",
    description=(
        "오늘 날짜를 기준으로 AI가 정밀 선별한 우량 가치주, 성장주, 배당주 추천 목록과 "
        "추천 이유 및 분석 점수를 함께 반환합니다."
    ),
)
def get_ai_recommendations(db: Session = Depends(get_db)):
    """오늘 날짜에 맞춘 주식 가치주/성장주 목록 추천 데이터를 반환합니다 (R1 명세 준수).

    API 호출방식, 응답 예시 및 규격:
    - Method: GET
    - URL: /api/recommendations
    - 응답 규격 (성공 예시):
        {
            "status": "success",
            "date": "20260517",
            "data": [
                {
                    "name": "삼성전자",
                    "code": "005930",
                    "tag": "가치주",
                    "reason": "외국인 최근 5일 연속 순매수세 유입 및 20일 이동평균선 지지 확인.",
                    "score": 92
                }
            ]
        }
    """
    from database import Recommendation

    current_date = datetime.now().strftime("%Y%m%d")
    db_recs = db.query(Recommendation).all()

    data = []
    for r in db_recs:
        data.append(
            {
                "name": r.name,
                "code": r.code,
                "tag": r.tag,
                "reason": r.reason,
                "score": r.score,
            }
        )

    return {
        "status": "success",
        "date": current_date,
        "data": data,
    }


@app.post(
    "/api/tasks",
    tags=["Task"],
    summary="기획 마크다운 태스크 생성 및 원격 Git 동기화 API",
    description=(
        "입력받은 파일명과 마크다운 내용을 기반으로 로컬 프로젝트 docs/tasks 폴더 내에 "
        "명세서를 물리 작성하고, Git 형상관리를 통해 원격 리포지토리에 자동 Push합니다."
    ),
)
def create_task(task: TaskCreate):
    """지정된 이름과 내용을 기반으로 docs/tasks 디렉토리에 마크다운 형식 태스크 파일을 생성하고,

    Git에 자동으로 add, commit, push합니다. (보안 및 트래버스 방어 적용)
    """
    # 1. 파일 이름 유효성 검사 (디렉토리 트래버스 공격 차단 및 .md 확장자 확인)
    if not re.match(r"^[A-Za-z0-9\-_]+\.md$", task.filename):
        detail_msg = (
            "Invalid filename. Only alphanumeric, hyphens, "
            "underscores and .md extension are allowed."
        )
        raise HTTPException(
            status_code=400,
            detail=detail_msg,
        )

    # 2. 경로 설정 (프로젝트 루트의 docs/tasks)
    be_dir = Path(__file__).parent.resolve()
    project_root = be_dir.parent
    docs_tasks_dir = project_root / "docs" / "tasks"

    # docs/tasks 폴더가 없으면 자동 생성
    docs_tasks_dir.mkdir(parents=True, exist_ok=True)
    file_path = docs_tasks_dir / task.filename

    # 3. 파일 작성
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(task.content)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to write file: {str(e)}",
        )

    # 4. Git 커밋 및 푸시 연동 처리 (GitService에 위임)
    git_result = commit_and_push_task(file_path, task.filename, project_root)

    msg = f"Task file '{task.filename}' successfully written."
    return {
        "status": "success",
        "message": msg,
        "path": str(file_path.relative_to(project_root)),
        "git": git_result,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

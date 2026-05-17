import re
from pathlib import Path
from typing import Optional
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv
from sqlalchemy.orm import Session

# 모듈화된 계층 및 DB 관련 임포트
from git_service import commit_and_push_task
from database import init_db, get_db, Transaction, Stock

# 보안 지침: 환경변수 로드
load_dotenv()


# 기획자 MOON(무니)의 태스크 업로드 스펙 규격 정의
class TaskCreate(BaseModel):
    filename: str
    content: str


# 매매 거래 추가용 Pydantic 모델 정의
class TransactionCreate(BaseModel):
    type: str  # BUY / SELL
    code: str
    name: str
    quantity: int
    price: int
    acc_code: Optional[str] = ""
    date: Optional[str] = None


app = FastAPI(title="sunflower87 API")

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

_stocks_cache = {}


def get_stocks_master():
    global _stocks_cache
    if _stocks_cache:
        return _stocks_cache

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

                    _stocks_cache = integrated
                    print(
                        f"Loaded {len(_stocks_cache)} integrated stocks/ETFs "
                        f"from pykrx for date {date_str}"
                    )
                    return _stocks_cache
            except Exception as e:
                print(f"Failed to fetch integrated tickers for {date_str}: {e}")
                continue
    except Exception as e:
        print(f"Failed to load pykrx: {e}")

    # Fallback 종목 마스터 데이터 선언 (오프라인/네트워크 오류 및 D.O.D. 대응용)
    if not _stocks_cache:
        _stocks_cache = {
            "005930": "삼성전자",
            "005380": "현대차",
            "000660": "SK하이닉스",
            "035420": "네이버",
            "035720": "카카오",
            "373220": "LG에너지솔루션",
            "068270": "셀트리온",
            "005490": "POSCO홀딩스",
            "000270": "기아",
            "105560": "KB금융",
            "055550": "신한지주",
            "003550": "LG",
            "032830": "삼성생명",
            "015760": "한국전력",
            "034730": "SK",
            "090430": "아모레퍼시픽",
            "017670": "SK텔레콤",
            "011200": "HMM",
            "034020": "두산에너빌리티",
            "326030": "SK바이오사이언스",
            "000100": "유한양행",
            "009150": "삼성전기",
            "010140": "삼성중공업",
            "018260": "삼성에스디에스",
            "033780": "KT&G",
            "030200": "KT",
            "003490": "대한항공",
            # D.O.D. 및 핵심 피드백 사항 추가 선언
            "042660": "한화오션",
            "102110": "TIGER 200",
            "069500": "KODEX 200",
            "272580": "KODEX 200액티브",
            "360750": "TIGER 미국S&P500",
        }
        print(
            f"Using integrated offline fallback stocks master "
            f"(size: {len(_stocks_cache)})"
        )

    return _stocks_cache


@app.get("/api/stocks/search")
def search_stocks(keyword: str = ""):
    """종목명을 기반으로 종목코드를 자동 검색합니다 (부분 일치)."""
    if not keyword:
        return {"status": "success", "results": []}

    stocks_master = get_stocks_master()
    results = []

    keyword_lower = keyword.lower()
    for code, name in stocks_master.items():
        if keyword_lower in name.lower() or keyword_lower in code:
            results.append({"code": code, "name": name})

    return {"status": "success", "results": results[:10]}


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


@app.get("/api/accounts")
def get_miraeasset_accounts(db: Session = Depends(get_db)):
    """SQLite 데이터베이스 stocks 테이블의 데이터를 기반으로 현재 총자산을 동적 계산하여 반환합니다."""
    return get_enriched_accounts_data(db)


@app.get("/api/transactions")
def get_transaction_history(db: Session = Depends(get_db)):
    """최근 거래일시 순(ORDER BY date DESC)으로 매매 거래 내역을 반환합니다."""
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

    # 1. 초기 씨드 자산 설정 (A001 계좌만 초기 보유 주식이 있고, 현금 39,800,000.0원으로 시작)
    holdings = {}
    if acc_code == "A001":
        initial_cash = 39800000.0
        holdings = {
            "005930": {"name": "삼성전자", "quantity": 100, "avg_price": 72500.0},
            "005380": {"name": "현대차", "quantity": 30, "avg_price": 240000.0},
        }
    else:
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

    # Use baseline map for seeded stocks if they don't have transaction history,
    # otherwise use latest price
    current_prices_map = {
        "005930": 77000,
        "000660": 147000,
        "005380": 250000,
        "035420": 185000,
        "360750": 14250,
        "069500": 34650,
    }

    for code, info in holdings.items():
        current_p = current_prices_map.get(code, int(info["avg_price"]))
        new_stock = Stock(
            code=code,
            acc_code=acc_code,
            name=info["name"],
            quantity=info["quantity"],
            avg_price=info["avg_price"],
            current_price=current_p,
        )
        db.add(new_stock)


@app.post("/api/transactions/add")
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


@app.delete("/api/transactions/{tx_id}")
def delete_transaction(tx_id: int, db: Session = Depends(get_db)):
    """지정된 거래를 삭제하고 해당 계좌의 포트폴리오를 역산(Rollback)하여 원상복귀시킵니다."""
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


@app.put("/api/transactions/{tx_id}")
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


@app.get("/api/recommendations")
def get_ai_recommendations(db: Session = Depends(get_db)):
    """기획자 MOON(무니)의 R1 명세 데이터 규격 준수 (date 및 data 키 포맷)

    오늘 날짜에 맞춘 주식 가치주/성장주 목록 추천 데이터를 반환합니다.
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


@app.post("/api/tasks")
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

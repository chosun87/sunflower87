from datetime import datetime, timedelta
from fastapi import HTTPException
from sqlalchemy.orm import Session
from pykrx import stock as krx_stock

from database import Account, Stock, Transaction, StockOHLCVCache
from config import TRADE_DATE_PERIOD, DATA_GAP_THRESHOLD


def get_exact_trade_date_limits(target_period=60):
    """표준 영업일 개장일(KOSPI 지수 및 삼성전자 005930 기준)을 조회하여,
    정확히 target_period 개수만큼의 실제 한국 거래소 표준 영업일
    시작일과 종료일(16시 이전=전일, 16시 이후=당일)을 반환합니다.
    """
    now = datetime.today()
    current_hour = now.hour

    # 16시(오후 4시) 이후 여부에 따라 기준 종료일(Target End Date) 동적 정의
    if current_hour >= 16:
        target_end_str = now.strftime("%Y%m%d")
    else:
        target_end_str = (now - timedelta(days=1)).strftime("%Y%m%d")

    # 휴장일 필터링용 넉넉한 120일짜리 달력 버퍼 가동
    safe_start_str = (now - timedelta(days=120)).strftime("%Y%m%d")

    actual_trade_dates = []
    try:
        # R2 지침: KOSPI 인덱스로 먼저 개장일 캘린더 획득 시도
        df_market = krx_stock.get_market_ohlcv_by_date(
            safe_start_str, target_end_str, "KOSPI"
        )
        if df_market is None or df_market.empty:
            raise ValueError("Empty df")
        actual_trade_dates = df_market.index.strftime("%Y%m%d").tolist()
    except Exception:
        try:
            # pykrx의 지수(KOSPI) 타입 캐스팅 오류 회피를 위해,
            # 개장일이 완전히 일치하는 삼성전자(005930) 시세 인덱스로 캘린더 안전 획득
            df_market = krx_stock.get_market_ohlcv_by_date(
                safe_start_str, target_end_str, "005930"
            )
            if df_market is not None and not df_market.empty:
                actual_trade_dates = df_market.index.strftime("%Y%m%d").tolist()
        except Exception as e:
            print(f"[WARNING] Failed to fetch market limits: {e}")

    if actual_trade_dates:
        # 뒤에서부터 정확하게 target_period(60일)만큼 슬라이싱하여 시작일 and 종료일 확정
        valid_dates = actual_trade_dates[-target_period:]
        return valid_dates[0], valid_dates[-1]

    # Fail-safe 예외 대안: API 실패 시에는 단순 캘린더 데이 역산 반환
    safe_fallback_start = (now - timedelta(days=int(target_period * 1.5))).strftime(
        "%Y%m%d"
    )
    return safe_fallback_start, target_end_str


def get_market_trade_dates(start_date_str: str, end_date_str: str) -> list:
    """지정된 두 영업일 기간 동안 실제 한국 거래소(005930 캘린더 기준)가
    개장했던 표준 영업일 리스트를 반환합니다.
    """
    try:
        df_market = krx_stock.get_market_ohlcv_by_date(
            start_date_str, end_date_str, "005930"
        )
        if df_market is not None and not df_market.empty:
            return df_market.index.strftime("%Y%m%d").tolist()
    except Exception as e:
        print(f"[WARNING] Failed to fetch market calendar dates: {e}")
    return []


def sync_ohlcv_cache(db: Session, stock_code: str):
    """지정된 종목코드에 대해 pykrx 연동 주가 시계열을 동적 캐싱 및
    KOSPI 캘린더 기반 Gap 정제 알고리즘에 맞춰 동기화합니다.
    """
    today = datetime.now()
    current_hour = today.hour

    # 16시(오후 4시) 이후 여부에 따라 기준 종료일(Target End Date) 동적 정의
    if current_hour >= 16:
        target_end_str = today.strftime("%Y%m%d")
    else:
        target_end_str = (today - timedelta(days=1)).strftime("%Y%m%d")

    try:
        # [Step 1] 기존 캐시 데이터 최종일 조회
        last_cache = (
            db.query(StockOHLCVCache)
            .filter(StockOHLCVCache.stock_code == stock_code)
            .order_by(StockOHLCVCache.trade_date.desc())
            .first()
        )

        # 기록이 없다면 -> [케이스 A]로 바로 전이
        if not last_cache:
            print(
                f"No existing cache found for {stock_code}. Running [Case A] "
                f"(Initial {TRADE_DATE_PERIOD}-day setup)..."
            )
            _fetch_and_save_initial_ohlcv(db, stock_code)
        else:
            last_date_str = last_cache.trade_date

            # [Step 2] 120거래일 임계치 기반 데이터 공백 계산
            # KOSPI 표준 영업일 캘린더 리스트 획득
            trade_dates = get_market_trade_dates(last_date_str, target_end_str)

            # LAST_DATE보다 크고 YESTERDAY 이하인 진짜 영업일 개수 카운트
            gap_trade_days = len([d for d in trade_dates if d > last_date_str])
            print(
                f"Calculated trade dates gap between {last_date_str} and "
                f"{target_end_str} for {stock_code}: {gap_trade_days} trade days."
            )

            # [케이스 B] 공백 거래일 ≤ 120일 (거래일 기준 6개월 이하)
            if gap_trade_days <= DATA_GAP_THRESHOLD:
                print(
                    f"[Case B] Backfilling ohlcv gap for {stock_code} "
                    f"({gap_trade_days} trade days gap)..."
                )
                last_date_obj = datetime.strptime(last_date_str, "%Y%m%d")
                start_date_obj = last_date_obj + timedelta(days=1)
                start_date_str = start_date_obj.strftime("%Y%m%d")

                if start_date_str <= target_end_str:
                    df_gap = krx_stock.get_market_ohlcv_by_date(
                        start_date_str, target_end_str, stock_code
                    )
                    if df_gap is not None and not df_gap.empty:
                        _save_ohlcv_to_db(db, stock_code, df_gap)
                        print(f"Successfully backfilled {len(df_gap)} trade dates.")
                    else:
                        print("No market trade data during backfill period.")

            # [케이스 C] 공백 거래일 > 120일 (거래일 기준 6개월 초과)
            else:
                print(
                    f"[Case C] Trade dates gap ({gap_trade_days} days) "
                    f"exceeded threshold ({DATA_GAP_THRESHOLD} days) "
                    f"for {stock_code}. Purging cache..."
                )
                # 데이터 유효 기한 만료로 판단, 기존 과거 캐시 일괄 DELETE
                db.query(StockOHLCVCache).filter(
                    StockOHLCVCache.stock_code == stock_code
                ).delete()
                db.commit()

                # 지운 후 즉시 [케이스 A] 기동
                print(
                    f"Old cache purged. Running [Case A] (Initial "
                    f"{TRADE_DATE_PERIOD}-day setup)..."
                )
                _fetch_and_save_initial_ohlcv(db, stock_code)

    except Exception as e:
        # 외부 API 장애 혹은 크롤러 에러 시
        # 캐싱 실패로 전체 시스템 마비 차단
        print(f"[ERROR] Failed to sync OHLCV cache for {stock_code}: {e}")


def _fetch_and_save_initial_ohlcv(db: Session, stock_code: str):
    """[케이스 A] 순수 신규 및 만료 종목 처리:
    KOSPI 개장일 슬라이싱으로 정확한 60거래일치 수집 기입
    """
    start_str, end_str = get_exact_trade_date_limits(TRADE_DATE_PERIOD)
    print(
        f"Fetching exact {TRADE_DATE_PERIOD} trade dates for {stock_code} "
        f"from {start_str} to {end_str}..."
    )

    df = krx_stock.get_market_ohlcv_by_date(start_str, end_str, stock_code)
    if df is not None and not df.empty:
        _save_ohlcv_to_db(db, stock_code, df)
        print(f"Successfully cached initial {len(df)} trade dates.")
    else:
        print(
            f"[WARNING] No market data fetched from pykrx for {stock_code} "
            f"from {start_str} to {end_str}."
        )


def _save_ohlcv_to_db(db: Session, stock_code: str, df):
    """DataFrame 데이터를 stock_ohlcv_cache 테이블에 저장합니다."""
    if df is None or df.empty:
        return

    for date, row in df.iterrows():
        trade_date = date.strftime("%Y%m%d")

        # 동일 종목의 동일 날짜 중복 삽입 방지 검증 (PK 충돌 배제)
        existing = (
            db.query(StockOHLCVCache)
            .filter(
                StockOHLCVCache.stock_code == stock_code,
                StockOHLCVCache.trade_date == trade_date,
            )
            .first()
        )

        if not existing:
            cache_entry = StockOHLCVCache(
                stock_code=stock_code,
                trade_date=trade_date,
                open_price=int(row["시가"]),
                high_price=int(row["고가"]),
                low_price=int(row["저가"]),
                close_price=int(row["종가"]),
                volume=int(row["거래량"]),
            )
            db.add(cache_entry)

    db.commit()


def calculate_stock_balance(transactions, target_stock_code, acc_cd):
    """특정 계좌의 특정 종목의 거래 히스토리를 시간순으로 순회하며,
    '현재 보유 중인 수량'에 대한 '진짜 누적 매수 금액' 및 '누적 세금/수수료'를 1원의 오차도 없이 추적한다.
    """
    holding_quantity = 0
    total_purchase_amt = 0.0  # 현재 잔고를 구성하는 진짜 총 매수 금액
    total_tax_fee = 0.0  # 현재 잔고를 구성하는 진짜 총 세금+수수료

    # 거래 내역을 과거부터 최신순으로 정렬하여 순회
    sorted_tx = sorted(
        [t for t in transactions if t.code == target_stock_code and t.acc_cd == acc_cd],
        key=lambda x: x.date,
    )

    for tx in sorted_tx:
        cost = tx.quantity * tx.price
        t_fee = float(tx.tax_fee or 0.0)
        if tx.type == "BUY":
            # 매수 시: 수량과 금액(세금/수수료 포함)을 그대로 누적
            tx_amt = cost + t_fee
            holding_quantity += tx.quantity
            total_purchase_amt += tx_amt
            total_tax_fee += t_fee

        elif tx.type == "SELL":
            # 매도 시: 전량 매도 혹은 분할 매도 처리
            if holding_quantity <= 0:
                continue

            # 이동평균 평단가 및 평단 수수료 계산 (소수점 유지)
            current_avg_price = total_purchase_amt / holding_quantity
            current_avg_tax_fee = total_tax_fee / holding_quantity

            # 매도된 수량만큼의 '매수 원가' 및 '누적 수수료'를 차감하여 잔고 평단가 유지
            holding_quantity -= tx.quantity
            if holding_quantity <= 0:
                # 전량 매도되어 잔고가 0이 된 경우, 완전히 초기화
                holding_quantity = 0
                total_purchase_amt = 0.0
                total_tax_fee = 0.0
            else:
                # 분할 매도인 경우 현재 평단가 기준으로 남은 금액들 재정산
                total_purchase_amt = holding_quantity * current_avg_price
                total_tax_fee = holding_quantity * current_avg_tax_fee

    return holding_quantity, total_purchase_amt, total_tax_fee


def get_enriched_accounts_data(db: Session) -> dict:
    """SQLite 데이터베이스 account 및 stocks 테이블의 데이터를 로드하고
    실시간 수익률 및 평가액을 계산하여 프런트엔드 규격에 맞춰 반환합니다.
    """
    # 1. 활성 계좌 목록 로드 (dt_deleted IS NULL, acc_order ASC)
    db_accounts = (
        db.query(Account)
        .filter(Account.dt_deleted.is_(None))
        .order_by(Account.acc_order.asc())
        .all()
    )

    # 2. 보유 주식 목록 로드
    db_stocks = db.query(Stock).all()
    all_transactions = db.query(Transaction).all()

    # 계좌별 주식 분배 사전 초기화
    account_stocks_map = {acc.acc_cd: [] for acc in db_accounts}

    # DB에 존재하는 주식을 각각의 계좌 번호에 따라 올바르게 분배 및 계산
    for stock in db_stocks:
        acct_cd = stock.acc_cd or ""
        if acct_cd not in account_stocks_map:
            account_stocks_map[acct_cd] = []

        code = stock.code
        name = stock.name

        # 1. 거래 기록 기반 이동평균법 정밀 정산 (어띠베 BE_CRITICAL 긴급 지시서 반영)
        qty, purchase_amt, total_tax_fee = calculate_stock_balance(
            all_transactions, stock.code, acct_cd
        )

        # 2. 거래 기록이 전혀 없는 레거시 보유 주식에 대한 하이브리드 안전 가드 (Heal/Fallback)
        if qty <= 0 and stock.quantity > 0:
            qty = stock.quantity
            purchase_amt = float(stock.purchase_amount or 0.0)
            if purchase_amt <= 0 and stock.avg_price > 0:
                purchase_amt = qty * float(stock.avg_price)
            total_tax_fee = 0.0

        # 캐시 테이블에서 해당 종목의 최신(전일 종가) 가격 획득
        latest_cache = (
            db.query(StockOHLCVCache)
            .filter(StockOHLCVCache.stock_code == stock.code)
            .order_by(StockOHLCVCache.trade_date.desc())
            .first()
        )
        if latest_cache:
            stock.current_price = latest_cache.close_price
            db.add(stock)

        current_price = int(round(stock.current_price or 0))

        # BE R4/R5 정산 공식 전면 구현 및 ZeroDivisionError 원천 방어
        # 수수료/세금을 더하지 않고 순수 매수금액으로 연산하도록 요청 조정 반영
        total_purchase_amt_with_tax = purchase_amt
        total_tax_fee_val = total_tax_fee
        total_purchase_amt_pure = total_purchase_amt_with_tax - total_tax_fee_val

        total_eval_amt = qty * current_price
        total_profit_loss = total_eval_amt - total_purchase_amt_pure

        if qty <= 0 or total_purchase_amt_pure <= 0:
            avg_price_val = 0.0
            return_rate = 0.0
        else:
            # 평단가 산정 시에는 세금/수수료 포함된 단가를 추적 (엑셀 32921 매칭)
            avg_price_val = total_purchase_amt_with_tax / qty
            return_rate = round((total_profit_loss / total_purchase_amt_pure) * 100, 2)

        account_stocks_map[acct_cd].append(
            {
                "code": code,
                "name": name,
                "quantity": qty,
                "avg_price": avg_price_val,
                "current_price": current_price,
                "purchase_amount": total_purchase_amt_pure,  # backward compatibility
                "total_purchase_amt": total_purchase_amt_pure,  # BE R4 표준 규격
                "total_eval_amt": total_eval_amt,  # BE R4 표준 규격
                "total_profit_loss": total_profit_loss,  # BE R4 표준 규격
                "return_rate": return_rate,  # BE R4 표준 규격
                "eval_profit_rate": return_rate,  # backward compatibility
                "total_tax_fee": total_tax_fee_val,  # 총 세금+수수료
            }
        )

    if db_stocks:
        db.commit()

    accounts = []
    overall_total_eval = 0

    # 각 계좌별로 계산 및 DTO 조립
    for acc in db_accounts:
        stocks_list = account_stocks_map.get(acc.acc_cd, [])

        # 주식 평가액 계산
        stocks_purchase = int(round(sum(s["purchase_amount"] for s in stocks_list)))
        stocks_eval = int(
            round(sum(s["quantity"] * s["current_price"] for s in stocks_list))
        )

        # 총 평가금액 (주식 평가액 + 현금 잔고)
        total_eval = int(round(stocks_eval + acc.cash_balance))

        # 총 매입금액 (주식 매입금액 + 현금 잔고)
        total_purchase = int(round(stocks_purchase + acc.cash_balance))

        # 수익률 계산
        profit_rate = (
            round(((total_eval - total_purchase) / total_purchase) * 100, 2)
            if total_purchase > 0
            else 0.0
        )

        accounts.append(
            {
                "id": acc.acc_cd,
                "acc_cd": acc.acc_cd,
                "acc_nm": acc.acc_nm,
                "acc_company_nm": acc.acc_company_nm,
                "alias": f"[{acc.acc_company_nm}] {acc.acc_nm}",
                "balance": int(round(acc.cash_balance)),  # 예수금 잔액 전달
                "cash_balance": int(
                    round(acc.cash_balance)
                ),  # FE R9 표준 예수금 잔고 명세 바인딩
                "total_eval": total_eval,  # 총 평가액
                "profit_rate": profit_rate,  # 계좌 총 수익률
                "stocks": stocks_list,
            }
        )
        overall_total_eval += total_eval

    return {
        "status": "success",
        "total_asset": int(round(overall_total_eval)),
        "accounts": accounts,
    }


def recalculate_portfolio_for_account(db: Session, acc_cd: str):
    """지정된 계좌의 전체 거래 내역을 연대기순으로 처음부터 끝까지 추적해
    최종 보유 수량, 평단가 및 예수금 잔고(cash_balance)를 오차 없이 정밀 복원하고
    stocks 및 account 테이블에 동기화합니다.
    어느 시점이든 보유 수량이나 예수금 잔고가 마이너스가 되면 즉각 400 에러를 발생시킵니다.
    """
    account = db.query(Account).filter(Account.acc_cd == acc_cd).first()
    if not account:
        raise HTTPException(
            status_code=404, detail=f"Account with code '{acc_cd}' not found."
        )

    # 1. 초기 자산 설정 (데이터베이스의 account.initial_cash 값을 사용하며 소스코드 하드코딩은 완전 제거)
    cash_balance = float(account.initial_cash or 0.0)
    holdings = {}

    # 2. 해당 계좌의 모든 거래 기록을 연대기순으로 로드 (date 및 id 기준 오름차순 정렬)
    txs = (
        db.query(Transaction)
        .filter(Transaction.acc_cd == acc_cd)
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
        t_fee = float(tx.tax_fee or 0.0)

        if tx.type == "BUY":
            total_outflow = cost + t_fee
            # 매수 시 현금 차감 (예수금 부족 시 에러 유발)
            if cash_balance < total_outflow:
                detail_err = (
                    f"Insufficient cash balance for BUY transaction. "
                    f"Required: {total_outflow:,.0f} KRW (Cost: {cost:,.0f}, "
                    f"Fee: {t_fee:,.0f}), Available: {cash_balance:,.0f} KRW."
                )
                raise HTTPException(status_code=400, detail=detail_err)
            cash_balance -= total_outflow

            # 기획 표준 연산 공식:
            # 총 매수금액 = 각 매수 거래의 (수량 * 단가) 총합 + 각 거래의 tax_fee 총합 = total_outflow
            if code in holdings:
                existing = holdings[code]
                total_qty = existing["quantity"] + qty
                new_purchase_amount = existing["purchase_amount"] + total_outflow
                existing["quantity"] = total_qty
                existing["purchase_amount"] = new_purchase_amount
                existing["avg_price"] = new_purchase_amount / total_qty
            else:
                holdings[code] = {
                    "name": name,
                    "quantity": qty,
                    "purchase_amount": float(total_outflow),
                    "avg_price": float(total_outflow) / qty,
                }
        elif tx.type == "SELL":
            total_inflow = cost - t_fee
            # 매도 시 현금 합산
            cash_balance += total_inflow

            # 주식 보유고 갱신 (보유 주식 부족 시 에러 유발)
            if code not in holdings or holdings[code]["quantity"] < qty:
                detail_err = (
                    f"Insufficient stock holdings for SELL transaction. "
                    f"Holdings for {name} ({code}) falls below zero."
                )
                raise HTTPException(status_code=400, detail=detail_err)

            existing = holdings[code]
            realized_cost = qty * existing["avg_price"]
            remaining = existing["quantity"] - qty
            if remaining == 0:
                del holdings[code]
            else:
                existing["quantity"] = remaining
                existing["purchase_amount"] -= realized_cost
                existing["avg_price"] = existing["purchase_amount"] / remaining

    # 4. DB 테이블 동기화 (예수금 잔고 반영 및 stocks 테이블 완전 청소 후 재생성)
    account.cash_balance = int(round(cash_balance))

    db.query(Stock).filter(Stock.acc_cd == acc_cd).delete()

    for code, info in holdings.items():
        # 하드코딩 시세 맵 제거 -> StockOHLCVCache에서 최신 전일 종가 조회
        latest_cache = (
            db.query(StockOHLCVCache)
            .filter(StockOHLCVCache.stock_code == code)
            .order_by(StockOHLCVCache.trade_date.desc())
            .first()
        )

        if latest_cache:
            current_p = latest_cache.close_price
        else:
            # 시세 캐시가 없을 경우 평단가를 현재가로 폴백 적용
            current_p = int(round(info["avg_price"]))

        new_stock = Stock(
            code=code,
            acc_cd=acc_cd,
            name=info["name"],
            quantity=info["quantity"],
            avg_price=info["avg_price"],
            current_price=current_p,
            purchase_amount=info["purchase_amount"],
        )
        db.add(new_stock)

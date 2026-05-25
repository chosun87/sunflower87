from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from config import DATA_GAP_THRESHOLD, TRADE_DATE_PERIOD
from constants import CashType, TradeType
from database import (
    Account,
    Stock,
    StockCache,
    StockOHLCVCache,
    Transaction,
    TransactionCash,
)


def get_exact_trade_date_limits(target_period=60):
    now = datetime.today()
    current_hour = now.hour

    if current_hour >= 16:
        target_end_str = now.strftime("%Y%m%d")
    else:
        target_end_str = (now - timedelta(days=1)).strftime("%Y%m%d")

    safe_start_str = (now - timedelta(days=120)).strftime("%Y%m%d")
    actual_trade_dates = []

    try:
        from pykrx import stock as krx_stock

        df_market = krx_stock.get_market_ohlcv_by_date(
            safe_start_str, target_end_str, "KOSPI"
        )
        if df_market is None or df_market.empty:
            raise ValueError("Empty df")
        actual_trade_dates = df_market.index.strftime("%Y%m%d").tolist()
    except Exception:
        try:
            df_market = krx_stock.get_market_ohlcv_by_date(
                safe_start_str, target_end_str, "005930"
            )
            if df_market is not None and not df_market.empty:
                actual_trade_dates = df_market.index.strftime("%Y%m%d").tolist()
        except Exception as e:
            print(f"[WARNING] Failed to fetch market limits: {e}")

    if actual_trade_dates:
        valid_dates = actual_trade_dates[-target_period:]
        if valid_dates:
            return valid_dates[0], valid_dates[-1]

    safe_fallback_start = (now - timedelta(days=int(target_period * 1.5))).strftime(
        "%Y%m%d"
    )
    return safe_fallback_start, target_end_str


def get_market_trade_dates(start_date_str: str, end_date_str: str) -> list:
    try:
        from pykrx import stock as krx_stock

        df_market = krx_stock.get_market_ohlcv_by_date(
            start_date_str, end_date_str, "005930"
        )
        if df_market is not None and not df_market.empty:
            return df_market.index.strftime("%Y%m%d").tolist()
    except Exception as e:
        print(f"[WARNING] Failed to fetch market calendar dates: {e}")
    return []


def _save_ohlcv_to_db(db: Session, stock_code: str, df):
    if df is None or df.empty:
        return

    # Check if '거래대금' or '등락률' exist, if not set 0
    has_trading_value = "거래대금" in df.columns
    has_fluctuation = "등락률" in df.columns

    for date, row in df.iterrows():
        trade_date = date.strftime("%Y-%m-%d")
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
                open_price=int(row.get("시가", 0)),
                high_price=int(row.get("고가", 0)),
                low_price=int(row.get("저가", 0)),
                close_price=int(row.get("종가", 0)),
                volume=int(row.get("거래량", 0)),
                trading_value=int(row.get("거래대금", 0)) if has_trading_value else 0,
                fluctuation_rate=(
                    float(row.get("등락률", 0.0)) if has_fluctuation else 0.0
                ),
            )
            db.add(cache_entry)
    db.commit()


def _fetch_and_save_initial_ohlcv(db: Session, stock_code: str):
    start_str, end_str = get_exact_trade_date_limits(TRADE_DATE_PERIOD)
    from pykrx import stock as krx_stock

    df = krx_stock.get_market_ohlcv_by_date(start_str, end_str, stock_code)
    if df is not None and not df.empty:
        _save_ohlcv_to_db(db, stock_code, df)


def sync_ohlcv_cache(
    db: Session, stock_code: str, start_date: str = None, end_date: str = None
):
    today = datetime.now()
    current_hour = today.hour

    if not end_date:
        if current_hour >= 16:
            target_end_str = today.strftime("%Y%m%d")
        else:
            target_end_str = (today - timedelta(days=1)).strftime("%Y%m%d")
    else:
        target_end_str = end_date.replace("-", "")

    try:
        last_cache = (
            db.query(StockOHLCVCache)
            .filter(StockOHLCVCache.stock_code == stock_code)
            .order_by(StockOHLCVCache.trade_date.desc())
            .first()
        )
        first_cache = (
            db.query(StockOHLCVCache)
            .filter(StockOHLCVCache.stock_code == stock_code)
            .order_by(StockOHLCVCache.trade_date.asc())
            .first()
        )

        if not last_cache or not first_cache:
            if start_date:
                req_start_obj = datetime.strptime(start_date.replace("-", ""), "%Y%m%d")
                safe_start_str = (req_start_obj - timedelta(days=120)).strftime(
                    "%Y%m%d"
                )
                from pykrx import stock as krx_stock

                df_init = krx_stock.get_market_ohlcv_by_date(
                    safe_start_str, target_end_str, stock_code
                )
                if df_init is not None and not df_init.empty:
                    _save_ohlcv_to_db(db, stock_code, df_init)
            else:
                _fetch_and_save_initial_ohlcv(db, stock_code)
            return

        last_date_str = last_cache.trade_date.replace("-", "")
        first_date_str = first_cache.trade_date.replace("-", "")

        if start_date:
            req_start_str = start_date.replace("-", "")
            req_start_obj = datetime.strptime(req_start_str, "%Y%m%d")
            safe_start_str = (req_start_obj - timedelta(days=120)).strftime("%Y%m%d")

            if safe_start_str < first_date_str:
                from pykrx import stock as krx_stock

                h_end_obj = datetime.strptime(first_date_str, "%Y%m%d") - timedelta(
                    days=1
                )
                h_end_str = h_end_obj.strftime("%Y%m%d")
                if safe_start_str <= h_end_str:
                    df_hist = krx_stock.get_market_ohlcv_by_date(
                        safe_start_str, h_end_str, stock_code
                    )
                    if df_hist is not None and not df_hist.empty:
                        _save_ohlcv_to_db(db, stock_code, df_hist)

        if last_date_str < target_end_str:
            trade_dates = get_market_trade_dates(last_date_str, target_end_str)
            gap_trade_days = len([d for d in trade_dates if d > last_date_str])

            if 0 < gap_trade_days <= DATA_GAP_THRESHOLD:
                last_date_obj = datetime.strptime(last_date_str, "%Y%m%d")
                m_start_str = (last_date_obj + timedelta(days=1)).strftime("%Y%m%d")
                if m_start_str <= target_end_str:
                    from pykrx import stock as krx_stock

                    df_gap = krx_stock.get_market_ohlcv_by_date(
                        m_start_str, target_end_str, stock_code
                    )
                    if df_gap is not None and not df_gap.empty:
                        _save_ohlcv_to_db(db, stock_code, df_gap)
            elif gap_trade_days > DATA_GAP_THRESHOLD:
                db.query(StockOHLCVCache).filter(
                    StockOHLCVCache.stock_code == stock_code
                ).delete()
                db.commit()
                if start_date:
                    req_start_obj = datetime.strptime(
                        start_date.replace("-", ""), "%Y%m%d"
                    )
                    safe_start_str = (req_start_obj - timedelta(days=120)).strftime(
                        "%Y%m%d"
                    )
                    from pykrx import stock as krx_stock

                    df_init = krx_stock.get_market_ohlcv_by_date(
                        safe_start_str, target_end_str, stock_code
                    )
                    if df_init is not None and not df_init.empty:
                        _save_ohlcv_to_db(db, stock_code, df_init)
                else:
                    _fetch_and_save_initial_ohlcv(db, stock_code)

    except Exception as e:
        print(f"[ERROR] Failed to sync OHLCV cache for {stock_code}: {e}")


def calculate_stock_balance(transactions, target_stock_code, acc_cd):
    holding_quantity = 0
    total_purchase_amt = 0.0
    total_tax_fee = 0.0
    all_time_buy_amt = 0.0
    all_time_sell_amt = 0.0
    all_time_tax_fee = 0.0

    sorted_tx = sorted(
        [
            t
            for t in transactions
            if t.stock_code == target_stock_code
            and t.acc_cd == acc_cd
            and t.dt_deleted is None
        ],
        key=lambda x: x.dt_trade,
    )

    for tx in sorted_tx:
        cost = tx.quantity * tx.price
        t_fee = float(tx.tax_fee or 0.0)
        all_time_tax_fee += t_fee

        if tx.trade_type == TradeType.BUY:
            tx_amt = cost + t_fee
            holding_quantity += tx.quantity
            total_purchase_amt += tx_amt
            total_tax_fee += t_fee
            all_time_buy_amt += tx_amt
        elif tx.trade_type == TradeType.SELL:
            all_time_sell_amt += cost - t_fee
            if holding_quantity <= 0:
                continue

            current_avg_price = total_purchase_amt / holding_quantity
            current_avg_tax_fee = total_tax_fee / holding_quantity

            holding_quantity -= tx.quantity
            if holding_quantity <= 0:
                holding_quantity = 0
                total_purchase_amt = 0.0
                total_tax_fee = 0.0
            else:
                total_purchase_amt = holding_quantity * current_avg_price
                total_tax_fee = holding_quantity * current_avg_tax_fee

    return (
        holding_quantity,
        total_purchase_amt,
        total_tax_fee,
        all_time_buy_amt,
        all_time_sell_amt,
        all_time_tax_fee,
    )


def get_enriched_accounts_data(db: Session) -> dict:
    db_accounts = (
        db.query(Account)
        .filter(Account.dt_deleted.is_(None))
        .order_by(Account.acc_order.asc())
        .all()
    )
    db_stocks = db.query(Stock).all()
    all_transactions = (
        db.query(Transaction).filter(Transaction.dt_deleted.is_(None)).all()
    )

    account_stocks_map = {acc.acc_cd: [] for acc in db_accounts}

    for stock in db_stocks:
        acct_cd = stock.acc_cd or ""
        if acct_cd not in account_stocks_map:
            account_stocks_map[acct_cd] = []

        code = stock.stock_code
        cache = db.query(StockCache).filter(StockCache.stock_code == code).first()
        name = cache.stock_name if cache else code

        (
            qty,
            purchase_amt,
            total_tax_fee,
            all_time_buy_amt,
            all_time_sell_amt,
            all_time_tax_fee,
        ) = calculate_stock_balance(all_transactions, code, acct_cd)

        if qty <= 0 and stock.quantity > 0:
            qty = stock.quantity
            purchase_amt = float(stock.purchase_amount or 0.0)
            if purchase_amt <= 0 and stock.avg_price > 0:
                purchase_amt = qty * float(stock.avg_price)
            total_tax_fee = 0.0

        latest_cache = (
            db.query(StockOHLCVCache)
            .filter(StockOHLCVCache.stock_code == code)
            .order_by(StockOHLCVCache.trade_date.desc())
            .first()
        )
        if latest_cache:
            stock.current_price = latest_cache.close_price
            db.add(stock)

        current_price = int(round(stock.current_price or 0))

        total_purchase_amt_with_tax = purchase_amt
        total_tax_fee_val = total_tax_fee
        total_purchase_amt_pure = total_purchase_amt_with_tax - total_tax_fee_val

        total_eval_amt = qty * current_price
        total_profit_loss = total_eval_amt - total_purchase_amt_pure

        if qty <= 0:
            total_tax_fee_val = all_time_tax_fee
            total_purchase_amt_pure = all_time_buy_amt - all_time_tax_fee
            total_eval_amt = all_time_sell_amt
            total_profit_loss = all_time_sell_amt - all_time_buy_amt
            avg_price_val = 0.0
            return_rate = (
                round((total_profit_loss / all_time_buy_amt) * 100, 2)
                if all_time_buy_amt > 0
                else 0.0
            )
        elif total_purchase_amt_pure <= 0:
            avg_price_val = 0.0
            return_rate = 0.0
        else:
            avg_price_val = total_purchase_amt_with_tax / qty
            return_rate = round((total_profit_loss / total_purchase_amt_pure) * 100, 2)

        account_stocks_map[acct_cd].append(
            {
                "stock_code": code,
                "stock_name": name,
                "quantity": qty,
                "avg_price": int(round(avg_price_val)),
                "current_price": current_price,
                "purchase_amount": int(round(total_purchase_amt_pure)),
                "total_eval_amt": int(round(total_eval_amt)),
                "total_profit_loss": int(round(total_profit_loss)),
                "return_rate": return_rate,
                "total_tax_fee": int(round(total_tax_fee_val)),
            }
        )

    if db_stocks:
        db.commit()

    accounts = []
    overall_total_eval = 0

    for acc in db_accounts:
        stocks_list = account_stocks_map.get(acc.acc_cd, [])
        stocks_purchase = int(round(sum(s["purchase_amount"] for s in stocks_list)))
        stocks_eval = int(
            round(sum(s["quantity"] * s["current_price"] for s in stocks_list))
        )
        total_eval = int(round(stocks_eval + acc.cash_balance))
        total_purchase = int(round(stocks_purchase + acc.cash_balance))
        profit_rate = (
            round(((total_eval - total_purchase) / total_purchase) * 100, 2)
            if total_purchase > 0
            else 0.0
        )

        accounts.append(
            {
                "acc_cd": acc.acc_cd,
                "acc_nm": acc.acc_nm,
                "acc_company_nm": acc.acc_company_nm,
                "cash_balance": int(round(acc.cash_balance)),
                "total_eval": total_eval,
                "profit_rate": profit_rate,
                "stocks": stocks_list,
            }
        )
        overall_total_eval += total_eval

    return {
        "status": "success",
        "data": {"total_asset": int(round(overall_total_eval)), "accounts": accounts},
    }


def recalculate_portfolio_for_account(db: Session, acc_cd: str):
    account = db.query(Account).filter(Account.acc_cd == acc_cd).first()
    if not account:
        raise HTTPException(
            status_code=404, detail=f"Account with code '{acc_cd}' not found."
        )

    cash_balance = float(account.initial_cash or 0.0)
    holdings = {}

    # Load and combine all valid transactions
    stock_txs = (
        db.query(Transaction)
        .filter(Transaction.acc_cd == acc_cd, Transaction.dt_deleted.is_(None))
        .all()
    )
    cash_txs = (
        db.query(TransactionCash)
        .filter(TransactionCash.acc_cd == acc_cd, TransactionCash.dt_deleted.is_(None))
        .all()
    )

    # Create unified timeline events
    events = []
    for tx in stock_txs:
        events.append({"time": tx.dt_trade, "type": "STOCK", "data": tx})
    for ctx in cash_txs:
        events.append({"time": ctx.dt_cash, "type": "CASH", "data": ctx})

    events.sort(key=lambda x: x["time"])

    # Simulate timeline
    for event in events:
        if event["type"] == "CASH":
            ctx = event["data"]
            if ctx.cash_type in [
                CashType.DEPOSIT,
                CashType.INTEREST,
                CashType.DIVIDEND,
            ]:
                cash_balance += ctx.amount
            elif ctx.cash_type in [CashType.WITHDRAW, CashType.FEE]:
                cash_balance -= ctx.amount

        elif event["type"] == "STOCK":
            tx = event["data"]
            code = tx.stock_code
            qty = tx.quantity
            cost = qty * tx.price
            t_fee = float(tx.tax_fee or 0.0)

            if tx.trade_type == TradeType.BUY:
                total_outflow = cost + t_fee
                cash_balance -= total_outflow

                if code in holdings:
                    existing = holdings[code]
                    total_qty = existing["quantity"] + qty
                    new_purchase_amount = existing["purchase_amount"] + total_outflow
                    existing["quantity"] = total_qty
                    existing["purchase_amount"] = new_purchase_amount
                    existing["avg_price"] = new_purchase_amount / total_qty
                else:
                    holdings[code] = {
                        "quantity": qty,
                        "purchase_amount": float(total_outflow),
                        "avg_price": float(total_outflow) / qty,
                    }
            elif tx.trade_type == TradeType.SELL:
                total_inflow = cost - t_fee
                cash_balance += total_inflow

                if code not in holdings or holdings[code]["quantity"] < qty:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Insufficient stock holdings for SELL transaction ({code}).",
                    )

                existing = holdings[code]
                realized_cost = qty * existing["avg_price"]
                remaining = existing["quantity"] - qty
                if remaining == 0:
                    existing["quantity"] = 0
                    existing["purchase_amount"] = 0.0
                    existing["avg_price"] = 0.0
                else:
                    existing["quantity"] = remaining
                    existing["purchase_amount"] -= realized_cost
                    existing["avg_price"] = existing["purchase_amount"] / remaining

    account.cash_balance = int(round(cash_balance))
    db.query(Stock).filter(Stock.acc_cd == acc_cd).delete()

    for code, info in holdings.items():
        if info["quantity"] <= 0:
            continue

        latest_cache = (
            db.query(StockOHLCVCache)
            .filter(StockOHLCVCache.stock_code == code)
            .order_by(StockOHLCVCache.trade_date.desc())
            .first()
        )
        current_p = (
            latest_cache.close_price if latest_cache else int(round(info["avg_price"]))
        )

        new_stock = Stock(
            stock_code=code,
            acc_cd=acc_cd,
            quantity=info["quantity"],
            avg_price=int(round(info["avg_price"])),
            current_price=current_p,
            purchase_amount=int(round(info["purchase_amount"])),
        )
        db.add(new_stock)

    # Note: AccountDailyBalance recalculation can be triggered iteratively here,
    # but for simplicity and performance, we leave it to be populated on-the-fly or via dedicated endpoints.
    db.commit()

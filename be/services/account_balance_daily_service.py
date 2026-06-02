from datetime import datetime, timedelta

from fastapi import HTTPException
from sqlalchemy.orm import Session

from clients.krx_client import fetch_market_ohlcv_by_date
from constants import CashType, TradeType
from database import (
    Account,
    AccountBalanceDaily,
    StockOHLCVDaily,
    Transaction,
    TransactionCash,
    db_write_lock,
)


def sync_account_balance_daily(
    db: Session,
    acc_cd: str,
    req_start_date: str = None,
    req_end_date: str = None,
):
    account = db.query(Account).filter(Account.acc_cd == acc_cd).first()
    if not account:
        raise HTTPException(status_code=404, detail=f"Account '{acc_cd}' not found.")

    yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")

    if not req_end_date:
        end_date_str = yesterday
    else:
        if req_end_date > yesterday:
            end_date_str = yesterday
        else:
            end_date_str = req_end_date

    if not req_start_date:
        start_date_str = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    else:
        start_date_str = req_start_date

    if account.dt_opened and start_date_str < account.dt_opened:
        start_date_str = account.dt_opened

    if start_date_str > end_date_str:
        return {"status": "success", "message": "Start date cannot be after end date."}

    with db_write_lock:
        # Delete existing records in the range before recalculating
        db.query(AccountBalanceDaily).filter(
            AccountBalanceDaily.acc_cd == acc_cd,
            AccountBalanceDaily.trade_date >= start_date_str,
            AccountBalanceDaily.trade_date <= end_date_str,
        ).delete(synchronize_session=False)
        db.commit()

    # Note: We still fetch all transactions from the beginning to calculate
    # the correct balance and holdings for the target period.
    # We do not use 'start_date_str' to filter transactions.

    start_compact = start_date_str.replace("-", "")
    end_compact = end_date_str.replace("-", "")

    try:
        # Use Samsung Electronics (005930) to get standard KRX trading days
        df_ref = fetch_market_ohlcv_by_date(start_compact, end_compact, "005930")
        trading_days = [ts.strftime("%Y-%m-%d") for ts in df_ref.index]
    except Exception as e:
        print(f"Error fetching trading days: {e}")
        return {"status": "error", "message": "Failed to fetch trading days."}

    if not trading_days:
        return {"status": "success", "message": "No new trading days to sync."}

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

    events = []
    unique_stocks = set()
    for tx in stock_txs:
        events.append({"time": tx.dt_trade, "type": "STOCK", "data": tx})
        unique_stocks.add(tx.stock_code)
    for ctx in cash_txs:
        events.append({"time": ctx.dt_cash, "type": "CASH", "data": ctx})
    events.sort(key=lambda x: x["time"])

    for code in unique_stocks:
        try:
            # Check if we have prices for this date range
            count = (
                db.query(StockOHLCVDaily)
                .filter(
                    StockOHLCVDaily.stock_code == code,
                    StockOHLCVDaily.trade_date >= start_date_str,
                    StockOHLCVDaily.trade_date <= end_date_str,
                )
                .count()
            )
            if count < len(trading_days):
                df_stock = fetch_market_ohlcv_by_date(start_compact, end_compact, code)
                for ts, row in df_stock.iterrows():
                    t_date_str = ts.strftime("%Y-%m-%d")
                    close_p = int(row["종가"])
                    if close_p > 0:
                        existing = (
                            db.query(StockOHLCVDaily)
                            .filter(
                                StockOHLCVDaily.stock_code == code,
                                StockOHLCVDaily.trade_date == t_date_str,
                            )
                            .first()
                        )
                        if existing:
                            existing.close_price = close_p
                        else:
                            db.add(
                                StockOHLCVDaily(
                                    stock_code=code,
                                    trade_date=t_date_str,
                                    close_price=close_p,
                                    open_price=int(row["시가"]),
                                    high_price=int(row["고가"]),
                                    low_price=int(row["저가"]),
                                    volume=int(row["거래량"]),
                                    trading_value=0,
                                    fluctuation_rate=float(row.get("등락률", 0.0)),
                                    change_price=0,
                                    change_price_code="3",
                                )
                            )
                with db_write_lock:
                    db.commit()
        except Exception as e:
            print(f"Failed OHLCV for {code}: {e}")
            db.rollback()

    cash_balance = 0.0
    total_principal = 0.0
    holdings = {}

    event_idx = 0
    total_events = len(events)
    new_balances = []

    for t_date in trading_days:
        while event_idx < total_events and events[event_idx]["time"] <= t_date:
            event = events[event_idx]
            if event["type"] == "CASH":
                ctx = event["data"]
                if ctx.cash_type in [
                    CashType.DEPOSIT,
                    CashType.INTEREST,
                    CashType.DIVIDEND,
                ]:
                    cash_balance += ctx.amount
                    if ctx.cash_type == CashType.DEPOSIT:
                        total_principal += ctx.amount
                elif ctx.cash_type in [CashType.WITHDRAW, CashType.FEE]:
                    cash_balance -= ctx.amount
                    if ctx.cash_type == CashType.WITHDRAW:
                        total_principal -= ctx.amount
            elif event["type"] == "STOCK":
                tx = event["data"]
                code = tx.stock_code
                qty = tx.quantity
                cost = qty * tx.price
                t_fee = float(tx.tax_fee or 0.0)

                if tx.trade_type == TradeType.BUY:
                    cash_balance -= cost + t_fee
                    if code in holdings:
                        holdings[code]["quantity"] += qty
                    else:
                        holdings[code] = {"quantity": qty}
                elif tx.trade_type == TradeType.SELL:
                    cash_balance += cost - t_fee
                    if code in holdings:
                        holdings[code]["quantity"] = max(
                            0, holdings[code]["quantity"] - qty
                        )
            event_idx += 1

        stock_eval_balance = 0.0
        for code, info in holdings.items():
            if info["quantity"] <= 0:
                continue
            latest_cache = (
                db.query(StockOHLCVDaily)
                .filter(
                    StockOHLCVDaily.stock_code == code,
                    StockOHLCVDaily.trade_date <= t_date,
                )
                .order_by(StockOHLCVDaily.trade_date.desc())
                .first()
            )
            current_price = latest_cache.close_price if latest_cache else 0
            stock_eval_balance += info["quantity"] * current_price

        total_balance = cash_balance + stock_eval_balance
        return_rate = 0.0
        if total_principal > 0:
            return_rate = round(
                ((total_balance - total_principal) / total_principal) * 100, 2
            )

        new_balances.append(
            AccountBalanceDaily(
                acc_cd=acc_cd,
                trade_date=t_date,
                cash_balance=int(round(cash_balance)),
                stock_eval_balance=int(round(stock_eval_balance)),
                total_balance=int(round(total_balance)),
                return_rate=return_rate,
            )
        )

    if new_balances:
        with db_write_lock:
            for nb in new_balances:
                db.merge(nb)
            db.commit()

    return {
        "status": "success",
        "message": f"Synced {len(new_balances)} daily balances up to {end_date_str}.",
    }

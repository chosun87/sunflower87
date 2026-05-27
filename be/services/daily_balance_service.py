from datetime import datetime, timedelta

from fastapi import HTTPException
from pykrx import stock as pykrx_stock
from sqlalchemy.orm import Session

from constants import CashType, TradeType
from database import (
    Account,
    AccountDailyBalance,
    StockOHLCVCache,
    Transaction,
    TransactionCash,
)


def sync_daily_balances_for_account(db: Session, acc_cd: str):
    account = db.query(Account).filter(Account.acc_cd == acc_cd).first()
    if not account:
        raise HTTPException(status_code=404, detail=f"Account '{acc_cd}' not found.")

    last_balance = (
        db.query(AccountDailyBalance)
        .filter(AccountDailyBalance.acc_cd == acc_cd)
        .order_by(AccountDailyBalance.trade_date.desc())
        .first()
    )

    start_date_str = None
    if last_balance:
        last_date = datetime.strptime(last_balance.trade_date, "%Y-%m-%d").date()
        start_date = last_date + timedelta(days=1)
        start_date_str = start_date.strftime("%Y-%m-%d")

    end_date = (datetime.utcnow() - timedelta(days=1)).date()
    end_date_str = end_date.strftime("%Y-%m-%d")

    if start_date_str and start_date_str > end_date_str:
        return {"status": "success", "message": "Already up to date."}

    if not start_date_str:
        # Start from the first transaction
        first_tx = (
            db.query(Transaction.dt_trade)
            .filter(Transaction.acc_cd == acc_cd, Transaction.dt_deleted.is_(None))
            .order_by(Transaction.dt_trade.asc())
            .first()
        )
        first_ctx = (
            db.query(TransactionCash.dt_cash)
            .filter(
                TransactionCash.acc_cd == acc_cd, TransactionCash.dt_deleted.is_(None)
            )
            .order_by(TransactionCash.dt_cash.asc())
            .first()
        )

        first_dates = []
        if first_tx:
            first_dates.append(first_tx[0].date())
        if first_ctx:
            first_dates.append(first_ctx[0].date())

        if not first_dates:
            return {"status": "success", "message": "No transactions found."}

        start_date = min(first_dates)
        start_date_str = start_date.strftime("%Y-%m-%d")

    start_compact = start_date_str.replace("-", "")
    end_compact = end_date_str.replace("-", "")

    try:
        # Use Samsung Electronics (005930) to get standard KRX trading days
        df_ref = pykrx_stock.get_market_ohlcv(start_compact, end_compact, "005930")
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
                db.query(StockOHLCVCache)
                .filter(
                    StockOHLCVCache.stock_code == code,
                    StockOHLCVCache.trade_date >= start_date_str,
                    StockOHLCVCache.trade_date <= end_date_str,
                )
                .count()
            )
            if count < len(trading_days):
                df_stock = pykrx_stock.get_market_ohlcv(
                    start_compact, end_compact, code
                )
                for ts, row in df_stock.iterrows():
                    t_date_str = ts.strftime("%Y-%m-%d")
                    close_p = int(row["종가"])
                    if close_p > 0:
                        existing = (
                            db.query(StockOHLCVCache)
                            .filter(
                                StockOHLCVCache.stock_code == code,
                                StockOHLCVCache.trade_date == t_date_str,
                            )
                            .first()
                        )
                        if existing:
                            existing.close_price = close_p
                        else:
                            db.add(
                                StockOHLCVCache(
                                    stock_code=code,
                                    trade_date=t_date_str,
                                    close_price=close_p,
                                    open_price=int(row["시가"]),
                                    high_price=int(row["고가"]),
                                    low_price=int(row["저가"]),
                                    volume=int(row["거래량"]),
                                )
                            )
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
        t_datetime_end = datetime.strptime(t_date + " 23:59:59", "%Y-%m-%d %H:%M:%S")

        while event_idx < total_events and events[event_idx]["time"] <= t_datetime_end:
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
                db.query(StockOHLCVCache)
                .filter(
                    StockOHLCVCache.stock_code == code,
                    StockOHLCVCache.trade_date <= t_date,
                )
                .order_by(StockOHLCVCache.trade_date.desc())
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
            AccountDailyBalance(
                acc_cd=acc_cd,
                trade_date=t_date,
                cash_balance=int(round(cash_balance)),
                stock_eval_balance=int(round(stock_eval_balance)),
                total_balance=int(round(total_balance)),
                return_rate=return_rate,
            )
        )

    if new_balances:
        for nb in new_balances:
            db.merge(nb)
        db.commit()

    return {
        "status": "success",
        "message": f"Synced {len(new_balances)} daily balances up to {end_date_str}.",
    }

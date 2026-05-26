from fastapi import HTTPException
from sqlalchemy.orm import Session

from constants import CashType, TradeType
from database import (
    Account,
    Stock,
    StockCache,
    StockOHLCVCache,
    Transaction,
    TransactionCash,
)

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
    for tx in stock_txs:
        events.append({"time": tx.dt_trade, "type": "STOCK", "data": tx})
    for ctx in cash_txs:
        events.append({"time": ctx.dt_cash, "type": "CASH", "data": ctx})

    events.sort(key=lambda x: x["time"])

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

    db.commit()

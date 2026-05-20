from datetime import datetime

from fastapi import BackgroundTasks, HTTPException
from sqlalchemy.orm import Session

from database import Account, SessionLocal, Stock, Transaction
from portfolio_service import recalculate_portfolio_for_account

TRANSACTION_TYPES = {"BUY", "SELL"}


def _get_account(db: Session, acc_cd: str) -> Account:
    account = db.query(Account).filter(Account.acc_cd == acc_cd).first()
    if not account:
        raise HTTPException(
            status_code=404,
            detail=f"Account with code '{acc_cd}' not found.",
        )
    return account


def _parse_transaction_date(date_str: str) -> datetime:
    try:
        return datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S")
    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid date format: {date_str}. Expected YYYY-MM-DD HH:MM:SS.",
        ) from e


def get_transaction_history(
    db: Session,
    acc_cd: str | None = None,
    stock_code: str | None = None,
    start_date: str | None = None,
    end_date: str | None = None,
) -> list[dict]:
    from database import Account

    query = db.query(Transaction, Account).outerjoin(
        Account, Transaction.acc_cd == Account.acc_cd
    )

    if acc_cd:
        query = query.filter(Transaction.acc_cd == acc_cd)
    if stock_code:
        query = query.filter(Transaction.code.like(f"%{stock_code}%"))
    if start_date:
        try:
            dt_start = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.filter(Transaction.date >= dt_start)
        except ValueError:
            pass
    if end_date:
        try:
            dt_end = datetime.strptime(end_date, "%Y-%m-%d").replace(
                hour=23, minute=59, second=59
            )
            query = query.filter(Transaction.date <= dt_end)
        except ValueError:
            pass

    results = query.order_by(Transaction.date.desc()).all()
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
                "tax_fee": t.tax_fee,
                "acc_cd": t.acc_cd,
                "acc_nm": acc_name,
                "acc_company_nm": acc_company,
                "account_alias": (
                    f"[{acc_company}] {acc_name}" if acc_company else acc_name
                ),
            }
        )
    return data


def _sync_ohlcv_in_background(background_tasks: BackgroundTasks, code: str):
    from portfolio_service import sync_ohlcv_cache

    def _run_sync(session_factory, stock_code):
        bg_db = session_factory()
        try:
            sync_ohlcv_cache(bg_db, stock_code)
        finally:
            bg_db.close()

    background_tasks.add_task(_run_sync, SessionLocal, code)


def add_transaction(
    db: Session, tx_input, background_tasks: BackgroundTasks | None = None
) -> dict:
    tx_type = tx_input.type.upper()
    if tx_type not in TRANSACTION_TYPES:
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
    account = _get_account(db, acc_cd)

    is_new_stock = db.query(Stock).filter(Stock.code == tx_input.code).count() == 0
    tx_date = _parse_transaction_date(tx_input.date)

    cost = tx_input.quantity * tx_input.price
    tx_fee = tx_input.tax_fee or 0

    stock = (
        db.query(Stock)
        .filter(Stock.acc_cd == acc_cd, Stock.code == tx_input.code)
        .first()
    )

    if tx_type == "BUY":
        total_outflow = cost + tx_fee
        account.cash_balance -= total_outflow

        if stock:
            new_qty = stock.quantity + tx_input.quantity
            new_avg = (stock.quantity * stock.avg_price + cost) / new_qty
            stock.quantity = new_qty
            stock.avg_price = int(round(new_avg))
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
    else:
        if not stock or stock.quantity < tx_input.quantity:
            raise HTTPException(
                status_code=400,
                detail="Insufficient stock holdings for SELL transaction.",
            )
        account.cash_balance += cost - tx_fee
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
        tax_fee=tx_fee,
        acc_cd=acc_cd,
        date=tx_date,
    )
    db.add(new_tx)
    db.flush()

    recalculate_portfolio_for_account(db, acc_cd)
    db.commit()

    if tx_type == "BUY" and is_new_stock and background_tasks is not None:
        _sync_ohlcv_in_background(background_tasks, tx_input.code)

    return {
        "status": "success",
        "message": "Transaction recorded and portfolio recalculated successfully.",
    }


def delete_transaction(db: Session, tx_id: int) -> dict:
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
    if not tx:
        raise HTTPException(
            status_code=404,
            detail=f"Transaction with ID {tx_id} not found.",
        )

    acc_cd = tx.acc_cd
    db.delete(tx)
    db.flush()

    recalculate_portfolio_for_account(db, acc_cd)
    db.commit()

    return {
        "status": "success",
        "message": "Transaction deleted and portfolio reversed successfully.",
    }


def update_transaction(db: Session, tx_id: int, tx_input) -> dict:
    tx = db.query(Transaction).filter(Transaction.id == tx_id).first()
    if not tx:
        raise HTTPException(
            status_code=404,
            detail=f"Transaction with ID {tx_id} not found.",
        )

    new_acc_cd = tx_input.acc_cd or "A001"
    tx_type = tx_input.type.upper()
    if tx_type not in TRANSACTION_TYPES:
        raise HTTPException(
            status_code=400,
            detail="Invalid transaction type. Only BUY or SELL are allowed.",
        )
    if tx_input.quantity <= 0 or tx_input.price <= 0:
        raise HTTPException(
            status_code=400,
            detail="Quantity and price must be greater than zero.",
        )

    tx_date = _parse_transaction_date(tx_input.date)
    old_acc_cd = tx.acc_cd

    tx.type = tx_type
    tx.code = tx_input.code
    tx.name = tx_input.name
    tx.quantity = tx_input.quantity
    tx.price = tx_input.price
    tx.tax_fee = tx_input.tax_fee or 0
    tx.acc_cd = new_acc_cd
    tx.date = tx_date

    db.flush()
    recalculate_portfolio_for_account(db, old_acc_cd)
    if old_acc_cd != new_acc_cd:
        recalculate_portfolio_for_account(db, new_acc_cd)
    db.commit()

    return {
        "status": "success",
        "message": "Transaction updated and portfolio recalculated successfully.",
    }

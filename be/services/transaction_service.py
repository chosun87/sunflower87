from datetime import datetime
from typing import Any, Dict, List, Tuple

from sqlalchemy.orm import Session

from core.exceptions import NotFoundException
from database import Account, StockCache, Transaction, TransactionCash


def get_transactions(
    db: Session,
    acc_cd: str = None,
    stock_code: str = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = None,
) -> List[Dict[str, Any]]:
    query = (
        db.query(
            Transaction, StockCache.stock_name, Account.acc_nm, Account.acc_company_nm
        )
        .outerjoin(StockCache, Transaction.stock_code == StockCache.stock_code)
        .outerjoin(Account, Transaction.acc_cd == Account.acc_cd)
        .filter(Transaction.dt_deleted.is_(None))
    )

    if acc_cd:
        query = query.filter(Transaction.acc_cd == acc_cd)
    if stock_code:
        query = query.filter(Transaction.stock_code == stock_code)
    if start_date:
        query = query.filter(Transaction.dt_trade >= start_date)
    if end_date:
        query = query.filter(Transaction.dt_trade <= end_date)

    query = query.order_by(Transaction.dt_trade.desc())
    if limit is not None:
        query = query.limit(limit)

    results = query.all()
    data = []
    for tx, name, acc_nm, acc_company_nm in results:
        t_dict = {c.name: getattr(tx, c.name) for c in tx.__table__.columns}
        t_dict["stock_name"] = name
        t_dict["acc_nm"] = acc_nm
        t_dict["acc_company_nm"] = acc_company_nm
        t_dict["trade_type"] = tx.trade_type
        data.append(t_dict)
    return data


def get_transaction(db: Session, id: int) -> Dict[str, Any]:
    tx = (
        db.query(Transaction)
        .filter(Transaction.id == id, Transaction.dt_deleted.is_(None))
        .first()
    )
    if not tx:
        raise NotFoundException("Transaction not found")
    name = (
        db.query(StockCache.stock_name)
        .filter(StockCache.stock_code == tx.stock_code)
        .scalar()
    )
    t_dict = {c.name: getattr(tx, c.name) for c in tx.__table__.columns}
    t_dict["stock_name"] = name
    return t_dict


def create_transaction(
    db: Session,
    acc_cd: str,
    dt_trade: str,
    trade_type: str,
    stock_code: str,
    quantity: int,
    price: int,
    tax_fee: int,
) -> Transaction:
    new_tx = Transaction(
        acc_cd=acc_cd,
        dt_trade=dt_trade,
        trade_type=trade_type,
        stock_code=stock_code,
        quantity=quantity,
        price=price,
        tax_fee=tax_fee,
    )
    db.add(new_tx)
    db.commit()
    return new_tx


def update_transaction(
    db: Session,
    id: int,
    acc_cd: str = None,
    stock_code: str = None,
    dt_trade: str = None,
    trade_type: str = None,
    quantity: int = None,
    price: int = None,
    tax_fee: int = None,
) -> Tuple[Transaction, str, str]:
    db_tx = (
        db.query(Transaction)
        .filter(Transaction.id == id, Transaction.dt_deleted.is_(None))
        .first()
    )
    if not db_tx:
        raise NotFoundException("Transaction not found")

    old_acc_cd = db_tx.acc_cd

    if acc_cd is not None:
        db_tx.acc_cd = acc_cd
    if stock_code is not None:
        db_tx.stock_code = stock_code
    if dt_trade:
        db_tx.dt_trade = dt_trade
    if trade_type:
        db_tx.trade_type = trade_type
    if quantity is not None:
        db_tx.quantity = quantity
    if price is not None:
        db_tx.price = price
    if tax_fee is not None:
        db_tx.tax_fee = tax_fee

    db.commit()
    return db_tx, old_acc_cd, db_tx.acc_cd


def delete_transaction(db: Session, id: int) -> str:
    db_tx = (
        db.query(Transaction)
        .filter(Transaction.id == id, Transaction.dt_deleted.is_(None))
        .first()
    )
    if not db_tx:
        raise NotFoundException("Transaction not found")

    acc_cd = db_tx.acc_cd
    db_tx.dt_deleted = datetime.utcnow()
    db.commit()
    return acc_cd


# --- Transaction Cash ---


def get_transaction_cash(
    db: Session,
    acc_cd: str = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = None,
) -> List[Dict[str, Any]]:
    query = (
        db.query(TransactionCash, Account.acc_nm, Account.acc_company_nm)
        .outerjoin(Account, TransactionCash.acc_cd == Account.acc_cd)
        .filter(TransactionCash.dt_deleted.is_(None))
    )
    if acc_cd:
        query = query.filter(TransactionCash.acc_cd == acc_cd)
    if start_date:
        query = query.filter(TransactionCash.dt_cash >= start_date)
    if end_date:
        query = query.filter(TransactionCash.dt_cash <= end_date)

    query = query.order_by(TransactionCash.dt_cash.desc())
    if limit is not None:
        query = query.limit(limit)

    results = query.all()
    data = []
    for tx, acc_nm, acc_company_nm in results:
        t_dict = {c.name: getattr(tx, c.name) for c in tx.__table__.columns}
        t_dict["acc_nm"] = acc_nm
        t_dict["acc_company_nm"] = acc_company_nm
        data.append(t_dict)
    return data


def get_cash_transaction(db: Session, id: int) -> TransactionCash:
    tx = (
        db.query(TransactionCash)
        .filter(TransactionCash.id == id, TransactionCash.dt_deleted.is_(None))
        .first()
    )
    if not tx:
        raise NotFoundException("TransactionCash not found")
    return tx


def create_cash_transaction(
    db: Session,
    acc_cd: str,
    dt_cash: str,
    cash_type: str,
    amount: int,
    description: str,
) -> TransactionCash:
    new_tx = TransactionCash(
        acc_cd=acc_cd,
        dt_cash=dt_cash,
        cash_type=cash_type,
        amount=amount,
        description=description,
    )
    db.add(new_tx)
    db.commit()
    return new_tx


def update_cash_transaction(
    db: Session,
    id: int,
    acc_cd: str = None,
    dt_cash: str = None,
    cash_type: str = None,
    amount: int = None,
    description: str = None,
) -> Tuple[TransactionCash, str, str]:
    tx = get_cash_transaction(db, id)
    old_acc_cd = tx.acc_cd

    if acc_cd is not None:
        tx.acc_cd = acc_cd
    if dt_cash is not None:
        tx.dt_cash = dt_cash
    if cash_type is not None:
        tx.cash_type = cash_type
    if amount is not None:
        tx.amount = amount
    if description is not None:
        tx.description = description

    db.commit()
    db.refresh(tx)
    return tx, old_acc_cd, tx.acc_cd


def delete_cash_transaction(db: Session, id: int) -> str:
    tx = get_cash_transaction(db, id)
    acc_cd = tx.acc_cd
    tx.dt_deleted = datetime.utcnow()
    db.commit()
    return acc_cd

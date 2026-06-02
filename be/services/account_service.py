from datetime import datetime
from typing import List

from sqlalchemy.orm import Session

from core.exceptions import BadRequestException, NotFoundException
from database import Account, AccountBalanceDaily


def get_all_accounts(db: Session, include_deleted: bool = False) -> List[Account]:
    query = db.query(Account)
    if not include_deleted:
        query = query.filter(Account.dt_deleted.is_(None))
    return query.order_by(Account.acc_order.asc()).all()


def get_account(db: Session, acc_cd: str) -> Account:
    account = (
        db.query(Account)
        .filter(Account.acc_cd == acc_cd, Account.dt_deleted.is_(None))
        .first()
    )
    if not account:
        raise NotFoundException("Account not found")
    return account


def create_account(
    db: Session,
    acc_cd: str,
    acc_nm: str,
    acc_company_nm: str,
    acc_order: int,
    dt_opened: str,
) -> Account:
    existing = db.query(Account).filter(Account.acc_cd == acc_cd).first()
    if existing:
        raise BadRequestException("Account code already exists")
    new_account = Account(
        acc_cd=acc_cd,
        acc_nm=acc_nm,
        acc_company_nm=acc_company_nm,
        acc_order=acc_order,
        dt_opened=dt_opened,
        cash_balance=0,
    )
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    return new_account


def update_account(
    db: Session,
    acc_cd: str,
    acc_nm: str = None,
    acc_company_nm: str = None,
    acc_order: int = None,
    dt_opened: str = None,
) -> Account:
    db_account = get_account(db, acc_cd)
    if acc_nm is not None:
        db_account.acc_nm = acc_nm
    if acc_company_nm is not None:
        db_account.acc_company_nm = acc_company_nm
    if acc_order is not None:
        db_account.acc_order = acc_order
    if dt_opened is not None:
        db_account.dt_opened = dt_opened
    db.commit()
    db.refresh(db_account)
    return db_account


def delete_account(db: Session, acc_cd: str):
    db_account = get_account(db, acc_cd)
    db_account.dt_deleted = datetime.utcnow()
    db.commit()


def reorder_accounts(db: Session, acc_orders: List[str]):
    for index, acc_cd in enumerate(acc_orders):
        acc = db.query(Account).filter(Account.acc_cd == acc_cd).first()
        if acc:
            acc.acc_order = index + 1
    db.commit()


# Daily Balances


def get_balance_daily(db: Session, acc_cd: str) -> List[AccountBalanceDaily]:
    return (
        db.query(AccountBalanceDaily)
        .filter(AccountBalanceDaily.acc_cd == acc_cd)
        .order_by(AccountBalanceDaily.trade_date.asc())
        .all()
    )


def get_balance_daily_by_date(
    db: Session, acc_cd: str, trade_date: str
) -> AccountBalanceDaily:
    balance = (
        db.query(AccountBalanceDaily)
        .filter(
            AccountBalanceDaily.acc_cd == acc_cd,
            AccountBalanceDaily.trade_date == trade_date,
        )
        .first()
    )
    if not balance:
        raise NotFoundException("Daily balance not found")
    return balance


def create_balance_daily(
    db: Session,
    acc_cd: str,
    trade_date: str,
    cash_balance: int,
    stock_eval_balance: int,
    total_balance: int,
    return_rate: float,
) -> AccountBalanceDaily:
    existing = (
        db.query(AccountBalanceDaily)
        .filter(
            AccountBalanceDaily.acc_cd == acc_cd,
            AccountBalanceDaily.trade_date == trade_date,
        )
        .first()
    )
    if existing:
        raise BadRequestException("Daily balance for this date already exists")

    new_bal = AccountBalanceDaily(
        acc_cd=acc_cd,
        trade_date=trade_date,
        cash_balance=cash_balance,
        stock_eval_balance=stock_eval_balance,
        total_balance=total_balance,
        return_rate=return_rate,
    )
    db.add(new_bal)
    db.commit()
    db.refresh(new_bal)
    return new_bal


def update_balance_daily(
    db: Session,
    acc_cd: str,
    trade_date: str,
    cash_balance: int = None,
    stock_eval_balance: int = None,
    total_balance: int = None,
    return_rate: float = None,
) -> AccountBalanceDaily:
    balance = get_balance_daily_by_date(db, acc_cd, trade_date)
    if cash_balance is not None:
        balance.cash_balance = cash_balance
    if stock_eval_balance is not None:
        balance.stock_eval_balance = stock_eval_balance
    if total_balance is not None:
        balance.total_balance = total_balance
    if return_rate is not None:
        balance.return_rate = return_rate
    db.commit()
    db.refresh(balance)
    return balance


def delete_balance_daily(db: Session, acc_cd: str, trade_date: str):
    balance = get_balance_daily_by_date(db, acc_cd, trade_date)
    db.delete(balance)
    db.commit()

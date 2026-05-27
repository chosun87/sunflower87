from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import schemas
from database import Account, AccountDailyBalance, get_db
from services.portfolio_service import recalculate_portfolio_for_account
from services.daily_balance_service import sync_daily_balances_for_account

router = APIRouter(prefix="/api/accounts", tags=["Account"])


@router.get("", response_model=schemas.ApiResponse[List[schemas.AccountResponse]])
def get_accounts(db: Session = Depends(get_db)):
    accounts = (
        db.query(Account)
        .filter(Account.dt_deleted.is_(None))
        .order_by(Account.acc_order.asc())
        .all()
    )
    return {"status": "success", "data": accounts}


@router.get("/{acc_cd}", response_model=schemas.ApiResponse[schemas.AccountResponse])
def get_account(acc_cd: str, db: Session = Depends(get_db)):
    account = (
        db.query(Account)
        .filter(Account.acc_cd == acc_cd, Account.dt_deleted.is_(None))
        .first()
    )
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"status": "success", "data": account}


@router.post(
    "", status_code=201, response_model=schemas.ApiResponse[schemas.AccountResponse]
)
def create_account(account: schemas.AccountCreate, db: Session = Depends(get_db)):
    existing = db.query(Account).filter(Account.acc_cd == account.acc_cd).first()
    if existing:
        raise HTTPException(status_code=400, detail="Account code already exists")
    new_account = Account(
        acc_cd=account.acc_cd,
        acc_nm=account.acc_nm,
        acc_company_nm=account.acc_company_nm,
        acc_order=account.acc_order,
        cash_balance=0,
    )
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    return {"status": "success", "data": new_account}


@router.put("/{acc_cd}", response_model=schemas.ApiResponse[schemas.AccountResponse])
def update_account(
    acc_cd: str, account: schemas.AccountUpdate, db: Session = Depends(get_db)
):
    db_account = (
        db.query(Account)
        .filter(Account.acc_cd == acc_cd, Account.dt_deleted.is_(None))
        .first()
    )
    if not db_account:
        raise HTTPException(status_code=404, detail="Account not found")
    if account.acc_nm is not None:
        db_account.acc_nm = account.acc_nm
    if account.acc_order is not None:
        db_account.acc_order = account.acc_order
    db.commit()
    db.refresh(db_account)
    return {"status": "success", "data": db_account}


@router.delete("/{acc_cd}")
def delete_account(acc_cd: str, db: Session = Depends(get_db)):
    db_account = (
        db.query(Account)
        .filter(Account.acc_cd == acc_cd, Account.dt_deleted.is_(None))
        .first()
    )
    if not db_account:
        raise HTTPException(status_code=404, detail="Account not found")
    db_account.dt_deleted = datetime.utcnow()
    db.commit()
    return {"status": "success", "message": "Account deleted successfully."}


@router.put("/reorder")
def reorder_accounts(acc_orders: List[str], db: Session = Depends(get_db)):
    for index, acc_cd in enumerate(acc_orders):
        acc = db.query(Account).filter(Account.acc_cd == acc_cd).first()
        if acc:
            acc.acc_order = index + 1
    db.commit()
    return {"status": "success", "message": "Account order updated successfully."}


@router.post("/{acc_cd}/recalculate-balances")
def recalculate_balances(acc_cd: str, db: Session = Depends(get_db)):
    recalculate_portfolio_for_account(db, acc_cd)
    return {"status": "success", "message": "Daily balances recalculated successfully."}


@router.post("/sync-all-daily-balances")
def sync_all_daily_balances(db: Session = Depends(get_db)):
    accounts = db.query(Account).filter(Account.dt_deleted.is_(None)).all()
    results = []
    for acc in accounts:
        res = sync_daily_balances_for_account(db, acc.acc_cd)
        results.append({"acc_cd": acc.acc_cd, "result": res})
    return {"status": "success", "data": results}


@router.post("/{acc_cd}/sync-daily-balances")
def sync_account_daily_balances(acc_cd: str, db: Session = Depends(get_db)):
    res = sync_daily_balances_for_account(db, acc_cd)
    return res


@router.get("/{acc_cd}/daily-balances")
def get_daily_balances(acc_cd: str, db: Session = Depends(get_db)):
    balances = (
        db.query(AccountDailyBalance)
        .filter(AccountDailyBalance.acc_cd == acc_cd)
        .order_by(AccountDailyBalance.trade_date.asc())
        .all()
    )
    return {"status": "success", "data": balances}


@router.get("/{acc_cd}/performance")
def get_performance(acc_cd: str, db: Session = Depends(get_db)):
    balances = (
        db.query(AccountDailyBalance)
        .filter(AccountDailyBalance.acc_cd == acc_cd)
        .order_by(AccountDailyBalance.trade_date.asc())
        .all()
    )
    return {"status": "success", "performance": balances}


@router.get(
    "/{acc_cd}/daily-balances/{trade_date}",
    response_model=schemas.ApiResponse[schemas.AccountDailyBalanceResponse],
)
def get_daily_balance(acc_cd: str, trade_date: str, db: Session = Depends(get_db)):
    balance = (
        db.query(AccountDailyBalance)
        .filter(
            AccountDailyBalance.acc_cd == acc_cd,
            AccountDailyBalance.trade_date == trade_date,
        )
        .first()
    )
    if not balance:
        raise HTTPException(status_code=404, detail="Daily balance not found")
    return {"status": "success", "data": balance}


@router.post(
    "/{acc_cd}/daily-balances",
    status_code=201,
    response_model=schemas.ApiResponse[schemas.AccountDailyBalanceResponse],
)
def create_daily_balance(
    acc_cd: str,
    balance: schemas.AccountDailyBalanceCreate,
    db: Session = Depends(get_db),
):
    existing = (
        db.query(AccountDailyBalance)
        .filter(
            AccountDailyBalance.acc_cd == acc_cd,
            AccountDailyBalance.trade_date == balance.trade_date,
        )
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400, detail="Daily balance for this date already exists"
        )

    new_bal = AccountDailyBalance(
        acc_cd=acc_cd,
        trade_date=balance.trade_date,
        cash_balance=balance.cash_balance,
        stock_eval_balance=balance.stock_eval_balance,
        total_balance=balance.total_balance,
        return_rate=balance.return_rate,
    )
    db.add(new_bal)
    db.commit()
    db.refresh(new_bal)
    return {"status": "success", "data": new_bal}


@router.put(
    "/{acc_cd}/daily-balances/{trade_date}",
    response_model=schemas.ApiResponse[schemas.AccountDailyBalanceResponse],
)
def update_daily_balance(
    acc_cd: str,
    trade_date: str,
    balance_data: schemas.AccountDailyBalanceUpdate,
    db: Session = Depends(get_db),
):
    balance = (
        db.query(AccountDailyBalance)
        .filter(
            AccountDailyBalance.acc_cd == acc_cd,
            AccountDailyBalance.trade_date == trade_date,
        )
        .first()
    )
    if not balance:
        raise HTTPException(status_code=404, detail="Daily balance not found")

    if balance_data.cash_balance is not None:
        balance.cash_balance = balance_data.cash_balance
    if balance_data.stock_eval_balance is not None:
        balance.stock_eval_balance = balance_data.stock_eval_balance
    if balance_data.total_balance is not None:
        balance.total_balance = balance_data.total_balance
    if balance_data.return_rate is not None:
        balance.return_rate = balance_data.return_rate

    db.commit()
    db.refresh(balance)
    return {"status": "success", "data": balance}


@router.delete("/{acc_cd}/daily-balances/{trade_date}")
def delete_daily_balance(acc_cd: str, trade_date: str, db: Session = Depends(get_db)):
    balance = (
        db.query(AccountDailyBalance)
        .filter(
            AccountDailyBalance.acc_cd == acc_cd,
            AccountDailyBalance.trade_date == trade_date,
        )
        .first()
    )
    if not balance:
        raise HTTPException(status_code=404, detail="Daily balance not found")

    db.delete(balance)
    db.commit()
    return {
        "status": "success",
        "message": "Daily balance record deleted successfully.",
    }

from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Account, AccountDailyBalance
import schemas
from portfolio import recalculate_portfolio_for_account

router = APIRouter(prefix="/api/accounts", tags=["Account"])

@router.get("", response_model=schemas.ApiResponse[List[schemas.AccountResponse]])
def get_accounts(db: Session = Depends(get_db)):
    accounts = db.query(Account).filter(Account.dt_deleted.is_(None)).order_by(Account.acc_order.asc()).all()
    return {"status": "success", "data": accounts}

@router.get("/{acc_cd}", response_model=schemas.ApiResponse[schemas.AccountResponse])
def get_account(acc_cd: str, db: Session = Depends(get_db)):
    account = db.query(Account).filter(Account.acc_cd == acc_cd, Account.dt_deleted.is_(None)).first()
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"status": "success", "data": account}

@router.post("", status_code=201, response_model=schemas.ApiResponse[schemas.AccountResponse])
def create_account(account: schemas.AccountCreate, db: Session = Depends(get_db)):
    existing = db.query(Account).filter(Account.acc_cd == account.acc_cd).first()
    if existing:
        raise HTTPException(status_code=400, detail="Account code already exists")
    new_account = Account(
        acc_cd=account.acc_cd,
        acc_nm=account.acc_nm,
        acc_company_nm=account.acc_company_nm,
        acc_order=account.acc_order,
        initial_cash=account.initial_cash,
        cash_balance=account.initial_cash
    )
    db.add(new_account)
    db.commit()
    db.refresh(new_account)
    return {"status": "success", "data": new_account}

@router.put("/{acc_cd}", response_model=schemas.ApiResponse[schemas.AccountResponse])
def update_account(acc_cd: str, account: schemas.AccountUpdate, db: Session = Depends(get_db)):
    db_account = db.query(Account).filter(Account.acc_cd == acc_cd, Account.dt_deleted.is_(None)).first()
    if not db_account:
        raise HTTPException(status_code=404, detail="Account not found")
    if account.acc_nm is not None: db_account.acc_nm = account.acc_nm
    if account.acc_order is not None: db_account.acc_order = account.acc_order
    if account.initial_cash is not None:
        db_account.initial_cash = account.initial_cash
        db.commit()
        recalculate_portfolio_for_account(db, acc_cd)
    db.commit()
    db.refresh(db_account)
    return {"status": "success", "data": db_account}

@router.delete("/{acc_cd}")
def delete_account(acc_cd: str, db: Session = Depends(get_db)):
    db_account = db.query(Account).filter(Account.acc_cd == acc_cd, Account.dt_deleted.is_(None)).first()
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

@router.get("/{acc_cd}/daily-balances")
def get_daily_balances(acc_cd: str, db: Session = Depends(get_db)):
    balances = db.query(AccountDailyBalance).filter(AccountDailyBalance.acc_cd == acc_cd).order_by(AccountDailyBalance.trade_date.asc()).all()
    return {"status": "success", "data": balances}

@router.get("/{acc_cd}/performance")
def get_performance(acc_cd: str, db: Session = Depends(get_db)):
    balances = db.query(AccountDailyBalance).filter(AccountDailyBalance.acc_cd == acc_cd).order_by(AccountDailyBalance.trade_date.asc()).all()
    return {"status": "success", "performance": balances}

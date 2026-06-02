from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import schemas
import services.account_service as account_service
from core.responses import success_response
from database import get_db
from services.account_balance_daily_service import sync_account_balance_daily
from services.portfolio_service import recalculate_portfolio_for_account

router = APIRouter(prefix="/api/accounts", tags=["Account"])


@router.get("", response_model=schemas.ApiResponse[List[schemas.AccountResponse]])
def get_accounts(include_deleted: bool = False, db: Session = Depends(get_db)):
    accounts = account_service.get_all_accounts(db, include_deleted)
    return success_response(accounts)


@router.get("/{acc_cd}", response_model=schemas.ApiResponse[schemas.AccountResponse])
def get_account(acc_cd: str, db: Session = Depends(get_db)):
    account = account_service.get_account(db, acc_cd)
    return success_response(account)


@router.post(
    "", status_code=201, response_model=schemas.ApiResponse[schemas.AccountResponse]
)
def create_account(account: schemas.AccountCreate, db: Session = Depends(get_db)):
    new_account = account_service.create_account(
        db,
        account.acc_cd,
        account.acc_nm,
        account.acc_company_nm,
        account.acc_order,
        account.dt_opened,
    )
    return success_response(new_account)


@router.put("/{acc_cd}", response_model=schemas.ApiResponse[schemas.AccountResponse])
def update_account(
    acc_cd: str, account: schemas.AccountUpdate, db: Session = Depends(get_db)
):
    updated = account_service.update_account(
        db,
        acc_cd,
        account.acc_nm,
        account.acc_company_nm,
        account.acc_order,
        account.dt_opened,
    )
    return success_response(updated)


@router.delete("/{acc_cd}")
def delete_account(acc_cd: str, db: Session = Depends(get_db)):
    account_service.delete_account(db, acc_cd)
    return success_response(message="Account deleted successfully.")


@router.put("/reorder")
def reorder_accounts(acc_orders: List[str], db: Session = Depends(get_db)):
    account_service.reorder_accounts(db, acc_orders)
    return success_response(message="Account order updated successfully.")


@router.post("/{acc_cd}/recalculate_balances")
def recalculate_balances(acc_cd: str, db: Session = Depends(get_db)):
    recalculate_portfolio_for_account(db, acc_cd)
    return success_response(message="Daily balances recalculated successfully.")


@router.post("/sync_balance_daily")
def sync_all_account_balance_daily(
    request: schemas.SyncAccountDailyBalanceRequest = None,
    db: Session = Depends(get_db),
):
    accounts = account_service.get_all_accounts(db, include_deleted=False)
    results = []
    req_start = request.start_date if request else None
    req_end = request.end_date if request else None
    for acc in accounts:
        res = sync_account_balance_daily(db, acc.acc_cd, req_start, req_end)
        results.append({"acc_cd": acc.acc_cd, "result": res})
    return success_response(results)


@router.post("/{acc_cd}/sync_balance_daily")
def sync_specific_account_balance_daily(
    acc_cd: str,
    request: schemas.SyncAccountDailyBalanceRequest = None,
    db: Session = Depends(get_db),
):
    req_start = request.start_date if request else None
    req_end = request.end_date if request else None
    res = sync_account_balance_daily(db, acc_cd, req_start, req_end)
    return success_response(res)


@router.get("/{acc_cd}/balance_daily")
def get_balance_daily(acc_cd: str, db: Session = Depends(get_db)):
    balances = account_service.get_balance_daily(db, acc_cd)
    return success_response(balances)


@router.get("/{acc_cd}/performance")
def get_performance(acc_cd: str, db: Session = Depends(get_db)):
    balances = account_service.get_balance_daily(db, acc_cd)
    # The original router wrapped this in {"status": "success", "performance": balances} instead of "data": balances.
    # To keep exact backward compatibility with the frontend format:
    return {"status": "success", "performance": balances}


@router.get(
    "/{acc_cd}/balance_daily/{trade_date}",
    response_model=schemas.ApiResponse[schemas.AccountDailyBalanceResponse],
)
def get_balance_daily_by_date(
    acc_cd: str, trade_date: str, db: Session = Depends(get_db)
):
    balance = account_service.get_balance_daily_by_date(db, acc_cd, trade_date)
    return success_response(balance)


@router.post(
    "/{acc_cd}/balance_daily",
    status_code=201,
    response_model=schemas.ApiResponse[schemas.AccountDailyBalanceResponse],
)
def create_balance_daily(
    acc_cd: str,
    balance: schemas.AccountDailyBalanceCreate,
    db: Session = Depends(get_db),
):
    new_bal = account_service.create_balance_daily(
        db,
        acc_cd,
        balance.trade_date,
        balance.cash_balance,
        balance.stock_eval_balance,
        balance.total_balance,
        balance.return_rate,
    )
    return success_response(new_bal)


@router.put(
    "/{acc_cd}/balance_daily/{trade_date}",
    response_model=schemas.ApiResponse[schemas.AccountDailyBalanceResponse],
)
def update_balance_daily(
    acc_cd: str,
    trade_date: str,
    balance_data: schemas.AccountDailyBalanceUpdate,
    db: Session = Depends(get_db),
):
    updated = account_service.update_balance_daily(
        db,
        acc_cd,
        trade_date,
        balance_data.cash_balance,
        balance_data.stock_eval_balance,
        balance_data.total_balance,
        balance_data.return_rate,
    )
    return success_response(updated)


@router.delete("/{acc_cd}/balance_daily/{trade_date}")
def delete_balance_daily(acc_cd: str, trade_date: str, db: Session = Depends(get_db)):
    account_service.delete_balance_daily(db, acc_cd, trade_date)
    return success_response(message="Daily balance record deleted successfully.")

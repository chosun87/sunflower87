from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import schemas
import services.transaction_service as transaction_service
from core.responses import success_response
from database import get_db
from services.portfolio_service import recalculate_portfolio_for_account

router = APIRouter(prefix="/api/transactions_cash", tags=["TransactionCash"])


@router.get(
    "", response_model=schemas.ApiResponse[List[schemas.TransactionCashResponse]]
)
def get_transaction_cash(
    acc_cd: str = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = None,
    db: Session = Depends(get_db),
):
    data = transaction_service.get_transaction_cash(
        db, acc_cd, start_date, end_date, limit
    )
    return success_response(data)


@router.get(
    "/{id}", response_model=schemas.ApiResponse[schemas.TransactionCashResponse]
)
def get_cash_transaction(id: int, db: Session = Depends(get_db)):
    tx = transaction_service.get_cash_transaction(db, id)
    return success_response(tx)


@router.post(
    "",
    status_code=201,
    response_model=schemas.ApiResponse[schemas.TransactionCashResponse],
)
def add_cash_transaction(
    tx: schemas.TransactionCashCreate, db: Session = Depends(get_db)
):
    new_tx = transaction_service.create_cash_transaction(
        db, tx.acc_cd, tx.dt_cash, tx.cash_type.value, tx.amount, tx.description
    )
    recalculate_portfolio_for_account(db, tx.acc_cd)
    return success_response(new_tx)


@router.put(
    "/{id}", response_model=schemas.ApiResponse[schemas.TransactionCashResponse]
)
def update_cash_transaction(
    id: int, tx_data: schemas.TransactionCashUpdate, db: Session = Depends(get_db)
):
    tx, old_acc_cd, new_acc_cd = transaction_service.update_cash_transaction(
        db,
        id,
        tx_data.acc_cd,
        tx_data.dt_cash,
        tx_data.cash_type.value if tx_data.cash_type else None,
        tx_data.amount,
        tx_data.description,
    )

    recalculate_portfolio_for_account(db, old_acc_cd)
    if new_acc_cd and new_acc_cd != old_acc_cd:
        recalculate_portfolio_for_account(db, new_acc_cd)

    return success_response(tx)


@router.delete("/{id}")
def delete_cash_transaction(id: int, db: Session = Depends(get_db)):
    acc_cd = transaction_service.delete_cash_transaction(db, id)
    recalculate_portfolio_for_account(db, acc_cd)
    return success_response(message="Cash transaction deleted & portfolio rolled back.")

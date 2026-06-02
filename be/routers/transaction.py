from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import schemas
import services.transaction_service as transaction_service
from core.responses import success_response
from database import get_db
from services.portfolio_service import recalculate_portfolio_for_account

router = APIRouter(prefix="/api/transactions", tags=["Transaction"])


@router.get("", response_model=schemas.ApiResponse[List[schemas.TransactionResponse]])
def get_transactions(
    acc_cd: str = None,
    stock_code: str = None,
    start_date: str = None,
    end_date: str = None,
    limit: int = None,
    db: Session = Depends(get_db),
):
    data = transaction_service.get_transactions(
        db, acc_cd, stock_code, start_date, end_date, limit
    )
    return success_response(data)


@router.get("/{id}", response_model=schemas.ApiResponse[schemas.TransactionResponse])
def get_transaction(id: int, db: Session = Depends(get_db)):
    t_dict = transaction_service.get_transaction(db, id)
    return success_response(t_dict)


@router.post(
    "", status_code=201, response_model=schemas.ApiResponse[schemas.TransactionResponse]
)
def add_transaction(tx: schemas.TransactionCreate, db: Session = Depends(get_db)):
    new_tx = transaction_service.create_transaction(
        db,
        tx.acc_cd,
        tx.dt_trade,
        tx.trade_type.value,
        tx.stock_code,
        tx.quantity,
        tx.price,
        tx.tax_fee,
    )
    recalculate_portfolio_for_account(db, tx.acc_cd)
    return success_response(new_tx)


@router.put("/{id}")
def update_transaction(
    id: int, tx_update: schemas.TransactionUpdate, db: Session = Depends(get_db)
):
    db_tx, old_acc_cd, new_acc_cd = transaction_service.update_transaction(
        db,
        id,
        tx_update.acc_cd,
        tx_update.stock_code,
        tx_update.dt_trade,
        tx_update.trade_type.value if tx_update.trade_type else None,
        tx_update.quantity,
        tx_update.price,
        tx_update.tax_fee,
    )

    recalculate_portfolio_for_account(db, old_acc_cd)
    if new_acc_cd and new_acc_cd != old_acc_cd:
        recalculate_portfolio_for_account(db, new_acc_cd)

    return success_response(db_tx)


@router.delete("/{id}")
def delete_transaction(id: int, db: Session = Depends(get_db)):
    acc_cd = transaction_service.delete_transaction(db, id)
    recalculate_portfolio_for_account(db, acc_cd)
    return success_response(message="Transaction deleted & portfolio rolled back.")

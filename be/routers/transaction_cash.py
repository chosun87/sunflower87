from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import schemas
from database import TransactionCash, get_db
from services.portfolio_service import recalculate_portfolio_for_account

router = APIRouter(prefix="/api/transactions_cash", tags=["TransactionCash"])


@router.get(
    "", response_model=schemas.ApiResponse[List[schemas.TransactionCashResponse]]
)
def get_transaction_cash(acc_cd: str = None, db: Session = Depends(get_db)):
    query = db.query(TransactionCash).filter(TransactionCash.dt_deleted.is_(None))
    if acc_cd:
        query = query.filter(TransactionCash.acc_cd == acc_cd)
    results = query.order_by(TransactionCash.dt_cash.desc()).all()
    return {"status": "success", "data": results}


@router.post(
    "",
    status_code=201,
    response_model=schemas.ApiResponse[schemas.TransactionCashResponse],
)
def add_cash_transaction(
    tx: schemas.TransactionCashCreate, db: Session = Depends(get_db)
):
    dt_cash_obj = datetime.strptime(tx.dt_cash, "%Y-%m-%d %H:%M:%S")
    new_tx = TransactionCash(
        acc_cd=tx.acc_cd,
        dt_cash=dt_cash_obj,
        cash_type=tx.cash_type.value,
        amount=tx.amount,
        description=tx.description,
    )
    db.add(new_tx)
    db.commit()
    recalculate_portfolio_for_account(db, tx.acc_cd)
    return {"status": "success", "data": new_tx}


@router.delete("/{id}")
def delete_cash_transaction(id: int, db: Session = Depends(get_db)):
    db_tx = (
        db.query(TransactionCash)
        .filter(TransactionCash.id == id, TransactionCash.dt_deleted.is_(None))
        .first()
    )
    if not db_tx:
        raise HTTPException(404, "TransactionCash not found")
    acc_cd = db_tx.acc_cd
    db_tx.dt_deleted = datetime.utcnow()
    db.commit()
    recalculate_portfolio_for_account(db, acc_cd)
    return {
        "status": "success",
        "message": "Cash transaction deleted & portfolio rolled back.",
    }


@router.get(
    "/{id}", response_model=schemas.ApiResponse[schemas.TransactionCashResponse]
)
def get_cash_transaction(id: int, db: Session = Depends(get_db)):
    tx = (
        db.query(TransactionCash)
        .filter(TransactionCash.id == id, TransactionCash.dt_deleted.is_(None))
        .first()
    )
    if not tx:
        raise HTTPException(status_code=404, detail="TransactionCash not found")
    return {"status": "success", "data": tx}


@router.put(
    "/{id}", response_model=schemas.ApiResponse[schemas.TransactionCashResponse]
)
def update_cash_transaction(
    id: int, tx_data: schemas.TransactionCashUpdate, db: Session = Depends(get_db)
):
    tx = (
        db.query(TransactionCash)
        .filter(TransactionCash.id == id, TransactionCash.dt_deleted.is_(None))
        .first()
    )
    if not tx:
        raise HTTPException(status_code=404, detail="TransactionCash not found")

    if tx_data.dt_cash is not None:
        tx.dt_cash = datetime.strptime(tx_data.dt_cash, "%Y-%m-%d %H:%M:%S")
    if tx_data.cash_type is not None:
        tx.cash_type = tx_data.cash_type.value
    if tx_data.amount is not None:
        tx.amount = tx_data.amount
    if tx_data.description is not None:
        tx.description = tx_data.description

    db.commit()
    recalculate_portfolio_for_account(db, tx.acc_cd)
    db.refresh(tx)
    return {"status": "success", "data": tx}

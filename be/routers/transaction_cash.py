from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import schemas
from database import TransactionCash, get_db
from portfolio import recalculate_portfolio_for_account

router = APIRouter(prefix="/api/transaction_cash", tags=["TransactionCash"])


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

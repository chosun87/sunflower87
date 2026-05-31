from datetime import datetime
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

import schemas
from database import Account, TransactionCash, get_db
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

    return {"status": "success", "data": data}


@router.post(
    "",
    status_code=201,
    response_model=schemas.ApiResponse[schemas.TransactionCashResponse],
)
def add_cash_transaction(
    tx: schemas.TransactionCashCreate, db: Session = Depends(get_db)
):
    new_tx = TransactionCash(
        acc_cd=tx.acc_cd,
        dt_cash=tx.dt_cash,
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

    old_acc_cd = tx.acc_cd

    if tx_data.acc_cd is not None:
        tx.acc_cd = tx_data.acc_cd
    if tx_data.dt_cash is not None:
        tx.dt_cash = tx_data.dt_cash
    if tx_data.cash_type is not None:
        tx.cash_type = tx_data.cash_type.value
    if tx_data.amount is not None:
        tx.amount = tx_data.amount
    if tx_data.description is not None:
        tx.description = tx_data.description

    db.commit()
    recalculate_portfolio_for_account(db, old_acc_cd)
    if tx_data.acc_cd and tx_data.acc_cd != old_acc_cd:
        recalculate_portfolio_for_account(db, tx_data.acc_cd)
    db.refresh(tx)
    return {"status": "success", "data": tx}

from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db, Transaction, StockCache
import schemas
from portfolio import recalculate_portfolio_for_account

router = APIRouter(prefix="/api/transactions", tags=["Transaction"])

@router.get("", response_model=schemas.ApiResponse[List[schemas.TransactionResponse]])
def get_transactions(acc_cd: str = None, stock_code: str = None, db: Session = Depends(get_db)):
    query = db.query(Transaction, StockCache.stock_name).outerjoin(StockCache, Transaction.stock_code == StockCache.stock_code).filter(Transaction.dt_deleted.is_(None))
    if acc_cd: query = query.filter(Transaction.acc_cd == acc_cd)
    if stock_code: query = query.filter(Transaction.stock_code == stock_code)
    
    results = query.order_by(Transaction.dt_trade.desc()).all()
    data = []
    for tx, name in results:
        t_dict = {c.name: getattr(tx, c.name) for c in tx.__table__.columns}
        t_dict["stock_name"] = name
        t_dict["trade_type"] = tx.trade_type
        data.append(t_dict)
    return {"status": "success", "data": data}

@router.get("/{id}", response_model=schemas.ApiResponse[schemas.TransactionResponse])
def get_transaction(id: int, db: Session = Depends(get_db)):
    tx = db.query(Transaction).filter(Transaction.id == id, Transaction.dt_deleted.is_(None)).first()
    if not tx: raise HTTPException(404, "Transaction not found")
    name = db.query(StockCache.stock_name).filter(StockCache.stock_code == tx.stock_code).scalar()
    t_dict = {c.name: getattr(tx, c.name) for c in tx.__table__.columns}
    t_dict["stock_name"] = name
    return {"status": "success", "data": t_dict}

@router.post("/add", status_code=201, response_model=schemas.ApiResponse[schemas.TransactionResponse])
def add_transaction(tx: schemas.TransactionCreate, db: Session = Depends(get_db)):
    dt_trade_obj = datetime.strptime(tx.dt_trade, "%Y-%m-%d %H:%M:%S")
    new_tx = Transaction(
        acc_cd=tx.acc_cd,
        dt_trade=dt_trade_obj,
        trade_type=tx.trade_type.value,
        stock_code=tx.stock_code,
        quantity=tx.quantity,
        price=tx.price,
        tax_fee=tx.tax_fee
    )
    db.add(new_tx)
    db.commit()
    recalculate_portfolio_for_account(db, tx.acc_cd)
    return {"status": "success", "data": new_tx}

@router.put("/{id}")
def update_transaction(id: int, tx_update: schemas.TransactionUpdate, db: Session = Depends(get_db)):
    db_tx = db.query(Transaction).filter(Transaction.id == id, Transaction.dt_deleted.is_(None)).first()
    if not db_tx: raise HTTPException(404, "Transaction not found")
    
    if tx_update.dt_trade: db_tx.dt_trade = datetime.strptime(tx_update.dt_trade, "%Y-%m-%d %H:%M:%S")
    if tx_update.trade_type: db_tx.trade_type = tx_update.trade_type.value
    if tx_update.quantity is not None: db_tx.quantity = tx_update.quantity
    if tx_update.price is not None: db_tx.price = tx_update.price
    if tx_update.tax_fee is not None: db_tx.tax_fee = tx_update.tax_fee
    
    db.commit()
    recalculate_portfolio_for_account(db, db_tx.acc_cd)
    return {"status": "success", "data": db_tx}

@router.delete("/{id}")
def delete_transaction(id: int, db: Session = Depends(get_db)):
    db_tx = db.query(Transaction).filter(Transaction.id == id, Transaction.dt_deleted.is_(None)).first()
    if not db_tx: raise HTTPException(404, "Transaction not found")
    
    acc_cd = db_tx.acc_cd
    db_tx.dt_deleted = datetime.utcnow()
    db.commit()
    recalculate_portfolio_for_account(db, acc_cd)
    return {"status": "success", "message": "Transaction deleted & portfolio rolled back."}

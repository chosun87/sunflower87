from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

import schemas
from database import StockOHLCVCache, get_db
from services.market_service import sync_ohlcv_cache

router = APIRouter(prefix="/api/stock_ohlcvs", tags=["StockOHLCV"])


@router.get("", response_model=schemas.ApiResponse[list[schemas.StockOHLCVResponse]])
def get_stock_ohlcvs(
    code: str, 
    start_date: str = None, 
    end_date: str = None, 
    background_tasks: BackgroundTasks = None, 
    db: Session = Depends(get_db)
):
    query = db.query(StockOHLCVCache).filter(StockOHLCVCache.stock_code == code)
    if start_date:
        query = query.filter(StockOHLCVCache.trade_date >= start_date)
    if end_date:
        query = query.filter(StockOHLCVCache.trade_date <= end_date)
        
    results = query.order_by(StockOHLCVCache.trade_date.asc()).all()
    
    # Background sync triggering
    if background_tasks:
        background_tasks.add_task(sync_ohlcv_cache, db, code)
        
    return {"status": "success", "data": results}


@router.get("/{stock_code}/{trade_date}", response_model=schemas.ApiResponse[schemas.StockOHLCVResponse])
def get_stock_ohlcv(stock_code: str, trade_date: str, db: Session = Depends(get_db)):
    result = db.query(StockOHLCVCache).filter(
        StockOHLCVCache.stock_code == stock_code,
        StockOHLCVCache.trade_date == trade_date
    ).first()
    if not result:
        raise HTTPException(status_code=404, detail="OHLCV record not found")
    return {"status": "success", "data": result}


@router.post("", status_code=201, response_model=schemas.ApiResponse[schemas.StockOHLCVResponse])
def create_stock_ohlcv(data: schemas.StockOHLCVCreate, db: Session = Depends(get_db)):
    existing = db.query(StockOHLCVCache).filter(
        StockOHLCVCache.stock_code == data.stock_code,
        StockOHLCVCache.trade_date == data.trade_date
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="OHLCV record already exists")
        
    new_record = StockOHLCVCache(
        stock_code=data.stock_code,
        trade_date=data.trade_date,
        open_price=data.open_price,
        high_price=data.high_price,
        low_price=data.low_price,
        close_price=data.close_price,
        volume=data.volume,
        trading_value=data.trading_value,
        fluctuation_rate=data.fluctuation_rate
    )
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    return {"status": "success", "data": new_record}


@router.put("/{stock_code}/{trade_date}", response_model=schemas.ApiResponse[schemas.StockOHLCVResponse])
def update_stock_ohlcv(stock_code: str, trade_date: str, update_data: schemas.StockOHLCVUpdate, db: Session = Depends(get_db)):
    record = db.query(StockOHLCVCache).filter(
        StockOHLCVCache.stock_code == stock_code,
        StockOHLCVCache.trade_date == trade_date
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="OHLCV record not found")
        
    if update_data.open_price is not None: record.open_price = update_data.open_price
    if update_data.high_price is not None: record.high_price = update_data.high_price
    if update_data.low_price is not None: record.low_price = update_data.low_price
    if update_data.close_price is not None: record.close_price = update_data.close_price
    if update_data.volume is not None: record.volume = update_data.volume
    if update_data.trading_value is not None: record.trading_value = update_data.trading_value
    if update_data.fluctuation_rate is not None: record.fluctuation_rate = update_data.fluctuation_rate
        
    db.commit()
    db.refresh(record)
    return {"status": "success", "data": record}


@router.delete("/{stock_code}/{trade_date}")
def delete_stock_ohlcv(stock_code: str, trade_date: str, db: Session = Depends(get_db)):
    record = db.query(StockOHLCVCache).filter(
        StockOHLCVCache.stock_code == stock_code,
        StockOHLCVCache.trade_date == trade_date
    ).first()
    if not record:
        raise HTTPException(status_code=404, detail="OHLCV record not found")
        
    db.delete(record)
    db.commit()
    return {"status": "success", "message": "OHLCV cache record deleted."}

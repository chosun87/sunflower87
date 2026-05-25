from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db, StockOHLCVCache
import schemas
from portfolio import sync_ohlcv_cache

router = APIRouter(prefix="/api/stock_ohlcv", tags=["StockOHLCV"])

@router.post("/refresh", status_code=202)
def refresh_prices(stock_code: str, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    # 1분 폴링 트리거를 위한 백그라운드 동기화 
    background_tasks.add_task(sync_ohlcv_cache, db, stock_code)
    return {"status": "success", "message": f"Background sync triggered for {stock_code}"}

@router.get("/{stock_code}", response_model=schemas.ApiResponse[list[schemas.StockOHLCVResponse]])
def get_stock_ohlcv(stock_code: str, db: Session = Depends(get_db)):
    results = db.query(StockOHLCVCache).filter(StockOHLCVCache.stock_code == stock_code).order_by(StockOHLCVCache.trade_date.asc()).all()
    return {"status": "success", "data": results}

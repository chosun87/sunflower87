from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db, Stock, StockCache
import schemas
from portfolio import get_enriched_accounts_data

router = APIRouter(prefix="/api/stocks", tags=["Stock"])

@router.get("/portfolio", response_model=dict)
def get_portfolio(db: Session = Depends(get_db)):
    return get_enriched_accounts_data(db)

@router.get("/masters", response_model=schemas.ApiResponse[list[schemas.StockCacheResponse]])
def get_stock_masters(db: Session = Depends(get_db)):
    masters = db.query(StockCache).filter(StockCache.dt_deleted.is_(None)).all()
    return {"status": "success", "data": masters}

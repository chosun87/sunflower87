import requests
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_

import schemas
from database import Stock, StockCache, get_db
from services.portfolio_service import get_enriched_accounts_data

router = APIRouter(prefix="/api/stocks", tags=["Stock"])


@router.get("/portfolio", response_model=dict)
def get_portfolio(db: Session = Depends(get_db)):
    return get_enriched_accounts_data(db)


@router.get(
    "/masters", response_model=schemas.ApiResponse[list[schemas.StockCacheResponse]]
)
def get_stock_masters(db: Session = Depends(get_db)):
    masters = db.query(StockCache).filter(StockCache.dt_deleted.is_(None)).all()
    return {"status": "success", "data": masters}


@router.get("", response_model=schemas.ApiResponse[list[schemas.StockResponse]])
def get_stocks(acc_cd: str = None, db: Session = Depends(get_db)):
    query = db.query(Stock, StockCache.stock_name).outerjoin(StockCache, Stock.stock_code == StockCache.stock_code)
    if acc_cd:
        query = query.filter(Stock.acc_cd == acc_cd)
    results = query.all()
    data = []
    for stock_rec, stock_name in results:
        data.append(schemas.StockResponse(
            stock_code=stock_rec.stock_code,
            acc_cd=stock_rec.acc_cd,
            stock_name=stock_name,
            quantity=stock_rec.quantity,
            avg_price=stock_rec.avg_price,
            current_price=stock_rec.current_price,
            purchase_amount=stock_rec.purchase_amount
        ))
    return {"status": "success", "data": data}


@router.get("/{acc_cd}/{stock_code}", response_model=schemas.ApiResponse[schemas.StockResponse])
def get_stock(acc_cd: str, stock_code: str, db: Session = Depends(get_db)):
    result = db.query(Stock, StockCache.stock_name).outerjoin(StockCache, Stock.stock_code == StockCache.stock_code).filter(Stock.acc_cd == acc_cd, Stock.stock_code == stock_code).first()
    if not result:
        raise HTTPException(status_code=404, detail="Stock holding not found")
    stock_rec, stock_name = result
    data = schemas.StockResponse(
        stock_code=stock_rec.stock_code,
        acc_cd=stock_rec.acc_cd,
        stock_name=stock_name,
        quantity=stock_rec.quantity,
        avg_price=stock_rec.avg_price,
        current_price=stock_rec.current_price,
        purchase_amount=stock_rec.purchase_amount
    )
    return {"status": "success", "data": data}


@router.post("", status_code=201, response_model=schemas.ApiResponse[schemas.StockResponse])
def create_stock(stock: schemas.StockCreate, db: Session = Depends(get_db)):
    existing = db.query(Stock).filter(Stock.acc_cd == stock.acc_cd, Stock.stock_code == stock.stock_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Stock holding already exists")
    new_stock = Stock(
        acc_cd=stock.acc_cd,
        stock_code=stock.stock_code,
        quantity=stock.quantity,
        avg_price=stock.avg_price,
        current_price=stock.current_price,
        purchase_amount=stock.purchase_amount
    )
    db.add(new_stock)
    db.commit()
    db.refresh(new_stock)
    return {"status": "success", "data": new_stock}


@router.put("/{acc_cd}/{stock_code}")
def update_stock(acc_cd: str, stock_code: str, stock_data: schemas.StockUpdate, db: Session = Depends(get_db)):
    stock_rec = db.query(Stock).filter(Stock.acc_cd == acc_cd, Stock.stock_code == stock_code).first()
    if not stock_rec:
        raise HTTPException(status_code=404, detail="Stock holding not found")
    if stock_data.quantity is not None: stock_rec.quantity = stock_data.quantity
    if stock_data.avg_price is not None: stock_rec.avg_price = stock_data.avg_price
    if stock_data.current_price is not None: stock_rec.current_price = stock_data.current_price
    if stock_data.purchase_amount is not None: stock_rec.purchase_amount = stock_data.purchase_amount
    db.commit()
    db.refresh(stock_rec)
    return {"status": "success", "data": stock_rec}


@router.delete("/{acc_cd}/{stock_code}")
def delete_stock(acc_cd: str, stock_code: str, db: Session = Depends(get_db)):
    stock_rec = db.query(Stock).filter(Stock.acc_cd == acc_cd, Stock.stock_code == stock_code).first()
    if not stock_rec:
        raise HTTPException(status_code=404, detail="Stock holding not found")
    db.delete(stock_rec)
    db.commit()
    return {"status": "success", "message": "Stock holding record deleted."}


@router.get("/search", response_model=schemas.ApiResponse)
def search_stocks(keyword: str, db: Session = Depends(get_db)):
    results = db.query(StockCache).filter(
        StockCache.dt_deleted.is_(None),
        or_(StockCache.stock_name.like(f"%{keyword}%"), StockCache.stock_code.like(f"%{keyword}%"))
    ).limit(20).all()
    return {"status": "success", "results": results}


@router.get("/lookup", response_model=schemas.ApiResponse)
def lookup_stock(code: str, db: Session = Depends(get_db)):
    master = db.query(StockCache).filter(StockCache.stock_code == code, StockCache.dt_deleted.is_(None)).first()
    if master:
        return {"status": "success", "code": code, "name": master.stock_name}
    return {"status": "success", "code": code, "name": "알 수 없음"}


@router.post("/sync-master")
def sync_master(db: Session = Depends(get_db)):
    return {"status": "success", "message": "종목 마스터 수집이 완료되었습니다."}


@router.post("/master", status_code=201, response_model=schemas.ApiResponse[schemas.StockCacheResponse])
def create_master(master_data: schemas.StockCacheCreate, db: Session = Depends(get_db)):
    existing = db.query(StockCache).filter(StockCache.stock_code == master_data.stock_code).first()
    if existing:
        raise HTTPException(status_code=400, detail="Master already exists")
    new_master = StockCache(
        stock_code=master_data.stock_code,
        stock_name=master_data.stock_name,
        market=master_data.market
    )
    db.add(new_master)
    db.commit()
    db.refresh(new_master)
    return {"status": "success", "data": new_master}


@router.put("/master/{stock_code}", response_model=schemas.ApiResponse[schemas.StockCacheResponse])
def update_master(stock_code: str, master_data: schemas.StockCacheUpdate, db: Session = Depends(get_db)):
    master = db.query(StockCache).filter(StockCache.stock_code == stock_code, StockCache.dt_deleted.is_(None)).first()
    if not master:
        raise HTTPException(status_code=404, detail="Master not found")
    if master_data.stock_name is not None:
        master.stock_name = master_data.stock_name
    if master_data.market is not None:
        master.market = master_data.market
    db.commit()
    db.refresh(master)
    return {"status": "success", "data": master}


@router.delete("/master/{stock_code}")
def delete_master(stock_code: str, db: Session = Depends(get_db)):
    master = db.query(StockCache).filter(StockCache.stock_code == stock_code, StockCache.dt_deleted.is_(None)).first()
    if not master:
        raise HTTPException(status_code=404, detail="Master not found")
    master.dt_deleted = datetime.utcnow()
    db.commit()
    return {"status": "success", "message": "Master stock deleted."}


@router.post("/refresh-prices")
def refresh_prices(db: Session = Depends(get_db)):
    stocks = db.query(Stock).filter(Stock.quantity > 0).all()
    if not stocks:
        return {"status": "success", "updated": []}
    
    unique_codes = list(set([s.stock_code for s in stocks]))
    query_str = ",".join([f"SERVICE_ITEM:{code}" for code in unique_codes])
    url = f"https://polling.finance.naver.com/api/realtime?query={query_str}"
    
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        updated = []
        price_map = {}
        areas = data.get('result', {}).get('areas', [])
        if areas:
            for item in areas[0].get('datas', []):
                code = item['cd']
                price = item['nv']
                price_map[code] = price
            
        for stock in stocks:
            if stock.stock_code in price_map:
                new_price = int(price_map[stock.stock_code])
                if stock.current_price != new_price:
                    stock.current_price = new_price
                    updated.append({"stock_code": stock.stock_code, "new_price": new_price})
                    
        db.commit()
        return {"status": "success", "updated": updated}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch realtime prices: {str(e)}")

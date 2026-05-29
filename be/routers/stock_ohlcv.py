from datetime import datetime

import requests
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from sqlalchemy.orm import Session

import schemas
from database import Stock, StockCache, StockOHLCVCache, get_db
from services.market_service import sync_ohlcv_cache

router = APIRouter(prefix="/api/stock_ohlcvs", tags=["StockOHLCV"])


@router.get("", response_model=schemas.ApiResponse[list[schemas.StockOHLCVResponse]])
def get_stock_ohlcvs(
    code: str,
    start_date: str = None,
    end_date: str = None,
    background_tasks: BackgroundTasks = None,
    db: Session = Depends(get_db),
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

    stock_name = (
        db.query(StockCache.stock_name).filter(StockCache.stock_code == code).scalar()
        or ""
    )
    return {"status": "success", "data": results, "stock_name": stock_name}


@router.get(
    "/{stock_code}/{trade_date}",
    response_model=schemas.ApiResponse[schemas.StockOHLCVResponse],
)
def get_stock_ohlcv(stock_code: str, trade_date: str, db: Session = Depends(get_db)):
    result = (
        db.query(StockOHLCVCache)
        .filter(
            StockOHLCVCache.stock_code == stock_code,
            StockOHLCVCache.trade_date == trade_date,
        )
        .first()
    )
    if not result:
        raise HTTPException(status_code=404, detail="OHLCV record not found")
    return {"status": "success", "data": result}


@router.post(
    "", status_code=201, response_model=schemas.ApiResponse[schemas.StockOHLCVResponse]
)
def create_stock_ohlcv(data: schemas.StockOHLCVCreate, db: Session = Depends(get_db)):
    existing = (
        db.query(StockOHLCVCache)
        .filter(
            StockOHLCVCache.stock_code == data.stock_code,
            StockOHLCVCache.trade_date == data.trade_date,
        )
        .first()
    )
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
        fluctuation_rate=data.fluctuation_rate,
    )
    db.add(new_record)
    db.commit()
    db.refresh(new_record)
    return {"status": "success", "data": new_record}


@router.put(
    "/{stock_code}/{trade_date}",
    response_model=schemas.ApiResponse[schemas.StockOHLCVResponse],
)
def update_stock_ohlcv(
    stock_code: str,
    trade_date: str,
    update_data: schemas.StockOHLCVUpdate,
    db: Session = Depends(get_db),
):
    record = (
        db.query(StockOHLCVCache)
        .filter(
            StockOHLCVCache.stock_code == stock_code,
            StockOHLCVCache.trade_date == trade_date,
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="OHLCV record not found")

    if update_data.open_price is not None:
        record.open_price = update_data.open_price
    if update_data.high_price is not None:
        record.high_price = update_data.high_price
    if update_data.low_price is not None:
        record.low_price = update_data.low_price
    if update_data.close_price is not None:
        record.close_price = update_data.close_price
    if update_data.volume is not None:
        record.volume = update_data.volume
    if update_data.trading_value is not None:
        record.trading_value = update_data.trading_value
    if update_data.fluctuation_rate is not None:
        record.fluctuation_rate = update_data.fluctuation_rate

    db.commit()
    db.refresh(record)
    return {"status": "success", "data": record}


@router.delete("/{stock_code}/{trade_date}")
def delete_stock_ohlcv(stock_code: str, trade_date: str, db: Session = Depends(get_db)):
    record = (
        db.query(StockOHLCVCache)
        .filter(
            StockOHLCVCache.stock_code == stock_code,
            StockOHLCVCache.trade_date == trade_date,
        )
        .first()
    )
    if not record:
        raise HTTPException(status_code=404, detail="OHLCV record not found")

    db.delete(record)
    return {"status": "success", "message": "OHLCV cache record deleted."}


@router.post("/current")
def refresh_current_ohlcv(db: Session = Depends(get_db)):
    stocks = db.query(Stock).filter(Stock.quantity > 0).all()
    if not stocks:
        return {"status": "success", "updated": []}

    unique_codes = list(set([s.stock_code for s in stocks]))
    updated = []

    today_str = datetime.now().strftime("%Y-%m-%d")

    try:
        dynamic_interval = 60000
        for code in unique_codes:
            url = (
                f"https://polling.finance.naver.com/api/realtime/domestic/stock/{code}"
            )
            response = requests.get(url, timeout=5)
            response.raise_for_status()
            data = response.json()

            dynamic_interval = data.get("pollingInterval", dynamic_interval)

            datas = data.get("datas", [])
            if not datas:
                continue

            item = datas[0]
            market_status = item.get("marketStatus", "OPEN")
            over_info = item.get("overMarketPriceInfo")

            # 방안 B: 시간외 거래 정보가 있고, 정규장이 마감된 상태라면 시간외 가격으로 덮어쓰기
            use_over_market = market_status == "CLOSE" and over_info is not None
            source = over_info if use_over_market else item
            price_key = "overPrice" if use_over_market else "closePrice"

            def parse_int(v):
                if not v:
                    return 0
                v_str = str(v).replace(",", "").strip()
                multiplier = 1
                if "백만" in v_str:
                    v_str = v_str.replace("백만", "").strip()
                    multiplier = 1000000
                elif "억" in v_str:
                    v_str = v_str.replace("억", "").strip()
                    multiplier = 100000000
                try:
                    return int(float(v_str) * multiplier)
                except ValueError:
                    return 0

            new_price = parse_int(source.get(price_key, item.get("closePrice", 0)))
            open_p = parse_int(source.get("openPrice", item.get("openPrice", 0)))
            high_p = parse_int(source.get("highPrice", item.get("highPrice", 0)))
            low_p = parse_int(source.get("lowPrice", item.get("lowPrice", 0)))
            vol = parse_int(
                source.get(
                    "accumulatedTradingVolume", item.get("accumulatedTradingVolume", 0)
                )
            )
            val = parse_int(
                source.get(
                    "accumulatedTradingValue", item.get("accumulatedTradingValue", 0)
                )
            )

            fl_rate_str = str(
                source.get("fluctuationsRatio", item.get("fluctuationsRatio", 0.0))
            ).replace(",", "")
            fl_rate = float(fl_rate_str)

            for stock in stocks:
                if stock.stock_code == code:
                    if stock.current_price != new_price:
                        stock.current_price = new_price
                        updated.append({"stock_code": code, "new_price": new_price})

            ohlcv = (
                db.query(StockOHLCVCache)
                .filter(
                    StockOHLCVCache.stock_code == code,
                    StockOHLCVCache.trade_date == today_str,
                )
                .first()
            )

            if ohlcv:
                ohlcv.open_price = open_p
                ohlcv.high_price = high_p
                ohlcv.low_price = low_p
                ohlcv.close_price = new_price
                ohlcv.volume = vol
                ohlcv.trading_value = val
                ohlcv.fluctuation_rate = fl_rate
            else:
                new_ohlcv = StockOHLCVCache(
                    stock_code=code,
                    trade_date=today_str,
                    open_price=open_p,
                    high_price=high_p,
                    low_price=low_p,
                    close_price=new_price,
                    volume=vol,
                    trading_value=val,
                    fluctuation_rate=fl_rate,
                )
                db.add(new_ohlcv)

        db.commit()
        return {
            "status": "success",
            "polling_interval": dynamic_interval,
            "updated": updated,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to fetch realtime prices: {str(e)}"
        )

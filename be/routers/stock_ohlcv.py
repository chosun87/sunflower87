from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy.orm import Session

import config
import schemas
from database import Stock, StockCache, StockOHLCVCurrent, StockOHLCVDaily, get_db
from services.market_service import (
    fetch_and_fill_ohlcv_gap,
    get_exact_trade_dates,
    sync_current_ohlcv,
    sync_owned_stocks_gap,
)

router = APIRouter(prefix="/api/stock_ohlcvs", tags=["StockOHLCV"])


@router.post("/sync/owned")
def sync_owned_stocks(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    stocks = db.query(Stock).filter(Stock.quantity > 0).all()
    if stocks:
        background_tasks.add_task(
            sync_owned_stocks_gap, db, stocks, config.DATA_GAP_THRESHOLD
        )
    return {"status": "success", "message": "Background sync started for owned stocks."}


@router.get("", response_model=schemas.ApiResponse[list[schemas.StockOHLCVResponse]])
def get_stock_ohlcvs(
    code: str,
    limit: int = Query(config.DATA_GAP_THRESHOLD, description="불러올 영업일 수"),
    before_date: str = Query(
        None, description="이 날짜 이전의 데이터를 불러옴 (YYYY-MM-DD)"
    ),
    db: Session = Depends(get_db),
):
    today_str = datetime.now().strftime("%Y-%m-%d")

    # 1. 계산을 위한 기준일 설정
    if before_date:
        ref_date_str = before_date.replace("-", "")
    else:
        ref_date_str = today_str.replace("-", "")

    # 2. 정확한 개장일 캘린더 추출
    exact_dates = get_exact_trade_dates(ref_date_str, limit)
    if not exact_dates:
        raise HTTPException(status_code=404, detail="Market calendar not available.")

    target_start_str = exact_dates[0]
    target_end_str = exact_dates[-1]

    # DB 조회용 포맷 변환
    target_start_db = (
        f"{target_start_str[:4]}-{target_start_str[4:6]}-{target_start_str[6:]}"
    )
    target_end_db = f"{target_end_str[:4]}-{target_end_str[4:6]}-{target_end_str[6:]}"

    # 3. DB 조회
    query = db.query(StockOHLCVDaily).filter(StockOHLCVDaily.stock_code == code)
    query = query.filter(StockOHLCVDaily.trade_date >= target_start_db)
    query = query.filter(StockOHLCVDaily.trade_date <= target_end_db)
    daily_results = query.order_by(StockOHLCVDaily.trade_date.asc()).all()

    # 4. 누락된 데이터 확인 및 Fetch
    if len(daily_results) < len(exact_dates):
        # 데이터가 모자라다면 해당 기간 갭 필링
        fetch_and_fill_ohlcv_gap(db, code, target_start_str, target_end_str)
        # 다시 조회
        daily_results = query.order_by(StockOHLCVDaily.trade_date.asc()).all()

    results_list = list(daily_results)

    # 5. 오늘 날짜인 경우 current_data 병합 (차트 진입 시)
    if not before_date or before_date >= today_str:
        current_data = (
            db.query(StockOHLCVCurrent)
            .filter(
                StockOHLCVCurrent.stock_code == code,
                StockOHLCVCurrent.trade_date == today_str,
            )
            .first()
        )

        if current_data:
            if not any(r.trade_date == today_str for r in results_list):
                mapped_current = schemas.StockOHLCVResponse(
                    stock_code=current_data.stock_code,
                    trade_date=current_data.trade_date,
                    open_price=current_data.open_price,
                    high_price=current_data.high_price,
                    low_price=current_data.low_price,
                    close_price=current_data.close_price,
                    volume=current_data.volume,
                    trading_value=0,
                    fluctuation_rate=current_data.change_rate,
                    change_price=current_data.change_value,
                    change_price_code=current_data.change_price_code,
                )
                results_list.append(mapped_current)

    stock_name = (
        db.query(StockCache.stock_name).filter(StockCache.stock_code == code).scalar()
        or ""
    )
    return {"status": "success", "data": results_list, "stock_name": stock_name}


@router.get(
    "/{stock_code}/{trade_date}",
    response_model=schemas.ApiResponse[schemas.StockOHLCVResponse],
)
def get_stock_ohlcv(stock_code: str, trade_date: str, db: Session = Depends(get_db)):
    result = (
        db.query(StockOHLCVDaily)
        .filter(
            StockOHLCVDaily.stock_code == stock_code,
            StockOHLCVDaily.trade_date == trade_date,
        )
        .first()
    )

    if not result:
        # fallback to current if trade_date is today
        today_str = datetime.now().strftime("%Y-%m-%d")
        if trade_date == today_str:
            curr = (
                db.query(StockOHLCVCurrent)
                .filter(
                    StockOHLCVCurrent.stock_code == stock_code,
                    StockOHLCVCurrent.trade_date == today_str,
                )
                .first()
            )
            if curr:
                mapped_current = schemas.StockOHLCVResponse(
                    stock_code=curr.stock_code,
                    trade_date=curr.trade_date,
                    open_price=curr.open_price,
                    high_price=curr.high_price,
                    low_price=curr.low_price,
                    close_price=curr.close_price,
                    volume=curr.volume,
                    trading_value=0,
                    fluctuation_rate=curr.change_rate,
                    change_price=curr.change_value,
                    change_price_code=curr.change_price_code,
                )
                return {"status": "success", "data": mapped_current}

        raise HTTPException(status_code=404, detail="OHLCV record not found")

    return {"status": "success", "data": result}


@router.post(
    "", status_code=201, response_model=schemas.ApiResponse[schemas.StockOHLCVResponse]
)
def create_stock_ohlcv(data: schemas.StockOHLCVCreate, db: Session = Depends(get_db)):
    existing = (
        db.query(StockOHLCVDaily)
        .filter(
            StockOHLCVDaily.stock_code == data.stock_code,
            StockOHLCVDaily.trade_date == data.trade_date,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=400, detail="OHLCV record already exists")

    new_record = StockOHLCVDaily(
        stock_code=data.stock_code,
        trade_date=data.trade_date,
        open_price=data.open_price,
        high_price=data.high_price,
        low_price=data.low_price,
        close_price=data.close_price,
        volume=data.volume,
        trading_value=data.trading_value,
        fluctuation_rate=data.fluctuation_rate,
        change_price=data.change_price,
        change_price_code=data.change_price_code,
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
        db.query(StockOHLCVDaily)
        .filter(
            StockOHLCVDaily.stock_code == stock_code,
            StockOHLCVDaily.trade_date == trade_date,
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
        db.query(StockOHLCVDaily)
        .filter(
            StockOHLCVDaily.stock_code == stock_code,
            StockOHLCVDaily.trade_date == trade_date,
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

    try:
        res = sync_current_ohlcv(db, stocks)
        return {
            "status": "success",
            "polling_interval": res["polling_interval"],
            "updated": res["updated"],
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

from datetime import datetime, timedelta

import pandas as pd
from sqlalchemy.orm import Session

import config
from clients.krx_client import fetch_market_ohlcv_by_date, get_exact_trade_dates
from clients.naver_client import fetch_realtime_price
from constants import ChangePriceCode
from database import StockOHLCVCurrent, StockOHLCVDaily, db_write_lock


def _save_ohlcv_to_db(db: Session, stock_code: str, df):
    if df is None or df.empty:
        return

    col_open = next((c for c in df.columns if "시가" in str(c)), "시가")
    col_high = next((c for c in df.columns if "고가" in str(c)), "고가")
    col_low = next((c for c in df.columns if "저가" in str(c)), "저가")
    col_close = next((c for c in df.columns if "종가" in str(c)), "종가")
    col_volume = next((c for c in df.columns if "거래량" in str(c)), "거래량")
    col_trading_value = next(
        (c for c in df.columns if "거래대금" in str(c)), "거래대금"
    )
    col_fluctuation = next((c for c in df.columns if "등락률" in str(c)), "등락률")

    now = datetime.utcnow().isoformat()

    for idx, row in df.iterrows():
        trade_date = idx.strftime("%Y-%m-%d")
        f_rate = float(
            row.get(col_fluctuation, 0.0)
            if pd.notna(row.get(col_fluctuation, 0.0))
            else 0.0
        )

        if f_rate > 0:
            c_p_code = (
                ChangePriceCode.상한.value
                if f_rate >= 29.5
                else ChangePriceCode.상승.value
            )
        elif f_rate < 0:
            c_p_code = (
                ChangePriceCode.하한.value
                if f_rate <= -29.5
                else ChangePriceCode.하락.value
            )
        else:
            c_p_code = ChangePriceCode.보합.value

        ohlcv = StockOHLCVDaily(
            stock_code=stock_code,
            trade_date=trade_date,
            open_price=int(
                row.get(col_open, 0) if pd.notna(row.get(col_open, 0)) else 0
            ),
            high_price=int(
                row.get(col_high, 0) if pd.notna(row.get(col_high, 0)) else 0
            ),
            low_price=int(row.get(col_low, 0) if pd.notna(row.get(col_low, 0)) else 0),
            close_price=int(
                row.get(col_close, 0) if pd.notna(row.get(col_close, 0)) else 0
            ),
            volume=int(
                row.get(col_volume, 0) if pd.notna(row.get(col_volume, 0)) else 0
            ),
            trading_value=int(
                row.get(col_trading_value, 0)
                if pd.notna(row.get(col_trading_value, 0))
                else 0
            ),
            fluctuation_rate=f_rate,
            change_price=0,
            change_price_code=c_p_code,
            dt_updated=now,
        )
        db.merge(ohlcv)
    db.commit()


def fetch_and_fill_ohlcv_gap(
    db: Session, stock_code: str, start_date_str: str, end_date_str: str
):
    """지정된 기간 동안의 pykrx 데이터를 가져와 DB에 채웁니다."""
    try:
        df = fetch_market_ohlcv_by_date(start_date_str, end_date_str, stock_code)
        if df is not None and not df.empty:
            _save_ohlcv_to_db(db, stock_code, df)
    except Exception as e:
        print(
            f"[ERROR] Failed to fetch gap for {stock_code} ({start_date_str}~{end_date_str}): {e}"
        )


def sync_owned_stocks_gap(
    db: Session, stocks: list, target_days: int = config.DATA_GAP_THRESHOLD
):
    """
    로그인 시 등에 호출되어, 보유 중인 종목들에 대해 과거 N일간의 갭을 채웁니다.
    """
    if not stocks:
        return

    today_str = datetime.now().strftime("%Y%m%d")
    exact_dates = get_exact_trade_dates(today_str, target_days)
    if not exact_dates:
        return

    target_start_str = exact_dates[0]
    target_end_str = exact_dates[-1]

    unique_codes = list(set([s.stock_code for s in stocks]))

    for code in unique_codes:
        first_cache = (
            db.query(StockOHLCVDaily)
            .filter(StockOHLCVDaily.stock_code == code)
            .order_by(StockOHLCVDaily.trade_date.asc())
            .first()
        )
        last_cache = (
            db.query(StockOHLCVDaily)
            .filter(StockOHLCVDaily.stock_code == code)
            .order_by(StockOHLCVDaily.trade_date.desc())
            .first()
        )

        if not first_cache or not last_cache:
            fetch_and_fill_ohlcv_gap(db, code, target_start_str, target_end_str)
            continue

        first_db_str = first_cache.trade_date.replace("-", "")
        last_db_str = last_cache.trade_date.replace("-", "")

        # 1. 과거 갭 채우기
        if first_db_str > target_start_str:
            gap_end_obj = datetime.strptime(first_db_str, "%Y%m%d") - timedelta(days=1)
            gap_end_str = gap_end_obj.strftime("%Y%m%d")
            if gap_end_str >= target_start_str:
                fetch_and_fill_ohlcv_gap(db, code, target_start_str, gap_end_str)

        # 2. 미래(최근) 갭 채우기
        if last_db_str < target_end_str:
            gap_start_obj = datetime.strptime(last_db_str, "%Y%m%d") + timedelta(days=1)
            gap_start_str = gap_start_obj.strftime("%Y%m%d")
            if gap_start_str <= target_end_str:
                fetch_and_fill_ohlcv_gap(db, code, gap_start_str, target_end_str)


def _upsert_stock_ohlcv_current(db: Session, code: str, today_str: str, fields: dict):
    current_ohlcv = (
        db.query(StockOHLCVCurrent)
        .filter(
            StockOHLCVCurrent.stock_code == code,
            StockOHLCVCurrent.trade_date == today_str,
        )
        .first()
    )

    now = datetime.utcnow().isoformat()
    if current_ohlcv:
        for k, v in fields.items():
            setattr(current_ohlcv, k, v)
        current_ohlcv.dt_updated = now
    else:
        new_current = StockOHLCVCurrent(
            stock_code=code, trade_date=today_str, dt_updated=now, **fields
        )
        db.add(new_current)


def sync_current_ohlcv(db: Session, stocks: list) -> dict:
    if not stocks:
        return {"polling_interval": 60000, "updated": []}

    unique_codes = list(set([s.stock_code for s in stocks]))
    updated = []
    today_str = datetime.now().strftime("%Y-%m-%d")
    dynamic_interval = 60000

    with db_write_lock:
        try:
            for code in unique_codes:
                data = fetch_realtime_price(code)
                dynamic_interval = data.get("polling_interval", dynamic_interval)
                fields = data.get("fields")

                if not fields:
                    continue

                new_price = fields["close_price"]

                for stock in stocks:
                    if stock.stock_code == code:
                        if stock.current_price != new_price:
                            stock.current_price = new_price
                            updated.append({"stock_code": code, "new_price": new_price})

                _upsert_stock_ohlcv_current(db, code, today_str, fields)

            db.commit()
            return {
                "polling_interval": dynamic_interval,
                "updated": updated,
            }
        except Exception as e:
            db.rollback()
            raise Exception(f"Failed to fetch realtime prices: {str(e)}")

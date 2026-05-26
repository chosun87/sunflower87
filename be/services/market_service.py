from datetime import datetime, timedelta

from sqlalchemy.orm import Session

from config import DATA_GAP_THRESHOLD, TRADE_DATE_PERIOD
from database import StockOHLCVCache


def get_exact_trade_date_limits(target_period=60):
    now = datetime.today()
    current_hour = now.hour

    if current_hour >= 16:
        target_end_str = now.strftime("%Y%m%d")
    else:
        target_end_str = (now - timedelta(days=1)).strftime("%Y%m%d")

    safe_start_str = (now - timedelta(days=120)).strftime("%Y%m%d")
    actual_trade_dates = []

    try:
        from pykrx import stock as krx_stock

        df_market = krx_stock.get_market_ohlcv_by_date(
            safe_start_str, target_end_str, "KOSPI"
        )
        if df_market is None or df_market.empty:
            raise ValueError("Empty df")
        actual_trade_dates = df_market.index.strftime("%Y%m%d").tolist()
    except Exception:
        try:
            df_market = krx_stock.get_market_ohlcv_by_date(
                safe_start_str, target_end_str, "005930"
            )
            if df_market is not None and not df_market.empty:
                actual_trade_dates = df_market.index.strftime("%Y%m%d").tolist()
        except Exception as e:
            print(f"[WARNING] Failed to fetch market limits: {e}")

    if actual_trade_dates:
        valid_dates = actual_trade_dates[-target_period:]
        if valid_dates:
            return valid_dates[0], valid_dates[-1]

    safe_fallback_start = (now - timedelta(days=int(target_period * 1.5))).strftime(
        "%Y%m%d"
    )
    return safe_fallback_start, target_end_str


def get_market_trade_dates(start_date_str: str, end_date_str: str) -> list:
    try:
        from pykrx import stock as krx_stock

        df_market = krx_stock.get_market_ohlcv_by_date(
            start_date_str, end_date_str, "005930"
        )
        if df_market is not None and not df_market.empty:
            return df_market.index.strftime("%Y%m%d").tolist()
    except Exception as e:
        print(f"[WARNING] Failed to fetch market calendar dates: {e}")
    return []


def _save_ohlcv_to_db(db: Session, stock_code: str, df):
    if df is None or df.empty:
        return

    has_trading_value = "거래대금" in df.columns
    has_fluctuation = "등락률" in df.columns

    for date, row in df.iterrows():
        trade_date = date.strftime("%Y-%m-%d")
        existing = (
            db.query(StockOHLCVCache)
            .filter(
                StockOHLCVCache.stock_code == stock_code,
                StockOHLCVCache.trade_date == trade_date,
            )
            .first()
        )

        if not existing:
            cache_entry = StockOHLCVCache(
                stock_code=stock_code,
                trade_date=trade_date,
                open_price=int(row.get("시가", 0)),
                high_price=int(row.get("고가", 0)),
                low_price=int(row.get("저가", 0)),
                close_price=int(row.get("종가", 0)),
                volume=int(row.get("거래량", 0)),
                trading_value=int(row.get("거래대금", 0)) if has_trading_value else 0,
                fluctuation_rate=(
                    float(row.get("등락률", 0.0)) if has_fluctuation else 0.0
                ),
            )
            db.add(cache_entry)
    db.commit()


def _fetch_and_save_initial_ohlcv(db: Session, stock_code: str):
    start_str, end_str = get_exact_trade_date_limits(TRADE_DATE_PERIOD)
    from pykrx import stock as krx_stock

    df = krx_stock.get_market_ohlcv_by_date(start_str, end_str, stock_code)
    if df is not None and not df.empty:
        _save_ohlcv_to_db(db, stock_code, df)


def sync_ohlcv_cache(
    db: Session, stock_code: str, start_date: str = None, end_date: str = None
):
    today = datetime.now()
    current_hour = today.hour

    if not end_date:
        if current_hour >= 16:
            target_end_str = today.strftime("%Y%m%d")
        else:
            target_end_str = (today - timedelta(days=1)).strftime("%Y%m%d")
    else:
        target_end_str = end_date.replace("-", "")

    try:
        last_cache = (
            db.query(StockOHLCVCache)
            .filter(StockOHLCVCache.stock_code == stock_code)
            .order_by(StockOHLCVCache.trade_date.desc())
            .first()
        )
        first_cache = (
            db.query(StockOHLCVCache)
            .filter(StockOHLCVCache.stock_code == stock_code)
            .order_by(StockOHLCVCache.trade_date.asc())
            .first()
        )

        if not last_cache or not first_cache:
            if start_date:
                req_start_obj = datetime.strptime(start_date.replace("-", ""), "%Y%m%d")
                safe_start_str = (req_start_obj - timedelta(days=120)).strftime(
                    "%Y%m%d"
                )
                from pykrx import stock as krx_stock

                df_init = krx_stock.get_market_ohlcv_by_date(
                    safe_start_str, target_end_str, stock_code
                )
                if df_init is not None and not df_init.empty:
                    _save_ohlcv_to_db(db, stock_code, df_init)
            else:
                _fetch_and_save_initial_ohlcv(db, stock_code)
            return

        last_date_str = last_cache.trade_date.replace("-", "")
        first_date_str = first_cache.trade_date.replace("-", "")

        if start_date:
            req_start_str = start_date.replace("-", "")
            req_start_obj = datetime.strptime(req_start_str, "%Y%m%d")
            safe_start_str = (req_start_obj - timedelta(days=120)).strftime("%Y%m%d")

            if safe_start_str < first_date_str:
                from pykrx import stock as krx_stock

                h_end_obj = datetime.strptime(first_date_str, "%Y%m%d") - timedelta(
                    days=1
                )
                h_end_str = h_end_obj.strftime("%Y%m%d")
                if safe_start_str <= h_end_str:
                    df_hist = krx_stock.get_market_ohlcv_by_date(
                        safe_start_str, h_end_str, stock_code
                    )
                    if df_hist is not None and not df_hist.empty:
                        _save_ohlcv_to_db(db, stock_code, df_hist)

        if last_date_str < target_end_str:
            trade_dates = get_market_trade_dates(last_date_str, target_end_str)
            gap_trade_days = len([d for d in trade_dates if d > last_date_str])

            if 0 < gap_trade_days <= DATA_GAP_THRESHOLD:
                last_date_obj = datetime.strptime(last_date_str, "%Y%m%d")
                m_start_str = (last_date_obj + timedelta(days=1)).strftime("%Y%m%d")
                if m_start_str <= target_end_str:
                    from pykrx import stock as krx_stock

                    df_gap = krx_stock.get_market_ohlcv_by_date(
                        m_start_str, target_end_str, stock_code
                    )
                    if df_gap is not None and not df_gap.empty:
                        _save_ohlcv_to_db(db, stock_code, df_gap)
            elif gap_trade_days > DATA_GAP_THRESHOLD:
                db.query(StockOHLCVCache).filter(
                    StockOHLCVCache.stock_code == stock_code
                ).delete()
                db.commit()
                if start_date:
                    req_start_obj = datetime.strptime(
                        start_date.replace("-", ""), "%Y%m%d"
                    )
                    safe_start_str = (req_start_obj - timedelta(days=120)).strftime(
                        "%Y%m%d"
                    )
                    from pykrx import stock as krx_stock

                    df_init = krx_stock.get_market_ohlcv_by_date(
                        safe_start_str, target_end_str, stock_code
                    )
                    if df_init is not None and not df_init.empty:
                        _save_ohlcv_to_db(db, stock_code, df_init)
                else:
                    _fetch_and_save_initial_ohlcv(db, stock_code)

    except Exception as e:
        print(f"[ERROR] Failed to sync OHLCV cache for {stock_code}: {e}")

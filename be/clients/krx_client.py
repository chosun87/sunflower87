from datetime import datetime, timedelta

from pykrx import stock as krx_stock


def get_exact_trade_dates(end_date_str: str, target_days: int) -> list:
    """
    특정 종료일 기준으로 정확히 target_days 만큼의 과거 개장일 목록을 반환합니다.
    """
    if target_days <= 0:
        return []

    # 넉넉한 바운딩 박스로 KOSPI 지수 캘린더를 호출 (휴장일 고려하여 대략 * 2)
    end_date_obj = datetime.strptime(end_date_str, "%Y%m%d")
    safe_start = (end_date_obj - timedelta(days=target_days * 2 + 10)).strftime(
        "%Y%m%d"
    )

    # 삼성전자(005930)가 실제로 거래된 날짜(=개장일)만 가져옴
    df_market = krx_stock.get_market_ohlcv_by_date(safe_start, end_date_str, "005930")

    if df_market is not None and not df_market.empty:
        valid_dates = df_market.index.strftime("%Y%m%d").tolist()
        return valid_dates[-target_days:]
    return []


def fetch_market_ohlcv_by_date(start_date_str: str, end_date_str: str, stock_code: str):
    """지정된 기간 동안의 pykrx 데이터를 반환합니다."""
    return krx_stock.get_market_ohlcv_by_date(start_date_str, end_date_str, stock_code)


def fetch_market_ohlcv_single_date(target_date_str: str, stock_code: str):
    """
    특정 일자의 pykrx 데이터를 반환합니다. (단일 일자)
    """
    # account_balance_daily_service.py 호환성용 메서드
    return krx_stock.get_market_ohlcv(target_date_str, target_date_str, stock_code)

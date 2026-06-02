import requests


def _parse_naver_int(v):
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


def _extract_naver_realtime_fields(item: dict) -> dict:
    market_status = item.get("marketStatus", "OPEN")
    over_info = item.get("overMarketPriceInfo")
    use_over_market = market_status == "CLOSE" and over_info is not None
    source = over_info if use_over_market else item

    if market_status == "OPEN":
        open_p = _parse_naver_int(item.get("openPriceRaw", item.get("openPrice", 0)))
        high_p = _parse_naver_int(item.get("highPriceRaw", item.get("highPrice", 0)))
        low_p = _parse_naver_int(item.get("lowPriceRaw", item.get("lowPrice", 0)))
        close_p = _parse_naver_int(item.get("closePriceRaw", item.get("closePrice", 0)))
        vol = _parse_naver_int(
            item.get(
                "accumulatedTradingVolumeRaw", item.get("accumulatedTradingVolume", 0)
            )
        )

        cr_str = str(
            item.get("fluctuationsRatioRaw", item.get("fluctuationsRatio", 0.0))
        ).replace(",", "")
        cv_str = str(
            item.get(
                "compareToPreviousClosePriceRaw",
                item.get("compareToPreviousClosePrice", 0),
            )
        ).replace(",", "")
        compare_code = str(item.get("compareToPreviousPrice", {}).get("code", "3"))
    else:
        price_key = "overPrice" if use_over_market else "closePrice"
        close_p = _parse_naver_int(source.get(price_key, item.get("closePrice", 0)))
        open_p = _parse_naver_int(source.get("openPrice", item.get("openPrice", 0)))
        high_p = _parse_naver_int(source.get("highPrice", item.get("highPrice", 0)))
        low_p = _parse_naver_int(source.get("lowPrice", item.get("lowPrice", 0)))
        vol = _parse_naver_int(
            source.get(
                "accumulatedTradingVolume", item.get("accumulatedTradingVolume", 0)
            )
        )
        cr_str = str(
            source.get("fluctuationsRatio", item.get("fluctuationsRatio", 0.0))
        ).replace(",", "")
        cv_str = str(
            source.get(
                "compareToPreviousClosePrice",
                item.get("compareToPreviousClosePrice", 0),
            )
        ).replace(",", "")
        compare_code = str(
            source.get(
                "compareToPreviousPrice", item.get("compareToPreviousPrice", {})
            ).get("code", "3")
        )

    c_rate = float(cr_str)
    c_val = int(float(cv_str))

    if compare_code in ["4", "5"]:
        c_rate = -abs(c_rate)
        c_val = -abs(c_val)

    return {
        "open_price": open_p,
        "high_price": high_p,
        "low_price": low_p,
        "close_price": close_p,
        "volume": vol,
        "change_rate": c_rate,
        "change_value": c_val,
        "change_price_code": compare_code,
    }


def fetch_realtime_price(stock_code: str) -> dict:
    """
    네이버 금융 실시간 주가 API를 호출하여 정제된 딕셔너리를 반환합니다.
    """
    url = f"https://polling.finance.naver.com/api/realtime/domestic/stock/{stock_code}"
    response = requests.get(url, timeout=5)
    response.raise_for_status()
    data = response.json()

    interval = data.get("pollingInterval", 60000)
    datas = data.get("datas", [])
    if not datas:
        return {"polling_interval": interval, "fields": None}

    fields = _extract_naver_realtime_fields(datas[0])
    return {"polling_interval": interval, "fields": fields}

# 답변 초안 작성용
이유:
1. `account_balance_daily_service.py` 132라인 쯤에서 하드코딩 되어 있음.
2. PyKRX `get_market_ohlcv_by_date` 메서드가 단일 종목의 기간 검색 시 '거래대금' 열을 반환하지 않음.

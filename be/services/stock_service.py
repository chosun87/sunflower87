# be/services/stock_service.py - 온디맨드 주가 동기화 개정안
from sqlalchemy.orm import Session

from database import SessionLocal, StockOHLCVCache
from portfolio_service import sync_ohlcv_cache


def get_or_fetch_ohlcv(stock_code: str, db: Session = None):
    """
    [Lazy Loading Architecture]
    사용자가 요청한(보유 중이거나 차트를 켠) 종목만
    선택적으로 캐시를 확인하고 스크래핑을 가동한다.
    """
    created_session = False
    if db is None:
        db = SessionLocal()
        created_session = True

    try:
        # 1. 로컬 DB 캐시에서 해당 종목 데이터가 이미 존재하는지 먼저 확인 (Cache Aside)
        #    사용자가 차트 상세 페이지를 열어본 종목에 한해서만 stock_ohlcv_cache 테이블에 행이 점진적으로 쌓입니다.
        local_cache = (
            db.query(StockOHLCVCache)
            .filter(StockOHLCVCache.stock_code == stock_code)
            .order_by(StockOHLCVCache.trade_date.desc())
            .limit(80)
            .all()
        )

        # 2. 캐시 미스(Cache Miss)이거나 16시 타임윈도우 기준 데이터 갭(Gap)이 발견된 경우에만
        #    '해당 종목 딱 하나만' 선택적으로 pykrx 외부 동기화를 가동 (Cache Fill)
        #    한 번 적재된 종목은 16시 장마감 타임윈도우 가드에 의해 당일 데이터가 무결하게 리프레시됩니다.
        if not local_cache:
            print(
                f"[sunflower87] [Lazy Loading] Cache Miss for {stock_code}. "
                "Triggering sync..."
            )
            sync_ohlcv_cache(db, stock_code)

            # 싱크 후 다시 조회
            local_cache = (
                db.query(StockOHLCVCache)
                .filter(StockOHLCVCache.stock_code == stock_code)
                .order_by(StockOHLCVCache.trade_date.desc())
                .limit(80)
                .all()
            )
        else:
            # 16시 마감 여부에 따라 오늘 자 최신 데이터 공백 확인 후 증분 백필 가동
            from datetime import datetime, timedelta

            today = datetime.now()
            current_hour = today.hour

            if current_hour >= 16:
                target_date_str = today.strftime("%Y%m%d")
            else:
                target_date_str = (today - timedelta(days=1)).strftime("%Y%m%d")

            last_cached_date = local_cache[0].trade_date

            # 주말이 아닌데 캐시 최종일이 타겟 최종일보다 이전인 경우 (Data Gap 발견)
            # KOSPI 캘린더나 장마감 기준 세부 동기화 로직 가동
            if last_cached_date < target_date_str:
                print(
                    f"[sunflower87] [Lazy Loading] Gap detected "
                    f"({last_cached_date} < {target_date_str}) for "
                    f"{stock_code}. Syncing..."
                )
                sync_ohlcv_cache(db, stock_code)

                local_cache = (
                    db.query(StockOHLCVCache)
                    .filter(StockOHLCVCache.stock_code == stock_code)
                    .order_by(StockOHLCVCache.trade_date.desc())
                    .limit(80)
                    .all()
                )

        # 3. 데이터베이스 레이어에서 정렬(ORDER BY trade_date ASC)된 데이터를 최종 반환
        local_cache_sorted = sorted(local_cache, key=lambda x: x.trade_date)
        return local_cache_sorted

    finally:
        if created_session:
            db.close()

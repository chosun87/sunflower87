import os
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from pykrx import stock as krx_stock

from database import CacheStock

def sync_cache_stocks(db: Session):
    print("[sunflower87] Launching super-fast KRX Stock Master seeding...")
    now = datetime.today()
    masters_seeded = False

    # 네트워크 상태를 고려하여 최근 7일 내의 실제 영업일 탐색
    for i in range(7):
        date_str = (now - timedelta(days=i)).strftime("%Y%m%d")
        try:
            df_kospi = krx_stock.get_market_price_change_by_ticker(
                date_str, date_str, "KOSPI"
            )
            df_kosdaq = krx_stock.get_market_price_change_by_ticker(
                date_str, date_str, "KOSDAQ"
            )

            # 동적으로 실제 존재하는 전체 ETF 티커 리스트 획득
            try:
                etf_tickers = krx_stock.get_etf_ticker_list(date_str)
            except Exception:
                etf_tickers = []

            if (
                df_kospi is not None
                and not df_kospi.empty
                and df_kosdaq is not None
                and not df_kosdaq.empty
            ):
                active_tickers = set()

                # KOSPI 수집적재
                for ticker, row in df_kospi.iterrows():
                    active_tickers.add(ticker)
                    name = row["종목명"]
                    existing = (
                        db.query(CacheStock)
                        .filter(CacheStock.stock_code == ticker)
                        .first()
                    )
                    market_type = "ETF" if ticker in etf_tickers else "KOSPI"
                    if not existing:
                        db.add(CacheStock(stock_code=ticker, stock_name=name, market=market_type, is_active=1))
                    elif existing.market is None:
                        existing.market = market_type

                # KOSDAQ 수집적재
                for ticker, row in df_kosdaq.iterrows():
                    active_tickers.add(ticker)
                    name = row["종목명"]
                    existing = (
                        db.query(CacheStock)
                        .filter(CacheStock.stock_code == ticker)
                        .first()
                    )
                    market_type = "ETF" if ticker in etf_tickers else "KOSDAQ"
                    if not existing:
                        db.add(CacheStock(stock_code=ticker, stock_name=name, market=market_type, is_active=1))
                    elif existing.market is None:
                        existing.market = market_type

                # 순수 ETF 목록 추가 수집적재
                for ticker in etf_tickers:
                    active_tickers.add(ticker)
                    existing = (
                        db.query(CacheStock)
                        .filter(CacheStock.stock_code == ticker)
                        .first()
                    )
                    if not existing:
                        try:
                            name = krx_stock.get_etf_ticker_name(ticker)
                            if name:
                                db.add(CacheStock(stock_code=ticker, stock_name=name, market="ETF", is_active=1))
                        except Exception as name_err:
                            print(f"Failed to fetch ETF name for {ticker}: {name_err}")
                    elif existing.market is None:
                        existing.market = "ETF"

                # ETF 및 기타 오프라인 사전 주요 종목 결합 보충
                from routers.stocks import get_offline_stocks
                offline_master = get_offline_stocks()

                etf_keywords = ["KODEX", "TIGER", "ACE", "SOL", "RISE", "KOSEF", "HANARO", "KBSTAR", "ARIRANG"]

                for code, name in offline_master.items():
                    active_tickers.add(code)
                    existing = (
                        db.query(CacheStock)
                        .filter(CacheStock.stock_code == code)
                        .first()
                    )
                    market_type = "KOSPI"
                    if code in etf_tickers or any(kw in name.upper() for kw in etf_keywords):
                        market_type = "ETF"
                    if not existing:
                        db.add(CacheStock(stock_code=code, stock_name=name, market=market_type, is_active=1))
                    elif existing.market is None:
                        existing.market = market_type

                # [Diff & Soft Delete 로직]
                db_active_stocks = db.query(CacheStock).filter(CacheStock.is_active == 1).all()
                for s in db_active_stocks:
                    if s.stock_code not in active_tickers:
                        s.is_active = 0
                        print(f"[sunflower87] Soft-deleted inactive stock: {s.stock_code} ({s.stock_name})")

                db.commit()
                print(f"[sunflower87] Successfully seeded complete KRX stock masters based on trade date {date_str}!")
                masters_seeded = True
                break
        except Exception as day_err:
            db.rollback()
            print(f"[WARNING] Seeding attempt for {date_str} skipped: {day_err}")
            continue

    # [Fail-safe Fallback Guard] 네트워크 장애 발생 시 오프라인 백업 사전 시딩 기동
    if not masters_seeded:
        print("[WARNING] KRX Online seeding failed. Activating offline backup dictionary seeding...")
        from routers.stocks import get_offline_stocks
        offline_master = get_offline_stocks()

        etf_keywords = ["KODEX", "TIGER", "ACE", "SOL", "RISE", "KOSEF", "HANARO", "KBSTAR", "ARIRANG"]

        for code, name in offline_master.items():
            market_type = "KOSPI"
            if any(kw in name.upper() for kw in etf_keywords):
                market_type = "ETF"
            elif code.startswith("2") or code.startswith("3") or code.startswith("4"):
                market_type = "KOSDAQ"

            existing_stock = db.query(CacheStock).filter(CacheStock.stock_code == code).first()
            if not existing_stock:
                db.add(CacheStock(stock_code=code, stock_name=name, market=market_type, is_active=1))
            elif existing_stock.market is None:
                existing_stock.market = market_type
        db.commit()
        print("[sunflower87] Offline fallback stock masters successfully seeded.")
        
    return {"status": "success", "message": "종목 마스터 수집이 완료되었습니다."}

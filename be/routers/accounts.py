from fastapi import APIRouter, Depends, BackgroundTasks
from sqlalchemy.orm import Session
from database import get_db
from portfolio_service import get_enriched_accounts_data

router = APIRouter(prefix="/api/accounts", tags=["Account"])


def sync_portfolio_prices_background(db_session_factory, stock_codes):
    """보유 주식들의 시세 캐시를 백그라운드에서 비동기로 안전하게 동기화합니다."""
    db = db_session_factory()
    try:
        from portfolio_service import sync_ohlcv_cache
        for code in stock_codes:
            sync_ohlcv_cache(db, code)
        print(f"Background task: Successfully synced prices for {len(stock_codes)} stocks.")
    except Exception as e:
        print(f"Background task failed: {e}")
    finally:
        db.close()


@router.get(
    "",
    summary="총자산 및 계좌별 세부 자산 현황 조회 API",
    description=(
        "SQLite 데이터베이스의 account 및 stocks 테이블을 통합 조회하여 "
        "총 자산 평가액, 계좌별 예수금, 주식 보유 내역 및 실시간 평가 수익률을 동적으로 계산해 반환합니다. "
        "시세 캐시 업데이트는 백그라운드에서 비동기로 처리되므로 즉각적인 초고속 응답을 보장합니다."
    ),
)
def get_miraeasset_accounts(background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """SQLite 데이터베이스 account 및 stocks 테이블을 기반으로 총자산 및 계좌별 세부 자산 현황을 반환합니다."""
    # 1. 캐시된 데이터를 기반으로 자산 현황을 즉시 연산하여 반환 (레이턴시 격리)
    result = get_enriched_accounts_data(db)

    # 2. 현재 보유 중인 고유 종목들의 시세를 백그라운드 태스크로 갱신 스케줄링
    stock_codes = set()
    for acc in result.get("accounts", []):
        for stock in acc.get("stocks", []):
            if stock.get("code"):
                stock_codes.add(stock["code"])

    if stock_codes:
        from database import SessionLocal
        background_tasks.add_task(sync_portfolio_prices_background, SessionLocal, list(stock_codes))

    return result

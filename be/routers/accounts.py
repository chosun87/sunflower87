from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from portfolio_service import get_enriched_accounts_data

router = APIRouter(prefix="/api/accounts", tags=["Account"])


@router.get(
    "",
    summary="총자산 및 계좌별 세부 자산 현황 조회 API",
    description=(
        "SQLite 데이터베이스의 account 및 stocks 테이블을 통합 조회하여 "
        "총 자산 평가액, 계좌별 예수금, 주식 보유 내역 및 실시간 평가 수익률을 동적으로 계산해 반환합니다."
    ),
)
def get_miraeasset_accounts(db: Session = Depends(get_db)):
    """SQLite 데이터베이스 account 및 stocks 테이블을 기반으로 총자산 및 계좌별 세부 자산 현황을 반환합니다."""
    return get_enriched_accounts_data(db)

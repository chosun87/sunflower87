from datetime import datetime

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import Recommendation, get_db

router = APIRouter(prefix="/api/recommendations", tags=["Market Stock"])


@router.get(
    "",
    summary="AI 추천 종목 조회 API",
    description=(
        "오늘 날짜를 기준으로 AI가 정밀 선별한 우량 가치주, 성장주, 배당주 추천 목록과 "
        "추천 이유 및 분석 점수를 함께 반환합니다."
    ),
)
def get_ai_recommendations(db: Session = Depends(get_db)):
    """오늘 날짜에 맞춘 주식 가치주/성장주 목록 추천 데이터를 반환합니다."""
    current_date = datetime.now().strftime("%Y%m%d")
    db_recs = db.query(Recommendation).all()

    data = []
    for r in db_recs:
        data.append(
            {
                "name": r.name,
                "code": r.code,
                "tag": r.tag,
                "reason": r.reason,
                "score": r.score,
            }
        )

    return {
        "status": "success",
        "date": current_date,
        "data": data,
    }

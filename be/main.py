import sys
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# 보안 지침: 프로젝트 환경변수 로드
load_dotenv()

# 모듈 경로 추가로 패키지 임포트 보장
sys.path.append(str(Path(__file__).parent.resolve()))

from database import init_db  # noqa: E402
from routers import (  # noqa: E402
    stocks,
    accounts,
    transactions,
    recommendations,
    tasks,
)

TRADE_DATE_PERIOD = 60      # 기본 확보 거래일수 (약 3개월치 컴팩트 유지)
DATA_GAP_THRESHOLD = 120    # 데이터 공백 허용 임계치 (순수 거래일 기준 6개월치 통제)

app = FastAPI(
    title="sunflower87 API 코어",
    description="미래에셋 멀티 계좌 및 AI 주식 추천 시스템",
    version="0.1.0",
)

# 데이터베이스 테이블 초기화 및 무결성 검증 (구동 시점에 구동)
init_db()

# CORS 허용 정책 설정
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 모듈별 API 라우터 등록
app.include_router(stocks.router)
app.include_router(accounts.router)
app.include_router(transactions.router)
app.include_router(recommendations.router)
app.include_router(tasks.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

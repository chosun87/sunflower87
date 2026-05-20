import sys
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 보안 지침: 프로젝트 환경변수 로드
load_dotenv()

# 모듈 경로 추가로 패키지 임포트 보장
sys.path.append(str(Path(__file__).parent.resolve()))

from database import init_db  # noqa: E402
from migrate import run_migrations  # noqa: E402
from routers import (  # noqa: E402
    accounts,
    recommendations,
    stocks,
    tasks,
    transactions,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 데이터베이스 마이그레이션 우선 기동 (스키마 보장)
    run_migrations()
    # 데이터베이스 테이블 초기화 및 무결성 검증 (구동 시점에 구동)
    init_db()
    yield


app = FastAPI(
    title="sunflower87 API 코어",
    description="미래에셋 멀티 계좌 및 AI 주식 추천 시스템",
    version="0.1.0",
    lifespan=lifespan,
)

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

# touch

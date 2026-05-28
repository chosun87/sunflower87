import sys
from contextlib import asynccontextmanager
from pathlib import Path

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# 보안 지침: 프로젝트 환경변수 로드
load_dotenv()

# 모듈 경로 추가로 패키지 임포트 보장
sys.path.append(str(Path(__file__).parent.resolve()))
from database import Account, SessionLocal, init_db  # noqa: E402
from git import git_task  # noqa: E402
from migrate import run_migrations  # noqa: E402
from routers import (  # noqa: E402
    account,
    dashboard,
    recommendation,
    stock,
    stock_ohlcv,
    transaction,
    transaction_cash,
    setting,
)
from services.daily_balance_service import sync_daily_balances_for_account  # noqa: E402


def run_midnight_batch():
    print("[Batch] Running daily balance synchronization...")
    db = SessionLocal()
    try:
        accounts = db.query(Account).filter(Account.dt_deleted.is_(None)).all()
        for acc in accounts:
            try:
                res = sync_daily_balances_for_account(db, acc.acc_cd)
                print(f"[Batch] Account {acc.acc_cd}: {res.get('message')}")
            except Exception as e:
                print(f"[Batch] Error syncing account {acc.acc_cd}: {e}")
    finally:
        db.close()
    print("[Batch] Daily balance synchronization complete.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 데이터베이스 마이그레이션 우선 기동 (스키마 보장)
    run_migrations()
    # 데이터베이스 테이블 초기화 및 무결성 검증 (구동 시점에 구동)
    init_db()

    # 1. Start APScheduler for Midnight Batch (00:30)
    scheduler = BackgroundScheduler()
    scheduler.add_job(run_midnight_batch, "cron", hour=0, minute=30)
    scheduler.start()

    # 2. Run initial sync on Startup
    run_midnight_batch()

    yield

    # Shutdown scheduler when app stops
    scheduler.shutdown()


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
app.include_router(account.router)
app.include_router(transaction.router)
app.include_router(transaction_cash.router)
app.include_router(stock.router)
app.include_router(stock_ohlcv.router)
app.include_router(recommendation.router)
app.include_router(dashboard.router)
app.include_router(git_task.router)
app.include_router(setting.router)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)

# touch

import os
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    create_engine,
)
from sqlalchemy.orm import declarative_base, sessionmaker

# 보안 지침: 환경변수 로드
load_dotenv()

# .env 로드 및 기본 폴백 설정
env_db_url = os.getenv("DATABASE_URL", "sqlite:///sunflower87.db")

# SQLite URL 규격화 검증 및 방어적 변환 지원
if env_db_url and not env_db_url.startswith("sqlite:///"):
    DATABASE_URL = f"sqlite:///{env_db_url}"
else:
    DATABASE_URL = env_db_url

# 커넥션 풀 및 엔진 생성
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Account(Base):
    """계좌 마스터 (account) 테이블 모델"""

    __tablename__ = "account"

    acc_cd = Column(String, primary_key=True)
    acc_nm = Column(String, nullable=False)
    acc_company_nm = Column(String, nullable=False)
    acc_order = Column(Integer, nullable=False, default=1)
    cash_balance = Column(Integer, nullable=False, default=0.0)
    initial_cash = Column(Integer, nullable=False, default=0.0)
    dt_created = Column(DateTime, default=datetime.utcnow, nullable=False)
    dt_deleted = Column(DateTime, nullable=True)


class Transaction(Base):
    """매매 거래 내역 (transactions) 테이블 모델"""

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, default=datetime.utcnow, nullable=False)
    type = Column(String, nullable=False)  # BUY / SELL
    code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)
    tax_fee = Column(Integer, nullable=False, default=0)
    acc_cd = Column(String, ForeignKey("account.acc_cd"), nullable=False, default="")


class Stock(Base):
    """현재 보유 잔고 (stocks) 테이블 모델"""

    __tablename__ = "stocks"

    code = Column(String, primary_key=True)
    acc_cd = Column(String, ForeignKey("account.acc_cd"), primary_key=True, default="")
    name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    avg_price = Column(Float, nullable=False)
    current_price = Column(Integer, nullable=False, default=0)
    purchase_amount = Column(Float, nullable=False, default=0.0)


class Recommendation(Base):
    """AI 추천 종목 (recommendations) 테이블 모델"""

    __tablename__ = "recommendations"

    code = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    tag = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    score = Column(Integer, nullable=False)


class CacheStock(Base):
    """종목 검색 및 동적 마스터 데이터용 (cache_stocks) 테이블 모델"""

    __tablename__ = "cache_stocks"

    stock_code = Column(String, primary_key=True)
    stock_name = Column(String, nullable=False)
    market = Column(String, nullable=True)  # KOSPI, KOSDAQ, ETF 시장 구분 필드 추가
    is_active = Column(Integer, default=1, nullable=False)  # 거래 활성 상태 플래그
    dt_cached = Column(DateTime, default=datetime.utcnow, nullable=False)


class StockOHLCVCache(Base):
    """시고저종(OHLCV) 주가 캐시용 (stock_ohlcv_cache) 테이블 모델"""

    __tablename__ = "stock_ohlcv_cache"

    stock_code = Column(String, primary_key=True)
    trade_date = Column(String, primary_key=True)
    open_price = Column(Integer, nullable=False)
    high_price = Column(Integer, nullable=False)
    low_price = Column(Integer, nullable=False)
    close_price = Column(Integer, nullable=False)
    volume = Column(Integer, nullable=False)


def init_db():
    """데이터베이스 테이블을 생성하고 기본 초기 데이터를 적재합니다."""
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. [Lazy Initialization] 동적 주식 마스터 테이블 (cache_stocks) 초고속 시딩 처리
        try:
            from services.cache_stocks import sync_cache_stocks
            sync_cache_stocks(db)
        except Exception as seed_err:
            db.rollback()
            print(f"[ERROR] Failed to seed stock masters on startup: {seed_err}")

        # 2. 각 계좌별로 연대기 포트폴리오를 최초 자동 동기화/재계산 처리
        from portfolio_service import recalculate_portfolio_for_account

        for acc in db.query(Account).filter(Account.dt_deleted.is_(None)).all():
            try:
                recalculate_portfolio_for_account(db, acc.acc_cd)
            except Exception as re_err:
                err_info = (
                    f"Error pre-calculating portfolio for " f"{acc.acc_cd} on startup:"
                )
                print(f"{err_info} {re_err}")
    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()


def get_db():
    """FastAPI 종속성 주입용 DB 세션 제너레이터"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

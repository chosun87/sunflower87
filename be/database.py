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
    cash_balance = Column(Integer, nullable=False, default=0)
    dt_created = Column(DateTime, default=datetime.utcnow, nullable=False)
    dt_deleted = Column(DateTime, nullable=True)


class Transaction(Base):
    """매매 내역  (transaction) 테이블 모델"""

    __tablename__ = "transaction"

    id = Column(Integer, primary_key=True, autoincrement=True)
    acc_cd = Column(String, ForeignKey("account.acc_cd"), nullable=False)
    dt_trade = Column(
        String, default=lambda: datetime.utcnow().strftime("%Y-%m-%d"), nullable=False
    )
    trade_type = Column(String, nullable=False)  # BUY / SELL
    stock_code = Column(String, ForeignKey("stock_cache.stock_code"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)
    tax_fee = Column(Integer, nullable=False, default=0)
    dt_deleted = Column(DateTime, nullable=True)


class TransactionCash(Base):
    """현금 거래 원장 (transaction_cash) 테이블 모델"""

    __tablename__ = "transaction_cash"

    id = Column(Integer, primary_key=True, autoincrement=True)
    acc_cd = Column(String, ForeignKey("account.acc_cd"), nullable=False)
    dt_cash = Column(
        String, default=lambda: datetime.utcnow().strftime("%Y-%m-%d"), nullable=False
    )
    cash_type = Column(
        String, nullable=False
    )  # DEPOSIT / WITHDRAW / INTEREST / DIVIDEND / FEE
    amount = Column(Integer, nullable=False)
    description = Column(String, nullable=True)
    dt_deleted = Column(DateTime, nullable=True)


class AccountDailyBalance(Base):
    """계좌별 일자별 잔고 (account_daily_balance) 테이블 모델"""

    __tablename__ = "account_daily_balance"

    acc_cd = Column(String, ForeignKey("account.acc_cd"), primary_key=True)
    trade_date = Column(String, primary_key=True)  # YYYY-MM-DD
    cash_balance = Column(Integer, nullable=False, default=0)
    stock_eval_balance = Column(Integer, nullable=False, default=0)
    total_balance = Column(Integer, nullable=False, default=0)
    return_rate = Column(Float, nullable=False, default=0.0)


class Stock(Base):
    """현재 보유 잔고 (stock) 테이블 모델"""

    __tablename__ = "stock"

    stock_code = Column(String, ForeignKey("stock_cache.stock_code"), primary_key=True)
    acc_cd = Column(String, ForeignKey("account.acc_cd"), primary_key=True)
    quantity = Column(Integer, nullable=False)
    avg_price = Column(Integer, nullable=False)  # INTEGER 캐스팅 적용
    current_price = Column(Integer, nullable=False, default=0)
    purchase_amount = Column(Integer, nullable=False, default=0)  # INTEGER 캐스팅 적용


class StockCache(Base):
    """종목 마스터 캐시 (stock_cache) 테이블 모델 - SSOT"""

    __tablename__ = "stock_cache"

    stock_code = Column(String, primary_key=True)
    stock_name = Column(String, nullable=False)
    market = Column(String, nullable=True)  # KOSPI, KOSDAQ, KONEX, ETF
    dt_cached = Column(DateTime, default=datetime.utcnow, nullable=False)
    dt_deleted = Column(DateTime, nullable=True)


class StockOHLCVCache(Base):
    """시고저종(OHLCV) 주가 캐시용 (stock_ohlcv_cache) 테이블 모델"""

    __tablename__ = "stock_ohlcv_cache"

    stock_code = Column(String, ForeignKey("stock_cache.stock_code"), primary_key=True)
    trade_date = Column(String, primary_key=True)  # YYYY-MM-DD
    open_price = Column(Integer, nullable=False)
    high_price = Column(Integer, nullable=False)
    low_price = Column(Integer, nullable=False)
    close_price = Column(Integer, nullable=False)
    volume = Column(Integer, nullable=False)
    trading_value = Column(Integer, nullable=False, default=0)  # 거래대금 신설
    fluctuation_rate = Column(Float, nullable=False, default=0.0)  # 등락률 신설


class Recommendation(Base):
    """AI 추천 종목 (recommendation) 테이블 모델"""

    __tablename__ = "recommendation"

    stock_code = Column(String, ForeignKey("stock_cache.stock_code"), primary_key=True)
    tag = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    score = Column(Integer, nullable=False)
    dt_recommended = Column(DateTime, default=datetime.utcnow, nullable=False)
    dt_deleted = Column(DateTime, nullable=True)
    investor_score = Column(Integer, nullable=True)  # 0~5


def init_db():
    """데이터베이스 테이블을 생성하고 기본 초기 데이터를 적재합니다."""
    Base.metadata.create_all(bind=engine)
    # 초기 로딩 시의 모듈 임포트 결합을 제거하고, 빈 껍데기만 남겨둡니다.
    # 데이터는 migrate.py 및 실제 API 호출 흐름에서 채워질 예정입니다.
    pass


def get_db():
    """FastAPI 종속성 주입용 DB 세션 제너레이터"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

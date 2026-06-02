import os
import threading
from datetime import datetime

from dotenv import load_dotenv
from sqlalchemy import (
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    UniqueConstraint,
    create_engine,
    event,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy.ext.hybrid import hybrid_property

# 전역 SQLite 쓰기 잠금 (동시성 데드락 방지용)
db_write_lock = threading.Lock()

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
engine = create_engine(
    DATABASE_URL, connect_args={"check_same_thread": False, "timeout": 15}
)

# Foreign Key 제약 활성화 + WAL 모드 (성능 개선)
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """SQLite 초기화: FK 제약, WAL 모드, 성능 튜닝"""
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Account(Base):
    """계좌 마스터 (account) 테이블 모델"""

    __tablename__ = "account"

    acc_cd = Column(String(20), primary_key=True)
    acc_nm = Column(String(50), nullable=False)
    acc_company_nm = Column(String(100), nullable=False)
    acc_order = Column(Integer, nullable=False, default=1)
    dt_opened = Column(String, nullable=True)
    cash_balance = Column(Integer, nullable=False, default=0)
    dt_created = Column(String, default=lambda: datetime.utcnow().isoformat(), nullable=False)
    dt_deleted = Column(String, nullable=True)
    
    # Phase 2: Soft Delete 패턴 강화
    @hybrid_property
    def is_active(self):
        """Python: 활성 여부"""
        return self.dt_deleted is None
    
    @is_active.expression
    def is_active(cls):
        """SQL: 활성 여부"""
        return cls.dt_deleted.is_(None)
    
    @hybrid_property
    def is_deleted(self):
        """Python: 삭제 여부"""
        return self.dt_deleted is not None
    
    @is_deleted.expression
    def is_deleted(cls):
        """SQL: 삭제 여부"""
        return cls.dt_deleted.isnot(None)


class Transaction(Base):
    """매매 내역  (transaction) 테이블 모델"""

    __tablename__ = "transaction"

    id = Column(Integer, primary_key=True, autoincrement=True)
    acc_cd = Column(String(20), ForeignKey("account.acc_cd"), nullable=False)
    dt_trade = Column(
        String, default=lambda: datetime.utcnow().strftime("%Y-%m-%d"), nullable=False
    )
    trade_type = Column(String(10), nullable=False)  # BUY / SELL
    stock_code = Column(String(6), ForeignKey("stock_cache.stock_code"), nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)
    tax_fee = Column(Integer, nullable=False, default=0)
    dt_deleted = Column(String, nullable=True)


class TransactionCash(Base):
    """현금 거래 원장 (transaction_cash) 테이블 모델"""

    __tablename__ = "transaction_cash"

    id = Column(Integer, primary_key=True, autoincrement=True)
    acc_cd = Column(String(20), ForeignKey("account.acc_cd"), nullable=False)
    dt_cash = Column(
        String, default=lambda: datetime.utcnow().strftime("%Y-%m-%d"), nullable=False
    )
    cash_type = Column(
        String(10), nullable=False
    )  # DEPOSIT / WITHDRAW / INTEREST / DIVIDEND / FEE
    amount = Column(Integer, nullable=False)
    description = Column(String(200), nullable=True)
    dt_deleted = Column(String, nullable=True)


class AccountBalanceDaily(Base):
    """계좌별 일자별 잔고 (account_balance_daily) 테이블 모델"""

    __tablename__ = "account_balance_daily"

    # Phase 2: Surrogate Key 도입
    id = Column(Integer, primary_key=True, autoincrement=True)
    acc_cd = Column(String(20), ForeignKey("account.acc_cd"), nullable=False)
    trade_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    cash_balance = Column(Integer, nullable=False, default=0)
    stock_eval_balance = Column(Integer, nullable=False, default=0)
    total_balance = Column(Integer, nullable=False, default=0)
    return_rate = Column(Float, nullable=False, default=0.0)
    
    # Unique Constraint: 비즈니스 키 보존
    __table_args__ = (
        UniqueConstraint('acc_cd', 'trade_date', name='uq_account_balance_daily_acc_trade'),
    )


class Stock(Base):
    """현재 보유 잔고 (stock) 테이블 모델"""

    __tablename__ = "stock"

    # Phase 2: Surrogate Key 도입
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(6), ForeignKey("stock_cache.stock_code"), nullable=False)
    acc_cd = Column(String(20), ForeignKey("account.acc_cd"), nullable=False)
    quantity = Column(Integer, nullable=False)
    avg_price = Column(Integer, nullable=False)  # INTEGER 캐스팅 적용
    current_price = Column(Integer, nullable=False, default=0)
    purchase_amount = Column(Integer, nullable=False, default=0)  # INTEGER 캐스팅 적용
    
    # Unique Constraint: 비즈니스 키 보존
    __table_args__ = (
        UniqueConstraint('stock_code', 'acc_cd', name='uq_stock_stock_code_acc'),
    )


class StockCache(Base):
    """종목 마스터 캐시 (stock_cache) 테이블 모델 - SSOT"""

    __tablename__ = "stock_cache"

    stock_code = Column(String(6), primary_key=True)
    stock_name = Column(String(100), nullable=False)
    market = Column(String(10), nullable=False)  # KOSPI, KOSDAQ, KONEX, ETF
    dt_cached = Column(String, default=lambda: datetime.utcnow().isoformat(), nullable=False)
    dt_deleted = Column(String, nullable=True)
    
    # Phase 2: Soft Delete 패턴 강화
    @hybrid_property
    def is_active(self):
        """Python: 활성 여부"""
        return self.dt_deleted is None
    
    @is_active.expression
    def is_active(cls):
        """SQL: 활성 여부"""
        return cls.dt_deleted.is_(None)
    
    @hybrid_property
    def is_deleted(self):
        """Python: 삭제 여부"""
        return self.dt_deleted is not None
    
    @is_deleted.expression
    def is_deleted(cls):
        """SQL: 삭제 여부"""
        return cls.dt_deleted.isnot(None)


class StockOHLCVDaily(Base):
    """시고저종(OHLCV) 일별 주가 (stock_ohlcv_daily) 테이블 모델"""

    __tablename__ = "stock_ohlcv_daily"

    # Phase 2: Surrogate Key 도입 (테이블 분리)
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(6), ForeignKey("stock_cache.stock_code"), nullable=False)
    trade_date = Column(String(10), nullable=False)  # YYYY-MM-DD
    open_price = Column(Integer, nullable=False)
    high_price = Column(Integer, nullable=False)
    low_price = Column(Integer, nullable=False)
    close_price = Column(Integer, nullable=False)
    volume = Column(Integer, nullable=False)
    trading_value = Column(Integer, nullable=False, default=0)
    fluctuation_rate = Column(Float, nullable=False, default=0.0)
    change_price = Column(Integer, nullable=False, default=0)
    change_price_code = Column(
        String(1), nullable=True
    )  # 1: 상한, 2: 상승, 3: 보합, 4: 하한, 5: 하락
    dt_updated = Column(String, default=lambda: datetime.utcnow().isoformat(), nullable=False)
    
    # Unique Constraint: 같은 종목, 날짜는 1개만
    __table_args__ = (
        UniqueConstraint('stock_code', 'trade_date', name='uq_stock_ohlcv_daily_stock_date'),
    )


class StockOHLCVCurrent(Base):
    """실시간 시고저종(OHLCV) 주가 (stock_ohlcv_current) 테이블 모델"""

    __tablename__ = "stock_ohlcv_current"

    # Phase 2: Surrogate Key 도입 (테이블 분리)
    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(6), ForeignKey("stock_cache.stock_code"), nullable=False)
    trade_date = Column(String(10), nullable=False)  # YYYY-MM-DD (보통 오늘 날짜)
    open_price = Column(Integer, nullable=False)
    high_price = Column(Integer, nullable=False)
    low_price = Column(Integer, nullable=False)
    close_price = Column(Integer, nullable=False)
    volume = Column(Integer, nullable=False)
    trading_value = Column(Integer, nullable=False, default=0)
    fluctuation_rate = Column(Float, nullable=False, default=0.0)  # cr (등락률)
    change_price = Column(Integer, nullable=False, default=0)  # cv (대비/전일비)
    change_price_code = Column(
        String(1), nullable=True
    )  # 1: 상한, 2: 상승, 3: 보합, 4: 하한, 5: 하락
    dt_updated = Column(String, default=lambda: datetime.utcnow().isoformat(), nullable=False)
    
    # Unique Constraint: 같은 종목, 날짜는 1개만
    __table_args__ = (
        UniqueConstraint('stock_code', 'trade_date', name='uq_stock_ohlcv_current_stock_date'),
    )


class Recommendation(Base):
    """AI 추천 종목 (recommendation) 테이블 모델"""

    __tablename__ = "recommendation"

    stock_code = Column(String(6), ForeignKey("stock_cache.stock_code"), primary_key=True)
    tag = Column(String(50), nullable=False)
    reason = Column(String(500), nullable=False)
    score = Column(Integer, nullable=False)
    dt_recommended = Column(String, default=lambda: datetime.utcnow().isoformat(), nullable=False)
    dt_deleted = Column(String, nullable=True)
    investor_score = Column(Integer, nullable=True)  # 0~5
    
    # Phase 2: Soft Delete 패턴 강화
    @hybrid_property
    def is_active(self):
        """Python: 활성 여부"""
        return self.dt_deleted is None
    
    @is_active.expression
    def is_active(cls):
        """SQL: 활성 여부"""
        return cls.dt_deleted.is_(None)
    
    @hybrid_property
    def is_deleted(self):
        """Python: 삭제 여부"""
        return self.dt_deleted is not None
    
    @is_deleted.expression
    def is_deleted(cls):
        """SQL: 삭제 여부"""
        return cls.dt_deleted.isnot(None)


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

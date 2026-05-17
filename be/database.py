import os
from datetime import datetime
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
)
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# 보안 지침: 환경변수 로드
load_dotenv()

# .env 로드 및 기본 폴백 설정
env_db_url = os.getenv("DATABASE_URL")

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
    acc_code = Column(String, ForeignKey("account.acc_cd"), nullable=False, default="")


class Stock(Base):
    """현재 보유 잔고 (stocks) 테이블 모델"""

    __tablename__ = "stocks"

    code = Column(String, primary_key=True)
    acc_code = Column(
        String, ForeignKey("account.acc_cd"), primary_key=True, default=""
    )
    name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    avg_price = Column(Integer, nullable=False)
    current_price = Column(Integer, nullable=False, default=0)


class Recommendation(Base):
    """AI 추천 종목 (recommendations) 테이블 모델"""

    __tablename__ = "recommendations"

    code = Column(String, primary_key=True)
    name = Column(String, nullable=False)
    tag = Column(String, nullable=False)
    reason = Column(String, nullable=False)
    score = Column(Integer, nullable=False)


class CacheStock(Base):
    """종목 검색 캐싱용 (cache_stocks) 테이블 모델"""

    __tablename__ = "cache_stocks"

    stock_code = Column(String, primary_key=True)
    stock_name = Column(String, nullable=False)
    dt_cached = Column(DateTime, default=datetime.utcnow, nullable=False)


def init_db():
    """데이터베이스 테이블을 생성하고 기본 초기 데이터를 적재합니다."""
    # 만약 account_number 또는 구버전 컬럼이 없는 스키마일 경우 테이블 재생성
    db = SessionLocal()
    need_recreate = False
    try:
        cursor = db.execute("PRAGMA table_info(transactions)")
        t_cols = [row[1] for row in cursor.fetchall()]
        cursor = db.execute("PRAGMA table_info(stocks)")
        s_cols = [row[1] for row in cursor.fetchall()]
        cursor = db.execute("PRAGMA table_info(account)")
        acc_cols = [row[1] for row in cursor.fetchall()]
        cursor = db.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='recommendations'"
        )
        rec_exists = cursor.fetchone()
        cursor = db.execute(
            "SELECT name FROM sqlite_master "
            "WHERE type='table' AND name='cache_stocks'"
        )
        cache_exists = cursor.fetchone()

        if (
            (t_cols and "acc_code" not in t_cols)
            or (s_cols and "acc_code" not in s_cols)
            or (s_cols and "current_price" not in s_cols)
            or not acc_cols
            or (acc_cols and "acc_cd" not in acc_cols)
            or not rec_exists
            or not cache_exists
        ):
            need_recreate = True
    except Exception:
        need_recreate = True
    finally:
        db.close()

    if need_recreate:
        print("Schema change detected. Recreating database tables...")
        engine.dispose()
        Base.metadata.drop_all(bind=engine)

    Base.metadata.create_all(bind=engine)


def get_db():
    """FastAPI 종속성 주입용 DB 세션 제너레이터"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

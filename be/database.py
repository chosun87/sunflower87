import os
from datetime import datetime
from sqlalchemy import create_engine, Column, Integer, String, Float, DateTime
from sqlalchemy.orm import declarative_base, sessionmaker
from dotenv import load_dotenv

# 보안 지침: 환경변수 로드
load_dotenv()

# .env 로드 및 기본 폴백 설정
env_db_url = os.getenv("DATABASE_URL", "sqlite:///sunflower87.db")

# SQLite URL 규격화 검증 및 방어적 변환 지원
if env_db_url and not env_db_url.startswith("sqlite:///"):
    DATABASE_URL = f"sqlite:///{env_db_url}"
else:
    DATABASE_URL = env_db_url or "sqlite:///sunflower87.db"

# 커넥션 풀 및 엔진 생성
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


class Account(Base):
    """계좌 마스터 (account) 테이블 모델"""

    __tablename__ = "account"

    accCode = Column(String, primary_key=True)
    accName = Column(String, nullable=False)
    accCompanyName = Column(String, nullable=False)
    cashBalance = Column(Float, nullable=False, default=0.0)
    accOrder = Column(Integer, nullable=False, default=1)
    dtCreated = Column(DateTime, default=datetime.utcnow, nullable=False)
    dtDeleted = Column(DateTime, nullable=True)


class Transaction(Base):
    """매매 거래 내역 (transactions) 테이블 모델"""

    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    date = Column(DateTime, default=datetime.utcnow, nullable=False)
    type = Column(String, nullable=False)  # BUY / SELL
    code = Column(String, nullable=False)
    name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    price = Column(Float, nullable=False)
    accCode = Column(String, nullable=False, default="A001")


class Stock(Base):
    """현재 보유 잔고 (stocks) 테이블 모델"""

    __tablename__ = "stocks"

    code = Column(String, primary_key=True)
    accCode = Column(String, primary_key=True, default="A001")
    name = Column(String, nullable=False)
    quantity = Column(Integer, nullable=False)
    avg_price = Column(Float, nullable=False)


def init_db():
    """데이터베이스 테이블을 생성하고 기본 초기 데이터를 적재합니다."""
    # 만약 account_number 컬럼이 없는 구버전 스키마일 경우 테이블 재생성
    db = SessionLocal()
    need_recreate = False
    try:
        cursor = db.execute("PRAGMA table_info(transactions)")
        t_cols = [row[1] for row in cursor.fetchall()]
        cursor = db.execute("PRAGMA table_info(stocks)")
        s_cols = [row[1] for row in cursor.fetchall()]
        cursor = db.execute("PRAGMA table_info(account)")
        acc_cols = [row[1] for row in cursor.fetchall()]
        if (t_cols and "accCode" not in t_cols) or (s_cols and "accCode" not in s_cols) or not acc_cols:
            need_recreate = True
    except Exception:
        pass
    finally:
        db.close()

    if need_recreate:
        print("Schema change detected. Recreating database tables...")
        Base.metadata.drop_all(bind=engine)

    Base.metadata.create_all(bind=engine)

    # 초기 기획 및 mock_data의 보유 주식을 SQLite 마이그레이션 (비어있을 경우에만)
    db = SessionLocal()
    try:
        if db.query(Account).count() == 0:
            default_accounts = [
                Account(
                    accCode="A001",
                    accName="주식계좌 1",
                    accCompanyName="미래에셋증권",
                    cashBalance=39800000.0,
                    accOrder=1,
                ),
                Account(
                    accCode="A002",
                    accName="연금계좌",
                    accCompanyName="미래에셋증권",
                    cashBalance=0.0,
                    accOrder=2,
                ),
                Account(
                    accCode="A003",
                    accName="ISA계좌",
                    accCompanyName="미래에셋증권",
                    cashBalance=0.0,
                    accOrder=3,
                ),
            ]
            db.add_all(default_accounts)
            db.commit()
            print("Database initialized with default accounts.")

        if db.query(Stock).count() == 0:
            # 기본 삼성전자, 현대차 종목 적재
            default_stocks = [
                Stock(
                    code="005930",
                    name="삼성전자",
                    quantity=100,
                    avg_price=72500,
                    accCode="A001",
                ),
                Stock(
                    code="005380",
                    name="현대차",
                    quantity=30,
                    avg_price=240000,
                    accCode="A001",
                ),
            ]
            db.add_all(default_stocks)
            db.commit()
            print("Database initialized with default stocks.")
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

import os
from datetime import datetime
from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    ForeignKey,
    text,
)
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
    acc_cd = Column(String, ForeignKey("account.acc_cd"), nullable=False, default="")


class Stock(Base):
    """현재 보유 잔고 (stocks) 테이블 모델"""

    __tablename__ = "stocks"

    code = Column(String, primary_key=True)
    acc_cd = Column(String, ForeignKey("account.acc_cd"), primary_key=True, default="")
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
    # 1. [마이그레이션] account 테이블에 initial_cash 컬럼이 없는 구 스키마 대응 및 값 강제 정렬
    db = SessionLocal()
    try:
        # account 테이블이 이미 존재할 때, 컬럼 정보 획득
        cursor = db.execute(text("PRAGMA table_info(account)"))
        acc_cols = [row[1] for row in cursor.fetchall()]
        if acc_cols and "initial_cash" not in acc_cols:
            db.execute(text("ALTER TABLE account ADD COLUMN initial_cash INTEGER DEFAULT 0"))
            db.commit()
            print("Successfully migrated: Added initial_cash column.")
        
        if acc_cols:
            # 기존 데이터가 존재하는 구 DB의 역산 무결성을 지키기 위해 기획 초기 자산값으로 동기화 정렬
            db.execute(text("UPDATE account SET initial_cash = 28539701 WHERE acc_cd = '미래-연금'"))
            db.execute(text("UPDATE account SET initial_cash = 40000000 WHERE acc_cd = '미래-ISA'"))
            db.execute(text("UPDATE account SET initial_cash = 20000000 WHERE acc_cd = '미래-종합'"))
            db.commit()
            print("Aligned initial_cash values for standard default accounts.")
    except Exception as migration_err:
        db.rollback()
        print(f"Migration initial_cash check/execution failed (safe to ignore if table doesn't exist yet): {migration_err}")
    finally:
        db.close()

    # 만약 acc_cd 또는 구버전 컬럼이 없는 스키마일 경우 테이블 재생성 경고 감지
    db = SessionLocal()
    need_recreate = False
    try:
        cursor = db.execute(text("PRAGMA table_info(transactions)"))
        t_cols = [row[1] for row in cursor.fetchall()]
        cursor = db.execute(text("PRAGMA table_info(stocks)"))
        s_cols = [row[1] for row in cursor.fetchall()]
        cursor = db.execute(text("PRAGMA table_info(account)"))
        acc_cols = [row[1] for row in cursor.fetchall()]
        cursor = db.execute(
            text(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name='recommendations'"
            )
        )
        rec_exists = cursor.fetchone()
        cursor = db.execute(
            text(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name='cache_stocks'"
            )
        )
        cache_exists = cursor.fetchone()

        cursor = db.execute(
            text(
                "SELECT name FROM sqlite_master "
                "WHERE type='table' AND name='stock_ohlcv_cache'"
            )
        )
        ohlcv_exists = cursor.fetchone()

        if (
            (t_cols and "acc_cd" not in t_cols)
            or (s_cols and "acc_cd" not in s_cols)
            or (s_cols and "current_price" not in s_cols)
            or not acc_cols
            or (acc_cols and "acc_cd" not in acc_cols)
            or (acc_cols and "initial_cash" not in acc_cols)
            or not rec_exists
            or not cache_exists
            or not ohlcv_exists
        ):
            need_recreate = True
    except Exception:
        need_recreate = True
    finally:
        db.close()

    if need_recreate:
        print(
            "⚠️ WARNING: Schema discrepancy detected! "
            "Automatic database recreating (drop_all) is disabled to protect "
            "your registered data."
        )

    Base.metadata.create_all(bind=engine)

    # 초기 기획 및 mock_data의 보유 주식을 SQLite 마이그레이션 (비어있을 경우에만)
    db = SessionLocal()
    try:
        if db.query(Account).count() == 0:
            default_accounts = [
                Account(
                    acc_cd="미래-연금",
                    acc_nm="연금저축계좌(신)",
                    acc_company_nm="미래에셋증권",
                    cash_balance=28539701.0,
                    initial_cash=28539701.0,
                    acc_order=1,
                    dt_created=datetime.strptime("2021-11-04", "%Y-%m-%d"),
                ),
                Account(
                    acc_cd="미래-ISA",
                    acc_nm="ISA(중계형)",
                    acc_company_nm="미래에셋증권",
                    cash_balance=40000000.0,
                    initial_cash=40000000.0,
                    acc_order=2,
                    dt_created=datetime.strptime("2025-11-06", "%Y-%m-%d"),
                ),
                Account(
                    acc_cd="미래-종합",
                    acc_nm="종합_주식",
                    acc_company_nm="미래에셋증권",
                    cash_balance=20000000.0,
                    initial_cash=20000000.0,
                    acc_order=3,
                    dt_created=datetime.strptime("2006-05-15", "%Y-%m-%d"),
                ),
            ]
            db.add_all(default_accounts)
            db.commit()
            print("Database initialized with default accounts.")

            if db.query(Transaction).count() == 0:
                # 초기 거래 이력을 시딩하여 포트폴리오가 거래 장부 기준으로 무결하게 산출되도록 처리
                default_transactions = [
                    # 미래-종합 계좌의 초기 주식 시드 거래 이력 (2025년 12월 01일 매수 가정)
                    Transaction(
                        date=datetime.strptime("2025-12-01 09:00:00", "%Y-%m-%d %H:%M:%S"),
                        type="BUY",
                        code="005930",
                        name="삼성전자",
                        quantity=100,
                        price=72500,
                        acc_cd="미래-종합"
                    ),
                    Transaction(
                        date=datetime.strptime("2025-12-01 09:10:00", "%Y-%m-%d %H:%M:%S"),
                        type="BUY",
                        code="005380",
                        name="현대차",
                        quantity=30,
                        price=240000,
                        acc_cd="미래-종합"
                    )
                ]
                db.add_all(default_transactions)
                db.commit()
                print("Database initialized with default transactions.")

        if db.query(Recommendation).count() == 0:
            default_recs = [
                Recommendation(
                    code="005930",
                    name="삼성전자",
                    tag="가치주",
                    reason="외국인 최근 5일 연속 순매수세 유입 및 20일 이동평균선 지지 확인.",
                    score=92,
                ),
                Recommendation(
                    code="005380",
                    name="현대차",
                    tag="저PBR/배당",
                    reason="정부 밸류업 프로그램 최대 수혜 예상. PBR 0.6배 수준으로 극심한 저평가 상태.",
                    score=88,
                ),
                Recommendation(
                    code="035420",
                    name="네이버",
                    tag="기술주",
                    reason="RSI 지수 30 부근으로 단기 과매도 구간 진입에 따른 기술적 반등 기대.",
                    score=85,
                ),
            ]
            db.add_all(default_recs)
            db.commit()
            print("Database initialized with default recommendations.")

        # 초기 적재 완료 후, 각 계좌별로 연대기 포트폴리오를 최초 자동 동기화/재계산 처리
        from portfolio_service import recalculate_portfolio_for_account
        for acc in db.query(Account).filter(Account.dt_deleted.is_(None)).all():
            try:
                recalculate_portfolio_for_account(db, acc.acc_cd)
            except Exception as re_err:
                print(f"Error pre-calculating portfolio for {acc.acc_cd} on startup: {re_err}")
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

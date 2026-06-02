import os
import sqlite3
from datetime import datetime

from database import (
    Account,
    Base,
    Recommendation,
    SessionLocal,
    Stock,
    StockCache,
    Transaction,
    engine,
)

DB_PATH = "sunflower87.db"


def run_migrations():
    print("[Migration] Starting 3NF database schema migrations...")
    if not os.path.exists(DB_PATH):
        print("[Migration] Database file does not exist yet. Creating new schema...")
        Base.metadata.create_all(bind=engine)
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    # Check for legacy tables
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name='transactions'"
    )
    has_legacy = cursor.fetchone() is not None

    if not has_legacy:
        print(
            "[Migration] No legacy 'transactions' table found. Schema might already be updated."
        )
        # Ensure new schema is created just in case
        Base.metadata.create_all(bind=engine)
        conn.close()
        return

    print("[Migration] Legacy schema detected. Backing up data to memory...")

    def fetch_all(table_name):
        try:
            cursor.execute(f"SELECT * FROM {table_name}")
            rows = cursor.fetchall()
            cols = [desc[0] for desc in cursor.description]
            return [dict(zip(cols, row)) for row in rows]
        except Exception:
            return []

    accounts_data = fetch_all("account")
    transactions_data = fetch_all("transactions")
    stocks_data = fetch_all("stocks")
    cache_stocks_data = fetch_all("cache_stocks")
    recs_data = fetch_all("recommendations")

    conn.close()

    print(
        f"[Migration] Backup complete: {len(accounts_data)} accounts, {len(transactions_data)} transactions, {len(stocks_data)} stocks."
    )
    print("[Migration] Dropping all legacy tables...")

    # Drop all tables manually since Base.metadata.drop_all() might not know about legacy tables
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    legacy_tables = [
        "account",
        "transactions",
        "stocks",
        "cache_stocks",
        "recommendations",
        "stock_ohlcv_cache",
    ]
    for table in legacy_tables:
        cursor.execute(f"DROP TABLE IF EXISTS {table}")
    conn.commit()
    conn.close()

    print("[Migration] Creating new 3NF schema...")
    Base.metadata.create_all(bind=engine)

    print("[Migration] Inserting backed up data into new schema...")
    db = SessionLocal()
    try:
        # 1. Account
        for d in accounts_data:
            dt_del = d.get("dt_deleted")
            if isinstance(dt_del, str):
                try:
                    dt_del = datetime.strptime(dt_del, "%Y-%m-%d %H:%M:%S.%f").isoformat()
                except ValueError:
                    try:
                        dt_del = datetime.strptime(dt_del, "%Y-%m-%d %H:%M:%S").isoformat()
                    except ValueError:
                        dt_del = None

            dt_cre = d.get("dt_created")
            if isinstance(dt_cre, str):
                try:
                    dt_cre = datetime.strptime(dt_cre, "%Y-%m-%d %H:%M:%S.%f").isoformat()
                except ValueError:
                    dt_cre = datetime.utcnow().isoformat()
            else:
                dt_cre = datetime.utcnow().isoformat()

            new_acc = Account(
                acc_cd=d["acc_cd"],
                acc_nm=d["acc_nm"],
                acc_company_nm=d.get("acc_company_nm", "미래에셋"),
                acc_order=d.get("acc_order", 1),
                dt_opened=d.get("dt_opened"),
                cash_balance=int(d.get("cash_balance", 0)),
                dt_created=dt_cre,
                dt_deleted=dt_del,
            )
            db.merge(new_acc)

        # 2. StockCache
        for d in cache_stocks_data:
            dt_c = d.get("dt_cached")
            if isinstance(dt_c, str):
                try:
                    dt_c = datetime.strptime(dt_c, "%Y-%m-%d %H:%M:%S.%f").isoformat()
                except ValueError:
                    dt_c = datetime.utcnow().isoformat()
            else:
                dt_c = datetime.utcnow().isoformat()

            new_cache = StockCache(
                stock_code=d["stock_code"],
                stock_name=d["stock_name"],
                market=d.get("market"),
                dt_cached=dt_c,
                dt_deleted=None,
            )
            db.merge(new_cache)

        db.commit()  # Commit caches first for foreign keys

        # 3. Transaction
        for d in transactions_data:
            dt_t = d.get("date")
            if isinstance(dt_t, str):
                try:
                    dt_t = datetime.strptime(dt_t, "%Y-%m-%d %H:%M:%S.%f").isoformat()
                except ValueError:
                    try:
                        dt_t = datetime.strptime(dt_t, "%Y-%m-%d %H:%M:%S").isoformat()
                    except ValueError:
                        dt_t = datetime.utcnow().isoformat()
            else:
                dt_t = datetime.utcnow().isoformat()

            # Just in case cache doesn't exist
            if not db.query(StockCache).filter_by(stock_code=d["code"]).first():
                db.merge(
                    StockCache(
                        stock_code=d["code"],
                        stock_name=d["name"],
                        dt_cached=datetime.utcnow().isoformat(),
                    )
                )
                db.commit()

            new_tx = Transaction(
                id=d["id"],
                acc_cd=d["acc_cd"],
                dt_trade=dt_t,
                trade_type=d["type"],
                stock_code=d["code"],
                quantity=d["quantity"],
                price=int(d["price"]),
                tax_fee=int(d.get("tax_fee", 0)),
                dt_deleted=None,
            )
            db.merge(new_tx)

        # 4. Stock
        for d in stocks_data:
            if not db.query(StockCache).filter_by(stock_code=d["code"]).first():
                db.merge(
                    StockCache(
                        stock_code=d["code"],
                        stock_name=d.get("name", "알수없음"),
                        dt_cached=datetime.utcnow().isoformat(),
                    )
                )
                db.commit()

            new_stock = Stock(
                stock_code=d["code"],
                acc_cd=d["acc_cd"],
                quantity=d["quantity"],
                avg_price=int(round(float(d.get("avg_price", 0)))),
                current_price=int(d.get("current_price", 0)),
                purchase_amount=int(round(float(d.get("purchase_amount", 0)))),
            )
            db.merge(new_stock)

        # 5. Recommendation
        for d in recs_data:
            if not db.query(StockCache).filter_by(stock_code=d["code"]).first():
                db.merge(
                    StockCache(
                        stock_code=d["code"],
                        stock_name=d.get("name", "알수없음"),
                        dt_cached=datetime.utcnow().isoformat(),
                    )
                )
                db.commit()

            new_rec = Recommendation(
                stock_code=d["code"],
                tag=d["tag"],
                reason=d["reason"],
                score=d["score"],
                dt_recommended=datetime.utcnow().isoformat(),
                dt_deleted=None,
            )
            db.merge(new_rec)

        db.commit()
        print("[Migration] Data migration completed successfully!")
    except Exception as e:
        db.rollback()
        print(f"[Migration] Error during data insertion: {e}")
    finally:
        db.close()


def add_performance_indices():
    """Phase 1: 성능 최적화용 인덱스 추가"""
    print("[Migration] Phase 1: Adding performance indices...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    indices = [
        # 복합 인덱스 (대부분의 쿼리 조건)
        "CREATE INDEX IF NOT EXISTS idx_transaction_acc_cd_dt_trade ON transaction(acc_cd, dt_trade)",
        "CREATE INDEX IF NOT EXISTS idx_account_balance_daily_acc_cd_date ON account_balance_daily(acc_cd, trade_date)",
        "CREATE INDEX IF NOT EXISTS idx_stock_ohlcv_daily_stock_date ON stock_ohlcv_daily(stock_code, trade_date)",
        
        # FK 역방향 조회 성능 개선
        "CREATE INDEX IF NOT EXISTS idx_transaction_stock_code ON transaction(stock_code)",
        "CREATE INDEX IF NOT EXISTS idx_transaction_cash_acc_cd ON transaction_cash(acc_cd)",
        "CREATE INDEX IF NOT EXISTS idx_transaction_cash_dt_cash ON transaction_cash(dt_cash)",
        "CREATE INDEX IF NOT EXISTS idx_stock_code ON stock(stock_code)",
        "CREATE INDEX IF NOT EXISTS idx_stock_acc_cd ON stock(acc_cd)",
        
        # 날짜 필터 성능 개선
        "CREATE INDEX IF NOT EXISTS idx_account_balance_daily_trade_date ON account_balance_daily(trade_date)",
        "CREATE INDEX IF NOT EXISTS idx_transaction_dt_trade ON transaction(dt_trade)",
        
        # 추가 최적화 인덱스
        "CREATE INDEX IF NOT EXISTS idx_stock_ohlcv_daily_stock_code ON stock_ohlcv_daily(stock_code)",
        "CREATE INDEX IF NOT EXISTS idx_stock_ohlcv_current_stock_code ON stock_ohlcv_current(stock_code)",
        "CREATE INDEX IF NOT EXISTS idx_recommendation_stock_code ON recommendation(stock_code)",
    ]
    
    try:
        for idx in indices:
            cursor.execute(idx)
            print(f"  ✓ {idx.split('ON ')[1].split('(')[0]} 인덱스 생성")
        
        conn.commit()
        print("[Migration] Phase 1: All indices created successfully!")
        return True
    except Exception as e:
        print(f"[Migration] Error creating indices: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def migrate_surrogate_keys():
    """Phase 2: Surrogate Key 마이그레이션 (OHLCV 통합 제외)"""
    print("[Migration] Phase 2: Migrating to Surrogate Keys...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # account_balance_daily 마이그레이션
        print("  [1/3] account_balance_daily: Surrogate Key 추가 중...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS account_balance_daily_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                acc_cd TEXT NOT NULL,
                trade_date TEXT NOT NULL,
                cash_balance INTEGER NOT NULL DEFAULT 0,
                stock_eval_balance INTEGER NOT NULL DEFAULT 0,
                total_balance INTEGER NOT NULL DEFAULT 0,
                return_rate REAL NOT NULL DEFAULT 0.0,
                UNIQUE(acc_cd, trade_date),
                FOREIGN KEY(acc_cd) REFERENCES account(acc_cd)
            )
        """)
        
        # 기존 데이터 마이그레이션
        cursor.execute("""
            INSERT INTO account_balance_daily_new 
            SELECT NULL, acc_cd, trade_date, cash_balance, stock_eval_balance, total_balance, return_rate
            FROM account_balance_daily
        """)
        
        # 기존 테이블 삭제 및 이름 변경
        cursor.execute("DROP TABLE IF EXISTS account_balance_daily")
        cursor.execute("ALTER TABLE account_balance_daily_new RENAME TO account_balance_daily")
        print("    ✓ account_balance_daily 마이그레이션 완료")
        
        # stock 마이그레이션
        print("  [2/3] stock: Surrogate Key 추가 중...")
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                acc_cd TEXT NOT NULL,
                quantity INTEGER NOT NULL,
                avg_price INTEGER NOT NULL,
                current_price INTEGER NOT NULL DEFAULT 0,
                purchase_amount INTEGER NOT NULL DEFAULT 0,
                UNIQUE(stock_code, acc_cd),
                FOREIGN KEY(stock_code) REFERENCES stock_cache(stock_code),
                FOREIGN KEY(acc_cd) REFERENCES account(acc_cd)
            )
        """)
        
        cursor.execute("""
            INSERT INTO stock_new 
            SELECT NULL, stock_code, acc_cd, quantity, avg_price, current_price, purchase_amount
            FROM stock
        """)
        
        cursor.execute("DROP TABLE IF EXISTS stock")
        cursor.execute("ALTER TABLE stock_new RENAME TO stock")
        print("    ✓ stock 마이그레이션 완료")
        
        # OHLCV 테이블 Surrogate Key 추가
        print("  [3/3] stock_ohlcv_daily, stock_ohlcv_current: Surrogate Key 추가 중...")
        
        # stock_ohlcv_daily에 id 컬럼 추가
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_ohlcv_daily_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                trade_date TEXT NOT NULL,
                open_price INTEGER NOT NULL,
                high_price INTEGER NOT NULL,
                low_price INTEGER NOT NULL,
                close_price INTEGER NOT NULL,
                volume INTEGER NOT NULL,
                trading_value INTEGER NOT NULL DEFAULT 0,
                fluctuation_rate REAL NOT NULL DEFAULT 0.0,
                change_price INTEGER NOT NULL DEFAULT 0,
                change_price_code TEXT,
                dt_updated TEXT NOT NULL,
                UNIQUE(stock_code, trade_date),
                FOREIGN KEY(stock_code) REFERENCES stock_cache(stock_code)
            )
        """)
        
        cursor.execute("""
            INSERT INTO stock_ohlcv_daily_new 
            SELECT NULL, stock_code, trade_date, open_price, high_price, low_price, close_price,
                   volume, trading_value, fluctuation_rate, change_price, change_price_code, dt_updated
            FROM stock_ohlcv_daily
        """)
        
        cursor.execute("DROP TABLE IF EXISTS stock_ohlcv_daily")
        cursor.execute("ALTER TABLE stock_ohlcv_daily_new RENAME TO stock_ohlcv_daily")
        
        # stock_ohlcv_current에 id 컬럼 추가
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS stock_ohlcv_current_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                stock_code TEXT NOT NULL,
                trade_date TEXT NOT NULL,
                open_price INTEGER NOT NULL,
                high_price INTEGER NOT NULL,
                low_price INTEGER NOT NULL,
                close_price INTEGER NOT NULL,
                volume INTEGER NOT NULL,
                trading_value INTEGER NOT NULL DEFAULT 0,
                fluctuation_rate REAL NOT NULL DEFAULT 0.0,
                change_price INTEGER NOT NULL DEFAULT 0,
                change_price_code TEXT,
                dt_updated TEXT NOT NULL,
                UNIQUE(stock_code, trade_date),
                FOREIGN KEY(stock_code) REFERENCES stock_cache(stock_code)
            )
        """)
        
        cursor.execute("""
            INSERT INTO stock_ohlcv_current_new 
            SELECT NULL, stock_code, trade_date, open_price, high_price, low_price, close_price,
                   volume, trading_value, fluctuation_rate, change_price, change_price_code, dt_updated
            FROM stock_ohlcv_current
        """)
        
        cursor.execute("DROP TABLE IF EXISTS stock_ohlcv_current")
        cursor.execute("ALTER TABLE stock_ohlcv_current_new RENAME TO stock_ohlcv_current")
        
        print("    ✓ OHLCV 테이블 Surrogate Key 추가 완료")
        
        conn.commit()
        print("[Migration] Phase 2: Surrogate Key 마이그레이션 완료!")
        return True
        
    except Exception as e:
        print(f"[Migration] Phase 2 Error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


def migrate_soft_delete_indices():
    """Phase 2: Soft Delete 인덱스 추가"""
    print("[Migration] Phase 2: Adding Soft Delete indices...")
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        indices = [
            "CREATE INDEX IF NOT EXISTS idx_account_is_active ON account(dt_deleted) WHERE dt_deleted IS NULL",
            "CREATE INDEX IF NOT EXISTS idx_stock_cache_is_active ON stock_cache(dt_deleted) WHERE dt_deleted IS NULL",
            "CREATE INDEX IF NOT EXISTS idx_transaction_is_active ON transaction(dt_deleted) WHERE dt_deleted IS NULL",
            "CREATE INDEX IF NOT EXISTS idx_transaction_cash_is_active ON transaction_cash(dt_deleted) WHERE dt_deleted IS NULL",
            "CREATE INDEX IF NOT EXISTS idx_recommendation_is_active ON recommendation(dt_deleted) WHERE dt_deleted IS NULL",
        ]
        
        for idx in indices:
            cursor.execute(idx)
            table_name = idx.split('ON ')[1].split('(')[0]
            print(f"  ✓ {table_name} soft delete 인덱스 생성")
        
        conn.commit()
        print("[Migration] Phase 2: Soft Delete indices created successfully!")
        return True
    except Exception as e:
        print(f"[Migration] Phase 2 Error: {e}")
        conn.rollback()
        return False
    finally:
        conn.close()


if __name__ == "__main__":
    run_migrations()
    add_performance_indices()
    
    # Phase 2: Surrogate Key 및 Soft Delete 인덱스
    print("\n" + "="*60)
    print("[Migration] Phase 2 마이그레이션 시작...")
    print("="*60)
    print("[Migration] ⚠️  OHLCV 테이블 통합은 원복됨 (별도 테이블 유지)")
    migrate_surrogate_keys()
    migrate_soft_delete_indices()
    print("[Migration] 모든 마이그레이션이 완료되었습니다!")

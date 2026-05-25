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
                    dt_del = datetime.strptime(dt_del, "%Y-%m-%d %H:%M:%S.%f")
                except ValueError:
                    try:
                        dt_del = datetime.strptime(dt_del, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        dt_del = None

            dt_cre = d.get("dt_created")
            if isinstance(dt_cre, str):
                try:
                    dt_cre = datetime.strptime(dt_cre, "%Y-%m-%d %H:%M:%S.%f")
                except ValueError:
                    dt_cre = datetime.utcnow()
            else:
                dt_cre = datetime.utcnow()

            new_acc = Account(
                acc_cd=d["acc_cd"],
                acc_nm=d["acc_nm"],
                acc_company_nm=d.get("acc_company_nm", "미래에셋"),
                acc_order=d.get("acc_order", 1),
                cash_balance=int(d.get("cash_balance", 0)),
                initial_cash=int(d.get("initial_cash", 0)),
                dt_created=dt_cre,
                dt_deleted=dt_del,
            )
            db.merge(new_acc)

        # 2. StockCache
        for d in cache_stocks_data:
            dt_c = d.get("dt_cached")
            if isinstance(dt_c, str):
                try:
                    dt_c = datetime.strptime(dt_c, "%Y-%m-%d %H:%M:%S.%f")
                except ValueError:
                    dt_c = datetime.utcnow()
            else:
                dt_c = datetime.utcnow()

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
                    dt_t = datetime.strptime(dt_t, "%Y-%m-%d %H:%M:%S.%f")
                except ValueError:
                    try:
                        dt_t = datetime.strptime(dt_t, "%Y-%m-%d %H:%M:%S")
                    except ValueError:
                        dt_t = datetime.utcnow()
            else:
                dt_t = datetime.utcnow()

            # Just in case cache doesn't exist
            if not db.query(StockCache).filter_by(stock_code=d["code"]).first():
                db.merge(
                    StockCache(
                        stock_code=d["code"],
                        stock_name=d["name"],
                        dt_cached=datetime.utcnow(),
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
                        dt_cached=datetime.utcnow(),
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
                        dt_cached=datetime.utcnow(),
                    )
                )
                db.commit()

            new_rec = Recommendation(
                stock_code=d["code"],
                tag=d["tag"],
                reason=d["reason"],
                score=d["score"],
                dt_recommended=datetime.utcnow(),
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


if __name__ == "__main__":
    run_migrations()

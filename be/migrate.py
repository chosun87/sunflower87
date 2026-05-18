import os
import sqlite3

DB_PATH = "sunflower87.db"


def run_migrations():
    """sqlite3 데이터베이스의 스키마 점진적 진화(ALTER TABLE)를 점검하고 안전히 적용합니다."""
    print("🚀 Starting database schema migrations...")
    if not os.path.exists(DB_PATH):
        print(
            "ℹ️ Database file does not exist yet. "
            "It will be created by SQLAlchemy init_db."
        )
        return

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    try:
        # 1. account 테이블 initial_cash 컬럼 추가 검증
        cursor.execute("PRAGMA table_info(account)")
        acc_cols = [row[1] for row in cursor.fetchall()]
        if acc_cols and "initial_cash" not in acc_cols:
            cursor.execute(
                "ALTER TABLE account ADD COLUMN initial_cash INTEGER DEFAULT 0"
            )
            print("✅ Migration: Added initial_cash column to account.")

        # 2. transactions 테이블 tax_fee 컬럼 추가 검증
        cursor.execute("PRAGMA table_info(transactions)")
        tx_cols = [row[1] for row in cursor.fetchall()]
        if tx_cols and "tax_fee" not in tx_cols:
            cursor.execute(
                "ALTER TABLE transactions ADD COLUMN tax_fee INTEGER DEFAULT 0"
            )
            print("✅ Migration: Added tax_fee column to transactions.")

        # 3. stocks 테이블 purchase_amount 컬럼 추가 검증
        cursor.execute("PRAGMA table_info(stocks)")
        stocks_cols = [row[1] for row in cursor.fetchall()]
        if stocks_cols and "purchase_amount" not in stocks_cols:
            cursor.execute(
                "ALTER TABLE stocks ADD COLUMN "
                "purchase_amount REAL DEFAULT 0.0"
            )
            print("✅ Migration: Added purchase_amount column to stocks.")

        conn.commit()
        print("🎉 Database migration completed successfully.")
    except Exception as e:
        conn.rollback()
        print(f"❌ Migration failed: {e}")
    finally:
        conn.close()


if __name__ == "__main__":
    run_migrations()

from database import SessionLocal, Account
from services.daily_balance_service import sync_daily_balances_for_account

db = SessionLocal()
try:
    accounts = db.query(Account).filter(Account.dt_deleted.is_(None)).all()
    for acc in accounts:
        print(f"Syncing {acc.acc_cd}...")
        result = sync_daily_balances_for_account(db, acc.acc_cd)
        print(result)
finally:
    db.close()

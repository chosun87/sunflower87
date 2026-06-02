from database import Account, SessionLocal
from services.account_balance_daily_service import sync_account_balance_daily

db = SessionLocal()
try:
    accounts = db.query(Account).filter(Account.dt_deleted.is_(None)).all()
    for acc in accounts:
        print(f"Syncing {acc.acc_cd}...")
        result = sync_account_balance_daily(db, acc.acc_cd)
        print(result)
finally:
    db.close()

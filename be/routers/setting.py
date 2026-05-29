from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import Account, AccountDailyBalance, get_db
from services.daily_balance_service import sync_account_daily_balance

router = APIRouter(prefix="/api/settings", tags=["Setting"])


@router.post("/sync-daily-balance", response_model=dict)
def manual_sync_daily_balance(db: Session = Depends(get_db)):
    accounts = db.query(Account).filter(Account.dt_deleted.is_(None)).all()
    results = []

    # Force recalculation by clearing the existing daily balance cache
    db.query(AccountDailyBalance).delete()
    db.commit()

    for acc in accounts:
        try:
            res = sync_account_daily_balance(db, acc.acc_cd)
            results.append({"acc_cd": acc.acc_cd, "result": res})
        except Exception as e:
            results.append(
                {"acc_cd": acc.acc_cd, "result": {"status": "error", "message": str(e)}}
            )
    return {"status": "success", "data": results}

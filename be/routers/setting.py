from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import get_db, Account
from services.daily_balance_service import sync_daily_balances_for_account

router = APIRouter(prefix="/api/settings", tags=["Setting"])

@router.post("/sync-daily-balance", response_model=dict)
def manual_sync_daily_balance(db: Session = Depends(get_db)):
    accounts = db.query(Account).filter(Account.dt_deleted.is_(None)).all()
    results = []
    for acc in accounts:
        try:
            res = sync_daily_balances_for_account(db, acc.acc_cd)
            results.append({"acc_cd": acc.acc_cd, "result": res})
        except Exception as e:
            results.append({"acc_cd": acc.acc_cd, "result": {"status": "error", "message": str(e)}})
    return {"status": "success", "data": results}

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database import Account, get_db
from services.account_balance_daily_service import sync_account_balance_daily

router = APIRouter(prefix="/api/settings", tags=["Setting"])


@router.post("/sync_account_balance_daily", response_model=dict)
def manual_sync_account_balance_daily(db: Session = Depends(get_db)):
    accounts = db.query(Account).filter(Account.dt_deleted.is_(None)).all()
    results = []

    for acc in accounts:
        try:
            res = sync_account_balance_daily(db, acc.acc_cd)
            results.append({"acc_cd": acc.acc_cd, "result": res})
        except Exception as e:
            results.append(
                {"acc_cd": acc.acc_cd, "result": {"status": "error", "message": str(e)}}
            )
    return {"status": "success", "data": results}

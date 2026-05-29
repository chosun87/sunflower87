from fastapi import APIRouter, BackgroundTasks, Depends
from sqlalchemy.orm import Session

import schemas
from database import Account, SessionLocal, get_db
from services.daily_balance_service import sync_account_daily_balance
from services.dashboard_service import get_dashboard_kpi

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


def run_daily_sync_bg():
    db = SessionLocal()
    try:
        accounts = db.query(Account).filter(Account.dt_deleted.is_(None)).all()
        for acc in accounts:
            sync_account_daily_balance(db, acc.acc_cd)
    except Exception as e:
        print(f"Background daily sync failed: {e}")
    finally:
        db.close()


@router.get("/kpi", response_model=schemas.DashboardKPIResponse)
def get_kpi(
    background_tasks: BackgroundTasks, acc_cd: str = None, db: Session = Depends(get_db)
):
    background_tasks.add_task(run_daily_sync_bg)
    return get_dashboard_kpi(db, acc_cd)

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

import schemas
from database import get_db
from services.dashboard_service import get_dashboard_kpi

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

@router.get("/kpi", response_model=schemas.DashboardKPIResponse)
def get_kpi(acc_cd: str = None, db: Session = Depends(get_db)):
    return get_dashboard_kpi(db, acc_cd)

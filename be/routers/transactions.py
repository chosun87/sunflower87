from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.orm import Session

from database import get_db
from schemas import ErrorResponse, TransactionCreate
from services.transaction_service import add_transaction as add_transaction_service
from services.transaction_service import (
    delete_transaction as delete_transaction_service,
)
from services.transaction_service import (
    get_transaction_history as get_transaction_history_service,
)
from services.transaction_service import (
    update_transaction as update_transaction_service,
)

router = APIRouter(prefix="/api/transactions", tags=["Transaction"])


@router.get(
    "",
    summary="전체 매매 거래 내역 조회 API",
    description="데이터베이스에 기록된 모든 매수/매도 거래 이력을 거래일시 역순(date DESC)으로 조회하여 반환합니다.",
)
def get_transaction_history(
    acc_cd: Optional[str] = Query(None, description="계좌 식별자 (예: A001)"),
    stock_code: Optional[str] = Query(None, description="종목 코드 (예: 005930)"),
    start_date: Optional[str] = Query(None, description="조회 시작일 (YYYY-MM-DD)"),
    end_date: Optional[str] = Query(None, description="조회 종료일 (YYYY-MM-DD)"),
    db: Session = Depends(get_db),
):
    """최근 거래일시 순(date DESC)으로 전체 매매 거래 내역을 반환합니다."""
    return {
        "status": "success",
        "data": get_transaction_history_service(
            db, acc_cd, stock_code, start_date, end_date
        ),
    }


@router.post(
    "/add",
    summary="매매 거래 기록 추가 및 자산 실시간 재계산 API",
    description=(
        "신규 매수/매도 거래를 장부에 기록하고, 해당 계좌의 예수금 및 보유 주식 잔고를 "
        "연대기 순으로 무결성 안전하게 재산출하여 DB에 실시간 반영합니다."
    ),
    responses={
        400: {
            "model": ErrorResponse,
            "description": "매수 잔고(예수금) 부족 또는 과매도 수량 미달 등 유효성 실패",
        },
        404: {
            "model": ErrorResponse,
            "description": "해당 식별자의 계좌(Account)를 찾을 수 없음",
        },
    },
)
def add_transaction(
    tx_input: TransactionCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    """매매 거래 기록을 추가하고 지정된 계좌의 자산을 연대기적으로 재계산합니다."""
    return add_transaction_service(db, tx_input, background_tasks)


@router.delete(
    "/{tx_id}",
    summary="거래 기록 삭제 및 자산 역산 복원 API",
    description=(
        "지정된 고유 ID의 거래 데이터를 장부에서 안전하게 제거하고, 기존 거래 내역을 처음부터 "
        "다시 누적 추적함으로써 해당 계좌의 자산을 거래 이전 상태로 역산하여 원상복귀시킵니다."
    ),
    responses={
        400: {
            "model": ErrorResponse,
            "description": (
                "삭제 후 역산 과정에서 자산이 마이너스가 되는 등의 역산 유효성 실패"
            ),
        },
        404: {
            "model": ErrorResponse,
            "description": "삭제 요청한 ID의 거래 기록을 찾을 수 없음",
        },
    },
)
def delete_transaction(tx_id: int, db: Session = Depends(get_db)):
    """지정된 거래를 삭제하고 해당 계좌의 포트폴리오를 역산(Rollback)하여 원상복귀시킵니다."""
    return delete_transaction_service(db, tx_id)


@router.put(
    "/{tx_id}",
    summary="거래 수정 및 포트폴리오 안전 재반영 API",
    description=(
        "기존 거래 내역 데이터를 완전히 수정하며, 기존 계좌와 신규 계좌의 예수금 및 "
        "주식 포트폴리오 자산을 분리하여 연대기적으로 완벽하게 재산출 및 복원 처리합니다."
    ),
    responses={
        400: {
            "model": ErrorResponse,
            "description": (
                "수정 후 기존/신규 계좌의 자산이 마이너스가 되는 등의 역산 유효성 실패"
            ),
        },
        404: {
            "model": ErrorResponse,
            "description": "수정 요청한 ID의 거래 기록 또는 관련 계좌를 찾을 수 없음",
        },
    },
)
def update_transaction(
    tx_id: int, tx_input: TransactionCreate, db: Session = Depends(get_db)
):
    """기존 거래 데이터를 변경하고, 기존 계좌와 신규 계좌의 포트폴리오를 트랜잭션 안전하게 동시 역산 및 재반영합니다."""
    return update_transaction_service(db, tx_id, tx_input)

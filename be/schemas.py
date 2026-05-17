from typing import Optional
from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    filename: str = Field(
        ...,
        description=(
            "저장할 마크다운 태스크 파일명 "
            "(예: TASK-04-SWAGGER_DOCUMENTATION_BE_R1.md)"
        ),
        examples=["TASK-04-SWAGGER_DOCUMENTATION_BE_R1.md"],
    )
    content: str = Field(
        ...,
        description="마크다운 태스크 파일에 기록할 상세 지침/내용",
        examples=["# TASK-04 상세..."],
    )


class TransactionCreate(BaseModel):
    date: Optional[str] = Field(
        None,
        description="거래일시 문자열 (포맷: YYYY-MM-DD HH:MM:SS 또는 ISO 8601)",
        examples=["2026-05-17 23:25:46"],
    )
    type: str = Field(
        ...,
        description="매매 구분 (BUY: 매수, SELL: 매도)",
        examples=["BUY"],
    )
    code: str = Field(
        ...,
        description="종목/ETF 6자리 고유 코드",
        examples=["005930"],
    )
    name: str = Field(
        ...,
        description="종목/ETF 명칭",
        examples=["삼성전자"],
    )
    quantity: int = Field(
        ...,
        description="매매 수량 (양의 정수)",
        examples=[10],
    )
    price: int = Field(
        ...,
        description="매매 단가 (양의 정수)",
        examples=[77000],
    )
    acc_cd: Optional[str] = Field(
        "",
        description="account 테이블의 acc_cd 참조 키",
        examples=["A001"],
    )
    acc_code: Optional[str] = Field(
        "",
        description="account 테이블의 acc_cd 참조 키 (호환용)",
        examples=["A001"],
    )


class ErrorResponse(BaseModel):
    detail: str = Field(
        ...,
        description="에러 및 예외 상세 설명 메세지",
        examples=["Insufficient cash balance. Required: 770k, Available: 0."],
    )

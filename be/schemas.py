from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field, validator


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
        gt=0,
        description="매매 수량 (양의 정수)",
        examples=[10],
    )
    price: int = Field(
        ...,
        gt=0,
        description="매매 단가 (양의 정수)",
        examples=[77000],
    )
    acc_cd: Optional[str] = Field(
        "",
        description="account 테이블의 acc_cd 참조 키",
        examples=["A001"],
    )
    tax_fee: Optional[int] = Field(
        0,
        ge=0,
        description="거래 세금 및 수수료 (기본값: 0)",
        examples=[1500],
    )

    @validator("date", pre=True, always=True)
    def parse_and_normalize_date(cls, v):
        """다양한 유형의 날짜 입력을 파싱하고 YYYY-MM-DD HH:MM:SS 표준 포맷으로 자동 정규화합니다."""
        if not v:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if isinstance(v, datetime):
            return v.strftime("%Y-%m-%d %H:%M:%S")

        v_str = str(v).strip()
        # ISO 'Z' 대응
        if v_str.endswith("Z"):
            v_str = v_str[:-1] + "+00:00"

        # 1. 표준 포맷
        try:
            parsed = datetime.strptime(v_str, "%Y-%m-%d %H:%M:%S")
            return parsed.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass

        # 2. ISO 8601 포맷
        try:
            parsed = datetime.fromisoformat(v_str)
            return parsed.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass

        # 3. 단순 일자 포맷
        try:
            parsed = datetime.strptime(v_str, "%Y-%m-%d")
            return parsed.strftime("%Y-%m-%d 00:00:00")
        except ValueError:
            pass

        # 폴백
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class ErrorResponse(BaseModel):
    detail: str = Field(
        ...,
        description="에러 및 예외 상세 설명 메세지",
        examples=["Insufficient cash balance. Required: 770k, Available: 0."],
    )

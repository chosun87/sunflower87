from datetime import datetime
from typing import Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field, validator

from constants import CashType, TradeType

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    status: str
    message: Optional[str] = None
    data: Optional[T] = None
    results: Optional[List[T]] = None


class TaskCreate(BaseModel):
    filename: str = Field(..., description="마크다운 파일명")
    content: str = Field(..., description="내용")


# --- Account ---
class AccountBase(BaseModel):
    acc_nm: str
    acc_company_nm: str
    acc_order: Optional[int] = 1
    initial_cash: Optional[int] = 0


class AccountCreate(AccountBase):
    acc_cd: str


class AccountUpdate(BaseModel):
    acc_nm: Optional[str] = None
    initial_cash: Optional[int] = None
    acc_order: Optional[int] = None


class AccountResponse(AccountBase):
    acc_cd: str
    cash_balance: int
    dt_created: datetime
    dt_deleted: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- Transaction (Stock) ---
class TransactionCreate(BaseModel):
    acc_cd: str
    dt_trade: Optional[str] = None
    trade_type: TradeType
    stock_code: str
    quantity: int = Field(..., gt=0)
    price: int = Field(..., gt=0)
    tax_fee: Optional[int] = 0

    @validator("dt_trade", pre=True, always=True)
    def parse_and_normalize_date(cls, v):
        if not v:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        v_str = str(v).strip()
        if v_str.endswith("Z"):
            v_str = v_str[:-1] + "+00:00"
        try:
            parsed = datetime.strptime(v_str, "%Y-%m-%d %H:%M:%S")
            return parsed.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass
        try:
            parsed = datetime.fromisoformat(v_str)
            return parsed.strftime("%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass
        try:
            parsed = datetime.strptime(v_str, "%Y-%m-%d")
            return parsed.strftime("%Y-%m-%d 00:00:00")
        except ValueError:
            pass
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class TransactionUpdate(BaseModel):
    dt_trade: Optional[str] = None
    trade_type: Optional[TradeType] = None
    quantity: Optional[int] = None
    price: Optional[int] = None
    tax_fee: Optional[int] = None


class TransactionResponse(BaseModel):
    id: int
    acc_cd: str
    acc_nm: Optional[str] = None  # 동적 조인용
    acc_company_nm: Optional[str] = None  # 동적 조인용
    dt_trade: datetime
    trade_type: str
    stock_code: str
    stock_name: Optional[str] = None  # 동적 조인용
    quantity: int
    price: int
    tax_fee: int
    dt_deleted: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- TransactionCash ---
class TransactionCashCreate(BaseModel):
    acc_cd: str
    dt_cash: Optional[str] = None
    cash_type: CashType
    amount: int
    description: Optional[str] = None

    @validator("dt_cash", pre=True, always=True)
    def parse_cash_date(cls, v):
        if not v:
            return datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return v  # 실제론 정밀 파싱 필요하나 간략화


class TransactionCashResponse(BaseModel):
    id: int
    acc_cd: str
    dt_cash: datetime
    cash_type: str
    amount: int
    description: Optional[str] = None
    dt_deleted: Optional[datetime] = None

    class Config:
        from_attributes = True


# --- AccountDailyBalance ---
class AccountDailyBalanceResponse(BaseModel):
    acc_cd: str
    trade_date: str
    cash_balance: int
    stock_eval_balance: int
    total_balance: int
    return_rate: float

    class Config:
        from_attributes = True


# --- Stock ---
class StockResponse(BaseModel):
    stock_code: str
    acc_cd: str
    stock_name: Optional[str] = None
    quantity: int
    avg_price: int
    current_price: int
    purchase_amount: int

    class Config:
        from_attributes = True


class StockCreate(BaseModel):
    acc_cd: str
    stock_code: str
    quantity: int
    avg_price: int
    current_price: int
    purchase_amount: int


# --- StockCache ---
class StockCacheResponse(BaseModel):
    stock_code: str
    stock_name: str
    market: Optional[str] = None

    class Config:
        from_attributes = True


# --- StockOHLCVCache ---
class StockOHLCVResponse(BaseModel):
    stock_code: str
    trade_date: str
    open_price: int
    high_price: int
    low_price: int
    close_price: int
    volume: int
    trading_value: int
    fluctuation_rate: float

    class Config:
        from_attributes = True


class StockOHLCVCreate(StockOHLCVResponse):
    pass


# --- Recommendation ---
class RecommendationResponse(BaseModel):
    stock_code: str
    stock_name: Optional[str] = None
    tag: str
    reason: str
    score: int
    dt_recommended: datetime
    dt_deleted: Optional[datetime] = None
    investor_score: Optional[int] = None

    class Config:
        from_attributes = True


class RecommendationCreate(BaseModel):
    stock_code: str
    tag: str
    reason: str
    score: int


class RecommendationUpdate(BaseModel):
    tag: Optional[str] = None
    reason: Optional[str] = None
    score: Optional[int] = None

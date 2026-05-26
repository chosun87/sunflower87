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


# --- Dashboard KPI ---
class DashboardKPIPeriod(BaseModel):
    profit: int
    return_rate: float


class DashboardKPITotal(BaseModel):
    total_asset: int
    total_principal: int
    profit: int
    return_rate: float


class DashboardKPIData(BaseModel):
    today: DashboardKPIPeriod
    this_month: DashboardKPIPeriod
    this_year: DashboardKPIPeriod
    total: DashboardKPITotal


class DashboardKPIResponse(BaseModel):
    status: str
    data: DashboardKPIData


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


class TransactionCashUpdate(BaseModel):
    dt_cash: Optional[str] = None
    cash_type: Optional[CashType] = None
    amount: Optional[int] = None
    description: Optional[str] = None


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
class AccountDailyBalanceCreate(BaseModel):
    trade_date: str
    cash_balance: int = 0
    stock_eval_balance: int = 0
    total_balance: int = 0
    return_rate: float = 0.0


class AccountDailyBalanceUpdate(BaseModel):
    cash_balance: Optional[int] = None
    stock_eval_balance: Optional[int] = None
    total_balance: Optional[int] = None
    return_rate: Optional[float] = None


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


class StockUpdate(BaseModel):
    quantity: Optional[int] = None
    avg_price: Optional[int] = None
    current_price: Optional[int] = None
    purchase_amount: Optional[int] = None


class StockCreate(BaseModel):
    acc_cd: str
    stock_code: str
    quantity: int
    avg_price: int
    current_price: int
    purchase_amount: int


# --- StockCache ---
class StockCacheCreate(BaseModel):
    stock_code: str
    stock_name: str
    market: Optional[str] = None


class StockCacheUpdate(BaseModel):
    stock_name: Optional[str] = None
    market: Optional[str] = None


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


class StockOHLCVCreate(BaseModel):
    stock_code: str
    trade_date: str
    open_price: int
    high_price: int
    low_price: int
    close_price: int
    volume: int
    trading_value: int = 0
    fluctuation_rate: float = 0.0


class StockOHLCVUpdate(BaseModel):
    open_price: Optional[int] = None
    high_price: Optional[int] = None
    low_price: Optional[int] = None
    close_price: Optional[int] = None
    volume: Optional[int] = None
    trading_value: Optional[int] = None
    fluctuation_rate: Optional[float] = None


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

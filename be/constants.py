from enum import Enum


class TradeType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"


class CashType(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"
    INTEREST = "INTEREST"
    DIVIDEND = "DIVIDEND"
    FEE = "FEE"


class MarketType(str, Enum):
    KOSPI = "KOSPI"
    KOSDAQ = "KOSDAQ"
    KONEX = "KONEX"
    ETF = "ETF"


class ChangePriceCode(str, Enum):
    상한 = "1"
    상승 = "2"
    보합 = "3"
    하한 = "4"
    하락 = "5"

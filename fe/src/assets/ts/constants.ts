// src/constants.ts

export const CASH_TYPE = {
  DEPOSIT: { code: 'DEPOSIT', label: '입금', color: 'text-red-500' },
  WITHDRAW: { code: 'WITHDRAW', label: '출금', color: 'text-blue-500' },
  INTEREST: { code: 'INTEREST', label: '이자', color: 'text-green-500' },
  DIVIDEND: { code: 'DIVIDEND', label: '배당금', color: 'text-purple-500' },
  FEE: { code: 'FEE', label: '수수료', color: 'text-gray-500' },
} as const;

// Select 컴포넌트(Dropdown)를 위한 옵션 배열
export const CASH_TYPE_OPTIONS = Object.values(CASH_TYPE).map((item) => ({
  label: item.label,
  value: item.code,
}));

// 거래 유형 (Trade Type)
export const TRADE_TYPE = {
  BUY: { code: 'BUY', label: '매수', color: 'text-red-500' },
  SELL: { code: 'SELL', label: '매도', color: 'text-blue-500' },
} as const;

export const TRADE_TYPE_OPTIONS = Object.values(TRADE_TYPE).map((item) => ({
  label: item.label,
  value: item.code,
}));

// 시장 유형 (Market Type)
export const MARKET_TYPE = {
  KOSPI: { code: 'KOSPI', label: 'KOSPI' },
  KOSDAQ: { code: 'KOSDAQ', label: 'KOSDAQ' },
  KONEX: { code: 'KONEX', label: 'KONEX' },
  ETF: { code: 'ETF', label: 'ETF' },
} as const;

export const MARKET_TYPE_OPTIONS = Object.values(MARKET_TYPE).map((item) => ({
  label: item.label,
  value: item.code,
}));

// 주가 변동 상태 코드 (Change Price Code)
export const CHANGE_PRICE_CODE = {
  UPPER_LIMIT: { code: '1', label: '상한', color: 'text-red-500' },
  RISING: { code: '2', label: '상승', color: 'text-red-500' },
  UNCHANGED: { code: '3', label: '보합', color: 'text-gray-500' },
  LOWER_LIMIT: { code: '4', label: '하한', color: 'text-blue-500' },
  FALLING: { code: '5', label: '하락', color: 'text-blue-500' },
} as const;

export const CHANGE_PRICE_CODE_OPTIONS = Object.values(CHANGE_PRICE_CODE).map((item) => ({
  label: item.label,
  value: item.code,
}));

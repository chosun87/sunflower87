# 대시보드 최근 거래 내역 API 연동

## 변경 내용
`LatestTrStockList.tsx`에서 하드코딩된 Mock 데이터(`LatestTrStockData.ts`) 대신 실제 백엔드 API인 `/api/transactions`를 호출하여 최신 거래 내역 5건을 가져오도록 수정합니다.

1. **상태 관리 및 데이터 페칭**:
   - `useState`와 `useEffect`를 도입하여 컴포넌트 마운트 시 `get('/api/transactions')` 호출.
2. **응답 데이터 매핑**:
   - `TransactionStock.tsx`와 동일한 방식으로 API 응답(`tx.dt_trade`, `tx.trade_type`, `tx.stock_name`, `tx.quantity` 등)을 화면 컴포넌트에서 사용하는 프로퍼티(`date`, `type`, `asset`, `amount`, `price`)로 매핑.
3. **5건 제한**:
   - 받아온 데이터 목록 중 앞에서부터 최대 5개만 잘라내어(`slice(0, 5)`) 테이블에 전달.

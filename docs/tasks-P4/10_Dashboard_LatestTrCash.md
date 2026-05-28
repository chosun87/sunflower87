# 대시보드 최근 입출금 내역 카드 추가

## 작업 내용
최근 주식 매매 내역 (`LatestTrStockList`)과 유사한 스타일의 **최근 입출금 내역 카드(`LatestTrCash`)**를 생성하여 대시보드에 배치합니다.

1. **데이터 인터페이스 생성**:
   - `fe/src/data/LatestTrCashData.ts` 파일을 생성하여 `TransactionCash` 인터페이스를 정의합니다.
2. **컴포넌트 생성**:
   - `fe/src/components/Dashboard/LatestTrCash.tsx` 컴포넌트를 생성합니다.
   - API `/api/transactions_cash`에서 최근 입출금 데이터를 불러옵니다.
   - `MAXROW` 제한(4개)을 두어 최근 내역만 표시합니다.
   - 패널 헤더 우측의 '전체화면' 버튼 클릭 시 `/transactionCash` 화면으로 이동합니다.
3. **대시보드 레이아웃 수정**:
   - `Dashboard.tsx`에서 '최근 매매 내역 ' 카드 우측에 '최근 입출금 내역' 카드를 배치합니다. (1열: 주식 매매 내역 , 2열: 입출금 내역)
   - 기존 우측에 있던 `DividendSummary`는 아래로 이동하거나 적절한 레이아웃에 맞게 재배치합니다.

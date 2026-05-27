# 계좌 입출금 내역 화면 FE 개발 계획서

본 계획서는 주식 매매 내역 화면(`TransactionStock.tsx`)과 동일한 UI/UX를 가지는 계좌 입출금 내역 화면의 프론트엔드(FE) 신규 개발 계획을 담고 있습니다.

## 1. 개요
현재 주식 매매 내역 화면의 구성 및 Look & Feel을 그대로 차용하여, 계좌별 현금 입출금(입금/출금/이자/배당/수수료) 내역을 관리할 수 있는 화면을 구축합니다.

## 2. 상세 개발 계획 (Proposed Changes)

### 2.1 화면 및 라우터 구성

#### [MODIFY] `fe/src/App.tsx`
- 주석 처리되어 있는 `TransactionCash` 컴포넌트 lazy loading import 구문 주석을 해제합니다.
- `<Route path="/transactionCash" element={<TransactionCash />} />` 라우트 주석을 해제하여 `/transactionCash` 경로를 활성화합니다.

#### [MODIFY] 사이드바 메뉴 컴포넌트 (`fe/src/components/Sidebar.tsx` 등)
- 좌측 네비게이션(GNB/LNB) 영역에 '계좌 입출금 내역' 메뉴 항목을 추가하고 `/transactionCash` 경로와 연결합니다.

### 2.2 신규 페이지 및 컴포넌트 개발

#### [NEW] `fe/src/pages/TransactionCash.tsx`
- **역할**: 계좌 입출금 내역 메인 페이지 컨테이너
- **구성**: 
  - `TransactionStock.tsx`와 동일한 페이지 템플릿(Page Header, Breadcrumb) 활용
  - API(`get /api/transactions_cash`) 호출 및 상태(State) 관리
  - 하위 컴포넌트(`TransactionCashCmpt`, `TrCashDialog`) 렌더링 및 이벤트 핸들링

#### [NEW] `fe/src/components/TransactionCash/TransactionCashCmpt.tsx`
- **역할**: 입출금 내역 DataTable 표시 컴포넌트
- **구성**:
  - `TransactionStockCmpt`의 디자인과 구조를 차용
  - 상단 툴바: '신규 등록' 버튼, 계좌 필터링(Dropdown)
  - 테이블 컬럼: 거래 일시(Date), 계좌명, 구분(Type: 입금/출금/이자/배당/수수료), 금액(Amount), 적요(Description)
  - 각 행의 Action 버튼: 수정(Edit), 삭제(Delete)

#### [NEW] `fe/src/components/TransactionCash/TrCashDialog.tsx`
- **역할**: 입출금 내역 신규 등록 및 수정을 위한 Modal Dialog 컴포넌트
- **구성**:
  - `TrStockDialog`에서 주식 종목 검색 기능을 제외하고 현금 거래에 맞게 폼 단순화
  - 폼 필드:
    - 계좌 선택 (Select)
    - 구분 선택 (Select: DEPOSIT, WITHDRAW, INTEREST, DIVIDEND, FEE)
    - 거래 일시 (Calendar/Date Picker)
    - 금액 (InputNumber)
    - 적요 (InputText)
  - 확인(저장)/취소 버튼 제공 및 BE API 연동(`POST` 및 `PUT`)

## 3. 검증 계획 (Verification Plan)
1. 새로운 입금 내역(예: 1,000,000원)을 다이얼로그를 통해 성공적으로 등록합니다.
2. 대시보드 및 보유 자산 화면에서 해당 계좌의 '현금 잔고(cash_balance)'가 즉시 증가했는지 확인합니다.
3. 내역을 수정하거나 삭제했을 때, 현금 잔고가 정상적으로 재계산(Rollback)되는지 확인합니다.

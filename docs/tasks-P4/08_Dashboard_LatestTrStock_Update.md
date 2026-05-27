# 대시보드 최근 거래 내역(LatestTrStockList) 수정안

## 변경 사항
1. **표시 개수 제한**: `LatestTrStockData.ts`에 임시 데이터가 4개 뿐이므로 추후 API 연동을 감안해 데이터 렌더링 시 최대 5개까지만 노출하도록 처리 (`slice(0, 5)`)
2. **패널 헤더 변경 및 전체화면 기능 대체**:
   - `CustomPanel`의 `maximizable` 속성을 제거하여 기본 제공되는 전체화면/더보기 버튼을 비활성화.
   - 커스텀 `headerTemplate`을 작성하여, 타이틀 우측에 `fa-list` (또는 `fa-expand`) 아이콘 버튼을 배치하고 클릭 시 `react-router-dom`의 `useNavigate`를 통해 `/transactionStock`(주식 매매 내역 화면)으로 이동.
   - 더보기 버튼은 템플릿에서 렌더링하지 않음으로써 자동 제거.
3. **컬럼 구성 및 순서 변경**:
   - 요구 순서: 거래일자, 구분, 종목명, 거래수량, 거래단가, 거래금액
   - `TransactionStockCmpt.tsx`의 렌더링 방식을 차용하여 `Badge`를 통한 매수/매도 구분 표시.
   - 모의 데이터 `LatestTrStockData.ts`의 `price` 타입을 `number`로 변경하여 거래금액(수량 * 단가) 계산을 용이하게 변경.

## 대상 파일
- `fe/src/data/LatestTrStockData.ts` (Mock 데이터 타입 및 포맷 수정)
- `fe/src/components/Dashboard/LatestTrStockList.tsx` (컴포넌트 로직 및 UI 수정)

# 📊 Phase-2 v1.3 요구사항 구현 계획 (ETF Soft Delete & 차트 로딩 UX)

지시서 v1.3에서 새롭게 추가되거나 변경된 요구사항을 백엔드와 프런트엔드에 반영하기 위한 상세 계획입니다.

## User Review Required

- **Soft Delete 로직 검증:** 매일 서버가 켜질 때마다 pykrx에서 가져온 KOSPI, KOSDAQ, ETF 전체 목록과 로컬 DB의 `cache_stocks`를 대조(Diff)하여, 오늘 거래소 목록에 없는 종목(상장폐지, 티커 변경 등)은 물리적으로 지우지 않고 `is_active = 0`으로 플래그만 변경하도록 `database.py`의 `init_db()`를 보강합니다. 이 방식에 동의하시나요?

## Proposed Changes

### 백엔드 (어씨베)

#### [MODIFY] be/schemas.py
- **0순위 Pydantic 무결성 검증:** `TransactionCreate` 스키마의 `quantity`와 `price` 필드에 `Field(..., gt=0)` 제약 조건을 추가하여 0 이하의 값이 들어올 경우 HTTP 422 Unprocessable Entity 에러로 원천 차단합니다.

#### [MODIFY] be/database.py
- **0.5순위 종목 마스터 Soft Delete:** `init_db()` 함수 로직 후반부에 **Diff(대조) 알고리즘**을 추가합니다. 당일 크롤링 성공 시 획득한 전체 티커 목록(KOSPI + KOSDAQ + ETF) Set과 기존 DB에 있는 전체 티커 Set을 비교하여, DB에는 있으나 크롤링 목록에 없는 티커들의 `is_active` 값을 `0`으로 업데이트(Soft Delete)합니다.

#### [MODIFY] be/routers/stocks.py
- 종목 검색 및 자동완성 API(`GET /api/stocks/search` 등)에서 `.filter(CacheStock.is_active == 1)` 조건을 추가하여, 상장폐지되거나 숨겨진 종목이 신규 검색결과에 노출되지 않도록 차단합니다. (단, 매매 내역 등 보유 현황 조회 시에는 `is_active` 여부와 상관없이 이름이 잘 매핑되도록 기존 조인/룩업 로직을 유지합니다.)

### 프런트엔드 (어씨페)

#### [MODIFY] fe/src/pages/StockDetail.jsx
- **4단계 UX 보완 (Loading Overlay):** 차트를 드래그(Pan/Zoom)하여 새로운 과거 구간 데이터를 가져오기 위해 300ms 디바운스 후 API 호출이 시작될 때, 차트 상단에 **반투명 블러(Blur) 오버레이 레이어 및 ProgressSpinner**를 띄우도록 렌더링 조건을 추가합니다. 이로써 백그라운드 데이터 패칭 중 화면이 멈춘 것처럼 보이지 않고 시각적 안정감을 제공합니다.

## Verification Plan
1. **백엔드 무결성 테스트:** `POST /api/transactions` 호출 시 `quantity: 0`을 주입하여 Pydantic 에러(422)가 발생하는지 확인합니다.
2. **Soft Delete 테스트:** 로컬 DB `cache_stocks`에 가짜 티커(예: `999999`)를 임의로 넣고 서버를 재기동한 뒤, 해당 티커의 `is_active`가 `0`으로 변환되는지 확인합니다.
3. **UX 오버레이 테스트:** 프런트엔드 차트 화면에서 과거로 스크롤 시 반투명 로딩 스피너가 차트 위에 은은하게 뜨는지 시각적으로 검수합니다.

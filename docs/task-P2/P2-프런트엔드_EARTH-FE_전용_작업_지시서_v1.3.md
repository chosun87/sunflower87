# 📊 Phase-2 프런트엔드 EARTH-FE(어씨페) 전용 작업 지시서 (v1.3)

- **작성자:** 기획자 MOON(무니)
- **수신자:** 프런트엔드 개발자 EARTH-FE(어씨페)
- **프로젝트 명:** sunflower87 통합 자산 관리 대시보드 고도화
- **우선순위 지표:** 0순위(리팩토링 구조 유지) → 1단계(KRX 컬러) → 2단계(매매 검색 UI) → 3단계(보유 필터링) → 4단계(차트 기간 이동 및 로딩 최적화)

---

## 📌 0. 코어 아키텍처 원장 준수 사항 (영구 지침)
- **5대 관심사 분리(SoC):** `AssetSummaryCard`, `AIRecommendationSection`, `AssetDetailTab`, `TransactionHistoryTab`, `TransactionDialog` 5분할 구조 및 `React.lazy` 동적 임포트 전환 구조를 원천 보존합니다.
- **성능 방어 결계:** 연산 부하가 큰 합산 데이터는 무조건 `useMemo` 내부에서 처리하여 렌더링 오버헤드를 0%로 통제합니다.
- **무결성 강제:** 백엔드 송출 직전 데이터는 반드시 `Math.abs()`로 감싸 양수 상태를 보장합니다.

---

## ✨ 0순위. 리팩토링 구조 유지 및 활용
- **조치 사항:** 최근 AI 리팩토링으로 완성된 공통 API 모듈(`fe/src/api/index.js`)을 적극 활용하여 신규 API 호출을 구현하고, 인라인 스타일이 아닌 CSS 클래스(`text-buy`, `text-sell` 등) 기반의 스타일링 일관성을 완벽히 조화시키십시오.

---

## 📌 1단계. UI/UX 전역 컬러 시스템 교체 (KRX 규격)
- **내용:** 기존 글로벌 파이낸스 컬러 룰을 파쇄하고, 한국 주식 시장 표준(KRX) 컬러 시스템으로 전면 교체합니다.
- **상세 요구사항:**
  - **상승 / 매수 / 평가이익 / 자산 증가:** 빨간색 계열(`var(--red-600)` 등) 적용
  - **하락 / 매도 / 평가손실 / 자산 감소:** 파란색 계열(`var(--blue-600)` 등) 적용
  - 최근 리팩토링된 공통 CSS 클래스(예: `text-buy`, `text-sell`)의 테마 컬러 정의를 수정하여 대시보드 전역에 KRX 규격이 일괄 반영되도록 조치하십시오.

---

## 📌 2단계. 거래 내역 검색 UI 구현 (`TransactionHistoryTab`)
- **상세 요구사항:**
  - `TransactionHistoryTab` 상단 영역에 PrimeReact `Dropdown`(계좌 필터), `AutoComplete` 또는 `InputText`(종목 필터), `Calendar(selectionMode="range")`(기간 필터) 폼을 배치하십시오.
  - 사용자가 검색 조건을 변경할 때마다 공통 API 모듈(`fe/src/api/index.js`)을 통해 백엔드 확장 API를 호출하고 DataTable을 기민하게 동기화하십시오.

---

## 📌 3단계. 계좌별 보유 종목 목록 필터링 및 투명도 처리 (`AssetDetailTab`)
- **상세 요구사항:**
  - 상단에 PrimeReact `RadioButton` 그룹을 신설하여 **[전체 종목] / [보유 중 종목]** 스위치 구조를 구현하십시오.
  - **렌더링 규칙:** [전체 종목] 선택 시 백엔드로부터 수신한 `quantity: 0`인 종목들도 리스트에 함께 노출하되, DataTable의 `rowClassName` 바인딩을 통해 해당 행(Row) 전체의 **CSS opacity를 0.7**로 흐리게 다운그레이드하여 마킹하십시오. [보유 중 종목] 모드일 때는 기존처럼 수량이 존재하는 종목만 노출합니다.

---

## 📌 4단계. 캔들 차트 인터랙션 고도화 및 로딩 시각화 (`StockDetail.jsx`)
- **상세 요구사항:**
  1. **기간 이동(Pan / Touch Move):** `ApexCharts` 의 `events.zoomed` 및 `events.scrolled` 콜백에서 X축 기간 범위(`min`, `max`)를 추출한 뒤, 공통 API 모듈을 사용해 백엔드 API(`GET /api/stocks/ohlcv`)로 변경된 범위의 데이터를 재요청하십시오.
  2. **🚨 [성능 방어] 300ms Debounce 결계:** 드래그 중 API 연속 트리거를 방지하기 위해 요청 체인에 반드시 **최소 300ms 디바운스**를 적용하십시오.
  3. **🚨 [UX 보완] 차트 로딩 상태(Loading Overlay) 구현:** 백엔드가 과거 데이터를 실시간 스크래핑(Historical Backfill)하는 동안 화면이 멈춘 것처럼 보이지 않도록, 디바운스가 끝난 직후 통신이 시작되어 완료될 때까지 **차트 전면에 은은한 로딩 스피너 혹은 블러(Blur) 오버레이 레이어**를 노출하여 시각적 안정감을 부여하십시오.
  4. **전체 화면(Fullscreen):** 차트 컨테이너 우측 상단 영역에 미니멀한 토글 버튼을 신설하고 브라우저 Native Fullscreen API(`requestFullscreen()`)를 결합하여 화면 확장 기능을 완성하십시오.

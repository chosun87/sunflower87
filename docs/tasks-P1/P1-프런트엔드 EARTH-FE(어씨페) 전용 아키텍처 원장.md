# 📊 sunflower87 프런트엔드 EARTH-FE(어씨페) 코어 아키텍처 원장

- **Tech Stack:** React (Vite), PrimeReact, ApexCharts
- **설계 철학:** 5대 관심사 분리(SoC), 렌더링 오버헤드 0%, 정석적인 상태 관리

## 📌 1. 컴포넌트 5분할 캡슐화 (Dashboard 구조)
- 1,160줄의 레거시 코드를 5개의 컴포넌트로 분리한 상태를 영구 유지한다.
  1) `AssetSummaryCard`: 총자산/예수금 요약
  2) `AIRecommendationSection`: 추천 종목
  3) `AssetDetailTab`: 보유 주식 DataTable
  4) `TransactionHistoryTab`: 매매 히스토리 DataTable
  5) `TransactionDialog`: 거래 등록/수정 모달

## 📌 2. 상태 관리 및 성능 방어 (Performance Guard)
- **`useMemo` 합산 결계:** Footer의 총자산, 총매수금액, 세금 합계 등은 반드시 `useMemo` 내부에서 연산하여 화면 프리징(Freezing)을 원천 방어한다.
- **`key` 리마운트 패턴:** 모달(`TransactionDialog`)은 `key` 속성을 이용해 모드(등록/수정) 변경 시 폼을 리셋하되, 종목 검색 이력은 부모 레이어에 캐싱하여 상태 유실을 막는다.
- **페이로드 부호 무결성:** 백엔드 송출 직전 `quantity`, `price`, `tax_fee`는 클라이언트에서 `Math.abs()`로 감싸 절대 양수 상태를 강제한다.
- **도미노 Refetch:** 거래 저장 완료 시 `fetchAccountData()`와 `loadTransactions()`를 연쇄 호출하여 자식 컴포넌트들을 1ms 시차 없이 동기화한다.

## 📌 3. 차트 (ApexCharts) 무결점 렌더링 규격
- **캔들 배열 공식 매핑:** 데이터 배열은 반드시 `[시가(Open), 고가(High), 저가(Low), 종가(Close)]` 순서를 엄수하여 캔들 꼬리 깨짐을 방지한다.
- **휴장일 공백 제거:** X축은 `category` 타입을 사용하여 주말/휴장일의 시각적 공백을 파쇄한다.
- **이동평균선 및 UI:** 백엔드의 80일치 데이터를 받아 5MA(주황), 20MA(보라)를 계산한 뒤 화면엔 최근 60거래일만 슬라이싱하여 표출한다. Glassmorphism 다크 툴팁을 유지한다.
- **리사이즈 누수 방어:** 창 크기 조절 이벤트를 감지할 때는 반드시 최소 `300ms Debounce`를 걸어 브라우저 크래시를 방지한다.
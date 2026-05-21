# 📊 Phase-2 4단계 캔들 차트 고도화 (80-Day Buffer & Pan 이동) 구현 계획

프런트엔드 차트의 좌우 드래그(Pan)를 지원하고 끊김 없는 이동평균선(MA) 계산을 위해 백엔드에 **80-Day Buffer** 규격을 적용하며, 차트 전체화면 모드를 신설하는 작업입니다.

## User Review Required

- **[성능/캐싱 동기화 정책]** 프런트엔드에서 드래그(Pan)하여 먼 과거(예: 2021년) 데이터를 조회할 때, 백엔드 `sync_ohlcv_cache` 로직은 해당 기간의 데이터를 pykrx로부터 다운로드하여 로컬 DB에 채워 넣어야 합니다. 이를 위해 기존 60일 고정 캐싱을 **조회 범위(start_date ~ end_date) + 80일 버퍼 유동형 캐싱**으로 유연하게 스케일링하도록 코어 로직을 보강하겠습니다. 이 확장 방향성에 동의하시나요?

## Proposed Changes

### 백엔드 (어씨베)

#### [MODIFY] be/routers/stocks.py
- `get_stock_ohlcv` 라우터에 `start_date: Optional[str]`, `end_date: Optional[str]` 파라미터를 수용합니다.
- 조회 쿼리: `start_date`가 들어오면 **80영업일 이전의 시계열 데이터부터** 불러올 수 있도록 날짜 범위를 동적으로 계산(`target_start_date = start_date - 120일`)하여 DB를 조회합니다. 조회 결과를 오름차순(ASC)으로 반환하여 프런트엔드 연산에 즉시 사용할 수 있게 합니다.

#### [MODIFY] be/portfolio_service.py
- `sync_ohlcv_cache(db, stock_code, start_date=None, end_date=None)` 로 파라미터를 확장합니다.
- 기존의 '과거 최신 데이터 백필(Backfill)' 로직 외에, **지정된 `start_date` 보다 더 이전의 데이터가 DB에 부족한 경우(Historical Backfill)** pykrx를 호출해 `cache` 테이블 앞단을 채우는 자가 치유 로직을 추가합니다.

### 프런트엔드 (어씨페)

#### [MODIFY] fe/src/pages/StockDetail.jsx
- **Pan & Zoom 이벤트 리스너 감지:** `ApexCharts`의 `events.zoomed` 및 `events.scrolled` 콜백을 캡처하여 현재 보고 있는 X축 기간(`min`, `max`)을 추출합니다.
- **300ms Debounce API 호출:** 기간이 변할 때마다 브라우저 과부하를 막기 위해 `lodash/debounce`(또는 커스텀 `setTimeout` 훅) 기반으로 300ms 이후에 백엔드 확장 API(`GET /api/stocks/ohlcv`)를 재요청하도록 연동합니다.
- **Fullscreen 버튼 신설:** 차트 컨테이너 상단 컨트롤 영역에 `requestFullscreen()`을 호출하는 토글 버튼 컴포넌트를 이식합니다.

## Verification Plan

### Manual Verification
1. 프런트엔드 차트 페이지에 접속하여 과거 방향으로 드래그(Pan) 해봅니다.
2. 콘솔 네트워크 탭에서 300ms 딜레이 후 API가 백그라운드 호출되는지 검증합니다.
3. 백엔드에서 80-Day 버퍼 데이터가 함께 전송되어 프런트엔드의 5MA, 20MA 곡선이 차트 왼쪽 끝단에서도 잘리지 않고 부드럽게 이어지는지 시각적으로 검수합니다.
4. '전체 화면' 토글 버튼을 눌러 모니터 풀 스크린 모드로 차트가 팽창 및 복귀하는지 테스트합니다.

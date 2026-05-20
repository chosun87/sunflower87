# TASK-04: URL 파라미터 기반 종목별 60거래일 캔들 차트(Candlestick Chart) 페이지 구현 (_FE_R7)

- **작성일:** 2026. 05. 19
- **작성자:** 기획자 MOON(무니)
- **승인자:** 의사결정권자 SUN(써니)
- **담당자:** EARTH-FE(어띠페)

---

## 📌 [COMMON] 공통 요구사항
- **동적 라우팅/파라미터 수립:** 특정 종목의 6자리 코드(예: `?code=494800` 또는 `/stock/494800`)를 파라미터로 주입받아 해당 종목의 60거래일 시계열 차트 페이지를 동적 렌더링한다.
- **글로벌 파이낸스 디자인 톤 동기화 (★절대 준수):** 캔들 차트의 양봉(상승)은 파란색(`#1e3a8a` 또는 `var(--blue-600)`), 음봉(하락)은 빨간색(`#dc2626` / `var(--red-600)`)으로 매핑하여 시스템 전체의 통일된 가시성을 유지한다.

---

## 🌍 [FE_TASK] 프런트엔드 상세 구현 지침

### 1. 작업 디렉토리 및 신규 페이지 생성
- 경로: `fe/src/pages/StockDetail.js` (또는 프로젝트 라우팅 규격에 맞춘 동적 라우트 폴더)
- URL 설계: `/stock?code={stock_code}` 형식으로 진입 시 파라미터를 파싱하는 훅(`useSearchParams` 또는 `useParams`)을 배치하라.

### 2. 백엔드 시계열 API 호출 인터페이스 연동
- 페이지 마운트 시 `GET /api/stocks/ohlcv?code={stock_code}` 엔드포인트를 호출하여 백엔드 DB 캐시 레이어에 적재된 60거래일치 데이터를 수신하라.
- 데이터 로딩 중에는 이전 규격에 맞추어 `isChartLoading` 상태 변수를 통해 스켈레톤(Skeleton) 또는 로딩 스핀 피드백을 노출하라.

### 3. 금융 표준 캔들 차트(Candlestick) 컴포넌트 구현
- 금융 시각화에 최적화된 **`react-apexcharts`** (또는 PrimeReact Chart 확장팩)를 활용하여 차트를 그리되 아래 스펙을 강제하라.
- **ApexCharts 기준 Options 설정 사양:**
  ```javascript
  const chartOptions = {
    chart: { type: 'candlestick', height: 400, toolbar: { show: true } },
    title: { text: `종목 코드 [${stockCode}] 60거래일 추세 분석`, align: 'left' },
    xaxis: { type: 'category', labels: { style: { cssClass: 'monospace' } } }, // 날짜 폰트 고정폭 적용
    yaxis: { tooltip: { enabled: true }, labels: { style: { cssClass: 'monospace' } } },
    plotOptions: {
      candlestick: {
        colors: {
          upward: 'var(--blue-600)',   // 양봉(상승): 파란색 통제
          downward: 'var(--red-600)'   // 음봉(하락): 빨간색 통제
        }
      }
    }
  };
  ```

### 4. 뒤로가기 및 대시보드 복귀 인터페이스
- 차트 상단에 PrimeReact Button을 활용해 "← 대시보드로 돌아가기" 버튼을 배치하고 클릭 시 메인 자산 현황 탭으로 부드럽게 라우팅 처리를 완료하라.

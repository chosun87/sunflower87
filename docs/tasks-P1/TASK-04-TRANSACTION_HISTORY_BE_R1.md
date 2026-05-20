# TASK-04: 16시 타임윈도우 분기형 60일 주가 시계열(OHLCV) 캐싱 및 자산 평가 API 구현 (_BE_R1)

- **작성일:** 2026. 05. 18
- **작성자:** 기획자 MOON(무니)
- **승인자:** 의사결정권자 SUN(써니)
- **담당자:** EARTH-BE(어띠베)

---

## 📌 [COMMON] 공통 요구사항
- **신규 태스크 분리:** 주가 시계열 엔진 및 전일/당일 종가 동적 스위칭 정산 로직의 고도화에 따라, 본 기능을 `TASK-04` 독립 태스크로 분리 발족한다.
- **16시 마감 타임윈도우(Time-Window) 적용:** 당일 최종 시세가 확정되는 **오후 4시(16:00)**를 기준으로 데이터 수집 대상 종료일(`END_DATE`)을 동적으로 제어한다.
  - **[Case 1] 16시 이전 조회:** 최근 매매거래일의 **'전일 종가'** 기준 역산 60거래일 확보.
  - **[Case 2] 16시 이후 조회:** 당일 확정 데이터가 반영된 **'당일 종가'** 기준 역산 60거래일 확보.
- **네이밍 컨벤션 표준화:** 계좌 식별자(외래키 포함)는 프런트엔드와 통일하여 무조건 **`acc_cd`**로 통일한다.

---

## 🌍 [BE_TASK] 백엔드 상세 구현 지침

### 1. 작업 디렉토리 및 전역 통제 변수 선언
- 작업 공간: `be/`
- `main.py` 최상단에 아래 전역 제어 변수를 엄격히 선언하라.
  ```python
  TRADE_DATE_PERIOD = 60      # 기본 확보 거래일수 (약 3개월치 컴팩트 유지)
  DATA_GAP_THRESHOLD = 120    # 데이터 공백 허용 임계치 (순수 거래일 기준 6개월치 통제)
  ```

### 2. SQLite 데이터베이스 시계열 캐시 스키마 (stock_ohlcv_cache)
- 테이블명: `stock_ohlcv_cache`
- 컬럼 구성: `stock_code(TEXT)`, `trade_date(TEXT)`, `open_price(INT)`, `high_price(INT)`, `low_price(INT)`, `close_price(INT)`, `volume(INT)`
- Composite Primary Key: `(stock_code, trade_date)` 복합 키를 설정하여 데이터 중복 적재를 원천 차단하라.

### 3. 16시 기준 동적 날짜 역산 유틸리티 펑션 구현
단순 달력 뺄셈 시 휴장일이 포함되어 60거래일 미만으로 수집되는 결함을 방지하기 위해, 아래의 KOSPI 인덱스 슬라이싱 기반 유틸리티 함수를 반드시 구현하라.

```python
from datetime import datetime, timedelta
from pykrx import stock

def get_exact_trade_date_limits(target_period=60):
    now = datetime.today()
    current_hour = now.hour
    
    # 16시(오후 4시) 이후 여부에 따라 기준 종료일(Target End Date) 동적 정의
    if current_hour >= 16:
        target_end_str = now.strftime("%Y%m%d")
    else:
        target_end_str = (now - timedelta(days=1)).strftime("%Y%m%d")
        
    # 휴장일 필터링용 넉넉한 120일짜리 달력 버퍼 가동
    safe_start_str = (now - timedelta(days=120)).strftime("%Y%m%d")
    
    # KOSPI 지수 조회를 통해 휴장일이 완벽히 제거된 '진짜 개장일 리스트' 인덱스 추출
    df_market = stock.get_market_ohlcv_by_date(safe_start_str, target_end_str, "005930")
    actual_trade_dates = df_market.index.strftime("%Y%m%d").tolist()
    
    # 뒤에서부터 정확히 target_period(60일)만큼 슬라이싱하여 최종 [시작일, 종료일] 확정
    valid_dates = actual_trade_dates[-target_period:]
    return valid_dates[0], valid_dates[-1]
```

### 4. 하이브리드 증분 수집 파이프라인 제어
보유 자산 조회(`GET /api/accounts`) 또는 매매 등록(`POST /api/transactions/add`) 트리거 시 아래 알고리즘을 수행하라.

- **[Step 1]** 로컬 DB에서 해당 종목의 가장 최신 `trade_date(LAST_DATE)`를 조회한다. 기록이 없으면 **[케이스 A]**로 이동한다.
- **[Step 2]** 위 유틸리티가 반환한 최종 종료일과 DB 내 `LAST_DATE` 사이의 순수 거래일 공백 수를 계산한다.
- **[케이스 B] 공백 거래일 ≤ 120일 (6개월 이하):** 데이터 연속성을 보존하기 위해 비어있는 공백 기간만 긁어와 메운다(Backfill).
- **[케이스 C] 공백 거래일 > 120일 (6개월 초과):** 단절 기간이 길어 유효성이 떨어진다고 판단, 해당 종목의 과거 캐시 기록을 DELETE 처리한다.
- **[케이스 A] 신규 및 만료 종목 처리:** 최종 확정된 시작일과 종료일 범위를 넘겨 정확히 60거래일치의 OHLCV 데이터를 pykrx로 일괄 수집하여 적재하라.

---

## 🏁 완료 조건
1. 오후 4시 이전 조회 시 전일 종가 기준, 오후 4시 이후 조회 시 당일 종가 기준으로 정확히 60거래일치 데이터 행(Row)이 유연하게 다루어지는가?
2. 거래일 기준 공백이 120일 이하인 종목 재매수 시 유실된 구간만 정확하게 백필 처리되는가?
3. 모든 API 요청 파라미터 및 DB 외래키에서 계좌 식별자는 무조건 `acc_cd` 표준을 고수하는가?

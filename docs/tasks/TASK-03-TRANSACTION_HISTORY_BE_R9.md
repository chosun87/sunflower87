# TASK-03: pykrx 연동 60일 주가 시계열(OHLCV) 동적 하이브리드 증분 캐싱 및 자산 평가 API 구현 (_BE_R9)

- **작성일:** 2026. 05. 18
- **작성자:** 기획자 MOON(무니)
- **승인자:** 의사결정권자 SUN(써니)
- **담당자:** EARTH-BE(어띠베)

---

## 📌 [COMMON] 공통 요구사항
- **동적 데이터 정제:** 전량 매도 후 재매수 등으로 인해 발생하는 주가 데이터 공백(Data Gap)을 제어하기 위해 임계치 기반 알고리즘을 도입한다.
- **수집 및 공백 정책:** 기본 수집 기간은 60거래일(약 3개월치)로 컴팩트하게 유지하고, 데이터 공백 허용 임계치는 순수 거래일 기준 6개월인 120일로 설정하여 데이터의 유효성을 통제한다.
- **평가 기준:** 보유 종목의 현재가는 최근 매매거래일의 **'전일 종가'**를 기준으로 산정한다.

---

## 🌍 [BE_TASK] 백엔드 상세 구현 지침

### 1. 작업 디렉토리 및 전역 통제 변수 세팅
- 작업 공간: `be/`
- `main.py` 최상단에 SUN님의 최종 결정 사양에 맞추어 아래 전역 변수 2개를 오차 없이 선언하라.
  ```python
  TRADE_DATE_PERIOD = 60      # 기본 확보 거래일수 (약 3개월치 컴팩트 유지)
  DATA_GAP_THRESHOLD = 120    # 데이터 공백 허용 임계치 (순수 거래일 기준 6개월치 통제)
  ```

### 2. SQLite 데이터베이스 시계열 캐시 스키마 (stock_ohlcv_cache)
복합 기본키 (stock_code, trade_date) 구조를 가진 시고저종(OHLCV) 테이블 스키마를 빌드하라.

### 3. ★ 날짜 역산 유틸리티 펑션 및 하이브리드 증분 수집 알고리즘
달력 기준 마이너스 연산 시 휴장일이 포함되어 60거래일 미만으로 데이터가 수집되는 결함을 방지하기 위해, 어띠베는 아래의 KOSPI 인덱스 슬라이싱 로직을 반드시 내부 유틸 함수로 구현하라.

```python
from datetime import datetime, timedelta
from pykrx import stock

def get_exact_trade_date_limits(target_period=60):
    # 달력 기준 120일 전부터 전일까지 넉넉하게 지정 (휴장일 필터링용 넷 버퍼)
    yesterday_str = (datetime.today() - timedelta(days=1)).strftime("%Y%m%dd")
    safe_start_str = (datetime.today() - timedelta(days=120)).strftime("%Y%m%dd")
    
    # 시장 전체 개장일 캘린더 배열을 획득하기 위해 KOSPI 지수 조회
    df_market = stock.get_market_ohlcv_by_date(safe_start_str, yesterday_str, "KOSPI")
    actual_trade_dates = df_market.index.strftime("%Y%m%dd").tolist()
    
    # 뒤에서부터 정확히 target_period(60일)만큼 슬라이싱하여 시작일 and 전일 확정
    valid_dates = actual_trade_dates[-target_period:]
    return valid_dates[0], valid_dates[-1]
```

*   **[Step 1] 기존 캐시 데이터 최종일 조회**:
    - 로컬 DB에서 해당 종목의 가장 최신 trade_date(LAST_DATE)를 조회하라. 기록이 없다면 **[케이스 A]**로 이동한다.
*   **[Step 2] 120거래일 임계치 기반 데이터 공백 계산**:
    - 위 유틸리티를 통해 확인한 진짜 거래일 리스트 상에서, YESTERDAY와 DB 내 LAST_DATE 사이의 순수 거래일 수(개수)를 카운트하라.
*   **[케이스 B] 공백 거래일 ≤ 120일 (거래일 기준 6개월 이하)**:
    - 데이터 연속성이 유효하다고 판단, `get_market_ohlcv_by_date(start_date=LAST_DATE + 1일, end_date=YESTERDAY)`를 호출하여 비어있는 공백 기간의 데이터를 통째로 긁어와 메워라(**Backfill**).
*   **[케이스 C] 공백 거래일 > 120일 (거래일 기준 6개월 초과)**:
    - 단절 기간이 너무 길어 수집 실익이 없다고 판단, 로컬 DB 내 해당 종목의 과거 OHLCV 기록을 과감히 **DELETE** 처리하라.
*   **[케이스 A] 순수 신규 및 만료 종목 처리 (최신 60일치 셋업)**:
    - `get_exact_trade_date_limits(TRADE_DATE_PERIOD)`로 획득한 정확한 시작일과 종료일 범위를 파라미터로 넘겨 총 **60거래일치**의 OHLCV 데이터를 수집 후 `stock_ohlcv_cache` 테이블에 새롭게 적재하라.

---

## 🏁 완료 조건
1. 최초 매수 종목 등록 시, 단순 달력 빼기가 아닌 '진짜 한국 증시 거래일' 기준으로 정확히 60개의 데이터 행(Row)이 DB에 채워지는가?
2. 거래일 기준 공백이 120일 이하인 종목은 과거 기록 유실 없이 빈틈없이 데이터가 메워(Backfill)지는가?
3. 전일 종가가 보유 자산 상세 화면의 현재가 자리에 정밀하게 안착하는가?

# TASK-04: 16시 타임윈도우 분기형 60일 주가 시계열(OHLCV) 캐싱 및 자산 평가 API 구현 (_BE_R2)

- **작성일:** 2026. 05. 18
- **작성자:** 기획자 MOON(무니)
- **승인자:** 의사결정권자 SUN(써니)
- **담당자:** EARTH-BE(어띠베)

---

## 📌 [COMMON] 공통 요구사항
- **네이밍 컨벤션 표준화 (★최종 확정):** 계좌 마스터 정보 조회 시, DB 컬럼명과 API 응답 객체의 Key(Alias) 명칭을 인위적 변형 없이 100% 동일하게 일치시켜 정합성을 확보한다.
- **16시 마감 타임윈도우(Time-Window) 적용:** 당일 최종 시세가 확정되는 **오후 4시(16:00)**를 기준으로 데이터 수집 대상 종료일(`END_DATE`)을 동적으로 제어한다.
- **표준 약어 고수:** 시스템 전반의 계좌 식별 고유 키는 무조건 **`acc_cd`** 표준명만을 사용한다.

---

## 🌍 [BE_TASK] 백엔드 상세 구현 지침

### 1. 작업 디렉토리 및 전역 통제 변수 선언
- 작업 공간: `be/`
- `main.py` 최상단에 아래 전역 제어 변수를 선언하라.
  ```python
  TRADE_DATE_PERIOD = 60      # 기본 확보 거래일수 (약 3개월치 컴팩트 유지)
  DATA_GAP_THRESHOLD = 120    # 데이터 공백 허용 임계치 (순수 거래일 기준 6개월치 통제)
  ```

### 2. ★ 계좌 마스터 조회 API 데이터 매핑 규칙 (Alias 통일)
`GET /api/accounts` 등 계좌 정보를 반환하는 엔드포인트 또는 DB 쿼리문 작성 시, 변수명과 딕셔너리 Key값을 DB 컬럼명과 완전하게 일치시켜 송출하라.

정형 규격 사양:
```python
# (X) "acc_nm": acc_name, "acc_company_nm": acc_company 형태로 변형하지 말 것.
# (O) 아래와 같이 컬럼명과 자로 잰 듯이 통일할 것.
account_response = {
    "acc_cd": row["acc_cd"],
    "acc_nm": row["acc_nm"],
    "acc_company_nm": row["acc_company_nm"],
    "cash_balance": row["cash_balance"]
}
```

### 3. SQLite 데이터베이스 시계열 캐시 스키마 (`stock_ohlcv_cache`)
- 테이블명: `stock_ohlcv_cache`
- 복합 기본키 `(stock_code, trade_date)` 구조를 설정하여 데이터 중복 적재를 원천 차단하라.

### 4. 16시 기준 동적 날짜 역산 유틸리티 펑션 구현 (KOSPI 인덱스 슬라이싱)
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
        
    safe_start_str = (now - timedelta(days=120)).strftime("%Y%m%d")
    
    df_market = stock.get_market_ohlcv_by_date(safe_start_str, target_end_str, "KOSPI")
    actual_trade_dates = df_market.index.strftime("%Y%m%d").tolist()
    
    valid_dates = actual_trade_dates[-target_period:]
    return valid_dates[0], valid_dates[-1]
```

### 5. 하이브리드 증분 수집 파이프라인 제어
보유 자산 조회 또는 매매 등록 트리거 시 알고리즘을 가동하라.
- **[케이스 B] 공백 거래일 ≤ 120일 (6개월 이하):** 비어있는 구간만 정확하게 메운다(Backfill).
- **[케이스 C] 공백 거래일 > 120일 (6개월 초과):** 해당 종목의 과거 캐시 기록을 DELETE 처리한 후 최신 60거래일치를 통째로 다시 채운다.

---

## 🏁 완료 조건
1. API 응답 JSON의 Key값이 `acc_nm`, `acc_company_nm`으로 DB 원장 명칭과 완벽히 일치하여 출력되는가?
2. 오후 4시를 기점으로 전일/당일 종가 스위칭 및 60거래일 캘린더 커팅이 정상 작동하는가?
3. 모든 데이터 핸들러에서 계좌 식별자는 `acc_cd` 표준을 예외 없이 준수하는가?

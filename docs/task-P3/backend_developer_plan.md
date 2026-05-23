# ⚙️ 백엔드 개발자 전용 개발 계획서 (Backend Developer Plan)

본 계획서는 **sunflower87** 프로젝트 리팩토링 중 비즈니스 로직 개편, 파이썬 파일 단수화, 공통 상수 모듈 정의, 비동기 캐싱 성능 개선, 대용량 거래일 버퍼 서빙 및 역할 도메인이 완벽히 격리된 REST API 엔드포인트 세트를 구현하는 백엔드 개발자 전용 명세서입니다.

---

## 1. 백엔드 모듈 단수화 및 공통 상수 정의

파이썬 파일 명칭을 단수형으로 정비하고, 문자열 하드코딩 오류를 방지하기 위해 공통 상수를 Python `Enum` 클래스로 정의하여 Pydantic 검증 스키마에 바인딩합니다.

### 📂 파일명 단수화 매핑
*   `be/routers/accounts.py` ➔ **`be/routers/account.py`**
*   `be/routers/transactions.py` ➔ **`be/routers/transaction.py`**
*   `be/routers/stocks.py` ➔ **`be/routers/stock.py`** (주식 마스터 검색/Lookup 전담)
*   `be/routers/recommendations.py` ➔ **`be/routers/recommendation.py`**
*   `be/routers/tasks.py` ➔ **`be/routers/task.py`**
*   `be/routers/stock_ohlcv.py` **[NEW]** (시고저종 대용량 주가 시계열 조회 전담)
*   `be/routers/transaction_cash.py` **[NEW]** (현금 흐름 입출금/이자/배당 원장 CRUD 전담)
*   `be/portfolio_service.py` ➔ **`be/portfolio.py`** (포트폴리오 연산 서비스 단수화)

### 🧱 공통 상수 정의 ([be/constants.py](file:///C:/01_projects/sunflower87/be/constants.py)) [NEW]
```python
from enum import Enum

class TradeType(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class CashType(str, Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"
    INTEREST = "INTEREST"
    DIVIDEND = "DIVIDEND"
    FEE = "FEE"

class MarketType(str, Enum):
    KOSPI = "KOSPI"
    KOSDAQ = "KOSDAQ"
    KONEX = "KONEX"
    ETF = "ETF"
```
*   `schemas.py`에서 `TransactionCreate` 등의 Pydantic 모델 필드를 정의할 때 위 Enums 자료형(`TradeType`, `CashType`)을 매핑하여 입력 유효성 검사를 자동 집행합니다.

---

## 2. 현금 거래 원장 연동 포트폴리오 연산 로직 (`be/portfolio.py`)

계좌의 실시간 현금 예수금(`cash_balance`) 및 자산 가치를 정밀하게 연산하는 공식을 구현합니다. 

### 🧮 예수금 정산 공식
$$\text{예수금} = \text{초기원금} + \sum \text{현금거래(입금/이자/배당)} - \sum \text{현금거래(출금/비용)} + \sum \text{주식매도액} - \sum \text{주식매수액(수수료 포함)}$$

### 🛠️ 구현 가이드라인
1.  **소프트 딜리트 필터링 강제**: 
    `Transaction` 및 `TransactionCash` 조회 쿼리에 반드시 `.filter(Model.dt_deleted.is_(None))` 제약조건을 강제하여 삭제 처리된 거래는 정산 연산에서 완벽하게 필터링 배제시킵니다.
2.  **KRW 정수화 연산**: 
    `avg_price` 및 `purchase_amount` 연산 시 부동소수점 오차가 발생하지 않도록 정밀한 정수형 캐스팅(`int(round(val))`)을 적용해 DB에 저장합니다.
3.  **3NF 동적 조인**:
    보유 잔고 리턴 조립 시, 중복 컬럼이 제거된 `stock` 테이블을 쿼리한 뒤 `stock_cache`와 조인하여 응답 JSON에 `"stock_name": "삼성전자"`를 동적으로 추가해 프론트엔드 호환성을 유지합니다.

---

## 3. EARTH 규격 비동기 주가 서빙 및 피드백 라우터 구현

### 📊 ① OHLCV 주가 서빙 라우터 ([be/routers/stock_ohlcv.py](file:///C:/01_projects/sunflower87/be/routers/stock_ohlcv.py)) [NEW]
*   **`GET /api/stock_ohlcv`** 엔드포인트를 구현하여 차트용 주가 시계열 데이터를 제공합니다.
*   **🚨 240거래일 과거 버퍼 프리펜드**:
    프론트엔드가 요청한 `start_date` 시점보다 **최소 240거래일 앞선 과거 데이터부터 누적하여 오름차순(ASC)**으로 정렬한 뒤 서빙합니다. 이를 충족시키기 위해 조회 쿼리 시 `target_start_date = start_date - 360달력일` 수준으로 날짜를 역산 확장하여 DB를 조회합니다.
*   **FastAPI BackgroundTasks 비동기 수집**:
    로컬 캐시 DB에 유효한 정보가 있을 경우 지연 시간 없이 즉시 **10ms 내외의 초고속 응답**을 클라이언트에 반환합니다. `pykrx` 연동 온라인 크롤링 작업은 `background_tasks: BackgroundTasks`에 백그라운드 위임하여 비동기 실행합니다.
*   **안전한 백그라운드 DB 세션 분리**:
    백그라운드 스레드에서 API의 요청 세션이 종료된 후에도 정상 작동할 수 있도록 별도의 독립 DB 세션을 열고 닫는 비동기 전용 래퍼인 `sync_ohlcv_cache_bg` 함수를 `portfolio.py` 내부에 구현하여 바인딩합니다.
*   **자가 치유 과거 백필**:
    조회 대상 과거 거래일에 누락된 일자가 있는 경우, 실시간으로 외부 API(`pykrx`)를 조회하여 로컬 캐시 DB 앞단을 채워 넣는 **점진적 백필 자가치유 알고리즘**을 심습니다.

### 💰 ② 현금 흐름 원장 라우터 ([be/routers/transaction_cash.py](file:///C:/01_projects/sunflower87/be/routers/transaction_cash.py)) [NEW]
*   **`GET /api/transactions_cash`**: 특정 계좌의 현금 입출금/이자/배당 이력 전체 조회
*   **`POST /api/transactions_cash/add`**: 신규 현금 흐름 등록 및 예수금 실시간 재정산 연계 호출
*   **`DELETE /api/transactions_cash/{id}`**: 특정 현금 흐름 **소프트 딜리트 (`dt_deleted` 마킹)** 처리 및 예수금 역산 정산 호출

### 💳 ③ 계좌 순서 정렬 및 시계열 성과 라우터 ([be/routers/account.py](file:///C:/01_projects/sunflower87/be/routers/account.py)) [MODIFY]
*   **`PUT /api/accounts/reorder` [NEW]**: 프론트엔드 설정(Settings) 화면에서 `SortableJS` 드래그앤드롭 리오더링 시 계좌 우선순위를 배치 동기화하는 API를 구현합니다.
    *   *요청 바디*: `{"acc_orders": [{"acc_cd": "A001", "acc_order": 1}, {"acc_cd": "A002", "acc_order": 2}]}`
*   **`GET /api/accounts/{acc_cd}/performance` [NEW]**: 대시보드 차트 카드에 계좌별 날짜별 잔고 및 누적 수익률 시계열을 전송하는 API를 구현합니다.
    *   *로직*: 과거 일자별로 해당 계좌의 예수금 변동 추이와 보유 주식 종가 평가액 추이를 역산 합산하여 계좌 종합 자산 성능 지표를 반환합니다.

### 🤖 ④ AI 추천 피드백 라우터 ([be/routers/recommendation.py](file:///C:/01_projects/sunflower87/be/routers/recommendation.py)) [MODIFY]
*   **`PATCH /api/recommendations/{stock_code}/feedback`** 엔드포인트를 구현하여 투자자의 피드백을 기록합니다.
*   **의견 피드백 제약조건**:
    투자자가 `0`~`5` 사이의 의견 점수(`investor_score`)를 전달하면 해당 추천에 기록하며, `0`점을 제출할 시 반려(Reject)로 처리합니다. 이 데이터는 추후 AI가 추천 정보를 생성할 때 학습 가중치 파라미터로 사용됩니다.
*   **`DELETE /api/recommendations/{stock_code}`**: 추천 제외 처리 시 물리 삭제하지 않고 `dt_deleted`에 타임스탬프를 마킹하여 과거 추천 이력을 보존합니다.

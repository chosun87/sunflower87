# ⚙️ 백엔드 개발자 전용 개발 계획서 (Backend Developer Plan)

본 계획서는 **sunflower87** 프로젝트 리팩토링 중 비즈니스 로직 개편, 파이썬 파일 단수화, 공통 상수 모듈 정의, 비동기 캐싱 성능 개선, 대용량 거래일 버퍼 서빙 및 역할 도메인이 완벽히 격리된 REST API 엔드포인트 세트를 구현하는 백엔드 개발자 전용 명세서입니다.

추가 요건인 **실시간 주가 수집(1분 간격 폴링)**, **계좌별 일자별 잔고 원장(`account_daily_balance`) 정산 공식**, **과거 데이터 변동 시 시계열 전체 강제 재계산(Self-Healing)**, 그리고 **데이터베이스 8개 전체 테이블에 대한 완전한 1:1 대칭형 RESTful CRUD API 명세**가 보강 탑재되었습니다.

---

## 1. 백엔드 모듈 단수화 및 공통 상수 정의

파이썬 파일 명칭을 단수형으로 정비하고, 문자열 하드코딩 오류를 방지하기 위해 공통 상수를 Python `Enum` 클래스로 정의하여 Pydantic 검증 스키마에 바인딩합니다.

### 📂 파일명 단수화 매핑 및 디렉토리 구조 개편
*   `be/routers/accounts.py` ➔ **`be/routers/account.py`**
*   `be/routers/transactions.py` ➔ **`be/routers/transaction.py`**
*   `be/routers/stocks.py` ➔ **`be/routers/stock.py`** (주식 마스터 검색/Lookup 전담)
*   `be/routers/recommendations.py` ➔ **`be/routers/recommendation.py`**
*   `be/routers/tasks.py` ➔ **`be/git/git_task.py`** **[NEW]** (기획 마크다운 태스크 관리 및 라우터)
*   `be/git_service.py` ➔ **`be/git/git_service.py`** **[NEW]** (Git 형상관리 공통 서비스 모듈)
*   `be/routers/stock_ohlcv.py` **[NEW]** (시고저종 대용량 주가 시계열 조회 전담)
*   `be/routers/transaction_cash.py` **[NEW]** (현금 흐름 입출금/이자/배당 원장 CRUD 전담)
*   `be/portfolio_service.py` ➔ **`be/portfolio.py`** (포트폴리오 연산 서비스 단수화)

---

### 📂 주요 모듈의 역할 및 세부 기능 명세

#### 1. `be/git/git_task.py` (구 `be/routers/tasks.py` 이동 및 명칭 변경) — 기획 마크다운 태스크 관리 모듈
*   **역할**: 마크다운 기반의 프로젝트 태스크 파일 생성 및 로컬 변경 사항을 원격 Git 리포지토리로 자동 Push하는 형상관리 연동 라우터입니다.
*   **세부 기능**:
    1.  **태스크 생성 및 작성 (`POST /api/tasks`)**: 클라이언트로부터 수신한 태스크 파일명과 마크다운 본문을 활용하여 프로젝트 루트 폴더 하위의 `docs/tasks` 내에 마크다운 문서(`.md`)를 물리적으로 생성하고 기록합니다.
    2.  **보안 및 입력 유효성 검증**: 디렉토리 트래버설(Directory Traversal) 웹 공격을 사전에 완벽히 방어하기 위해 파일명 유효성 정규식(`^[A-Za-z0-9\-_]+\.md$`)을 가동하여 알파뉴메릭, 하이픈, 언더스코어 및 `.md` 확장자만 수락합니다.
    3.  **Git 커밋 및 원격 푸시 자동화**: `be/git/git_service.py` 모듈과 연계하여, 생성 및 변경된 태스크 파일을 Git에 자동으로 스테이징(`git add`)하고 커밋(`git commit -m`)한 뒤 원격 리포지토리에 푸시(`git push`)함으로써 최신 기획 상태를 형상 관리 서버와 실시간 동기화합니다.

#### 2. `be/git/git_service.py` (구 `be/git_service.py` 이동) — Git 형상관리 연동 공통 모듈
*   **역할**: 로컬 저장소 변경 이력을 감지하여 Git 스테이징, 커밋 및 원격 푸시 명령어를 안전하게 프로세스로 실행하고 형상 관리 동기화 결과를 반환하는 서비스 엔진입니다.

#### 3. `be/portfolio.py` (구 `portfolio_service.py` 단수화) — 실시간 종합 금융 연산 엔진
*   **역할**: 계좌의 자산 가치 연산, 실시간 수익 추적, 영업일 캘린더 생성, OHLCV 주가 동적 캐싱 및 계좌/거래 내역 소급 정산(Self-Healing)을 책임지는 백엔드 핵심 비즈니스 로직 허브입니다.
*   **세부 기능**:
    1.  **표준 영업일 캘린더 생성 (`get_exact_trade_date_limits`, `get_market_trade_dates`)**: 한국 거래소(KOSPI 또는 삼성전자 005930 기준) 개장일을 `pykrx`를 통해 조회하여 공휴일과 주말이 정밀하게 제외된 한국 금융 시장 표준 영업일 범위를 실시간으로 획득 및 제공합니다.
    2.  **시고저종 캐싱 및 Gap 정제 (`sync_ohlcv_cache`)**:
        *   특정 종목의 OHLCV 시계열 주가 캐시를 로컬 데이터베이스(`stock_ohlcv_cache`)에 적재해 조회 속도를 극대화합니다.
        *   과거 유효 주가가 누락되었을 때 과거 방향으로 백필(Historical Backfill)하여 채워 넣고, 누락 영업일수(Gap)가 지정된 임계치를 초과할 시 캐시를 완전히 Purge하고 최신 세팅하는 Gap 정제 기능을 동작시킵니다.
    3.  **이동평균법 기반의 개별 종목 잔고 추적 (`calculate_stock_balance`)**: 계좌 소속 종목의 거래 원장을 시간순으로 엄격하게 순회 시뮬레이션하면서, 분할 매수/매도 시 세금 및 수수료를 반영한 가중 이동평균 평단가, 보유 수량, 순수 매수원금 및 실현 손익을 1원의 부동소수점 오차도 없이 추적 산정합니다.
    4.  **포트폴리오 DTO 빌드 및 동적 조인 (`get_enriched_accounts_data`)**:
        *   개별 종목에 대한 실시간 평가금액, 평가손익 및 수익률을 동적으로 순회 연산합니다.
        *   각 계좌의 실시간 예수금(`cash_balance`)과 보유 주식 평가총액을 합산하여 계좌별 수익률 및 전 계좌 통합 총자산을 산출하고, 3NF 스키마 설계에 따라 종목 마스터 테이블(`stock_cache`)과 Dynamic JOIN을 맺어 프론트엔드가 즉시 렌더링에 사용할 수 있는 한글 종목명(`stock_name`) 포함 완성형 JSON DTO를 반환합니다.
    5.  **연대기 포트폴리오 역산 복원 및 예수금 정산 (`recalculate_portfolio_for_account`)**: 
        *   계좌에 속한 모든 거래 기록(매매 거래, CMA 현금 거래)을 최초일 자산 시점부터 역산 순회하면서 최종 보유 수량, 평단가 및 예수금 잔고(`cash_balance`)를 완벽히 가감 역산하여 영구 동기화합니다.
        *   시뮬레이션 중 잔고나 수량이 마이너스(`minus`)로 떨어지는 회계 장부 불일치 오류가 감지될 시 즉시 예외를 발생시키고 롤백하여 장부 무결성을 확보합니다.

---

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

## 3. 전체 8개 테이블 완전 대칭형 RESTful CRUD API 구현 계획

백엔드에서 제공하며 프론트엔드가 호출하는 **전체 8개 테이블 완전 대칭형 RESTful CRUD API 스펙**입니다.

### 💳 ① 계좌 마스터 API (`be/routers/account.py`) - `account` 테이블
- **`GET /api/account`** [Read All]: 활성화된 전체 계좌 목록 조회
- **`GET /api/account/{acc_cd}`** [Read One]: 특정 계좌 상세 단일 조회
- **`POST /api/account`** [Create]: 신규 증권 계좌 등록 (Initial Cash 설정)
- **`PUT /api/account/{acc_cd}`** [Update]: 계좌 명칭, 투자 원금 및 순서 정보 수정 (포트폴리오 및 일지 자동 재연쇄 정산)
- **`DELETE /api/account/{acc_cd}`** [Delete]: 증권 계좌 소프트 딜리트 처리 (`dt_deleted` 필드에 삭제일 마킹)
- **`PUT /api/account/reorder`** [Update Priority]: `SortableJS` 드래그앤드롭 리오더링에 따른 계좌 우선순위 배치 동기화
- **`GET /api/account/{acc_cd}/performance`** [Performance Time Series]: 계좌별 날짜별 잔고 및 누적 수익률 시계열 전송

### 📝 ② 주식 매매 거래 API (`be/routers/transaction.py`) - `transaction` 테이블
- **`GET /api/transaction`** [Read All]: 전체 또는 조건별(계좌, 종목 등) 매매 거래 목록 조회
- **`GET /api/transaction/{id}`** [Read One]: 특정 매매 거래 단일 상세 조회
- **`POST /api/transaction/add`** [Create]: 신규 매수/매도 거래 기록 추가 & 자산 실시간 누적 연대기 정산 및 일자별 잔고 자동 재정산 호출
- **`PUT /api/transaction/{id}`** [Update]: 특정 매매 로그 수정 및 이전/신규 계좌 포트폴리오/일자별 잔고 동시 역산 재계산
- **`DELETE /api/transaction/{id}`** [Delete]: 특정 거래 기록 소프트 딜리트 처리 (`dt_deleted` 마킹) 및 잔고/예수금/일자별 잔고 자동 역산 복원(Rollback)

### 💰 ③ 현금 거래 API (`be/routers/transaction_cash.py`) - `transaction_cash` 테이블
- **`GET /api/transaction_cash`** [Read All]: 특정 계좌의 현금 입출금, 이자 수익, 배당 이력 전체 조회
- **`GET /api/transaction_cash/{id}`** [Read One]: 특정 현금 거래 단일 상세 조회
- **`POST /api/transaction_cash/add`** [Create]: 입출금, 이자, 배당 등의 신규 현금 흐름 기록 등록 및 예수금/일자별 잔고 자동 재정산 연쇄
- **`PUT /api/transaction_cash/{id}`** [Update]: 특정 현금 거래 명세 및 금액 수정 및 예수금/일자별 잔고 실시간 재연산
- **`DELETE /api/transaction_cash/{id}`** [Delete]: 특정 현금 거래 기록 소프트 딜리트 처리 (`dt_deleted` 마킹) 및 예수금/일자별 잔고 실시간 역산 복원

### 🚨 ④ 계좌 일자별 잔고 API (`be/routers/account.py`) - `account_daily_balance` 테이블
- **`GET /api/account/{acc_cd}/daily-balance`** [Read All]: 계좌별 날짜별 잔고 목록 시계열 조회
- **`GET /api/account/{acc_cd}/daily-balance/{trade_date}`** [Read One]: 계좌별 특정 날짜의 단일 잔고 스냅샷 조회
- **`POST /api/account/{acc_cd}/daily-balance`** [Create]: 계좌별 특정 날짜의 커스텀 잔고 스냅샷 강제 생성/주입
- **`PUT /api/account/{acc_cd}/daily-balance/{trade_date}`** [Update]: 계좌별 특정 날짜의 잔고 스냅샷 수치 수동 편집 및 수정
- **`DELETE /api/account/{acc_cd}/daily-balance/{trade_date}`** [Delete]: 계좌별 특정 날짜의 잔고 스냅샷 레코드 삭제
- **`POST /api/account/{acc_cd}/recalculate-balance`** [Recalculate]: 계좌 거래 대장을 바탕으로 일자별 잔고 전체 자동 재정산/재구성 (수동 자가치유)

### 📦 ⑤ 보유 잔고 API (`be/routers/stock.py`) - `stock` 테이블
- **`GET /api/stock`** [Read All]: 전체 계좌 또는 특정 계좌의 보유 잔고 목록 조회
- **`GET /api/stock/{acc_cd}/{stock_code}`** [Read One]: 특정 계좌 소속의 특정 종목 보유고 단일 조회
- **`POST /api/stock`** [Create]: 임의 보유 잔고 레코드 수동 생성 (오프라인/레거시 마스터 이식용)
- **`PUT /api/stock/{acc_cd}/{stock_code}`** [Update]: 특정 보유 잔고 수치 수동 편집
- **`DELETE /api/stock/{acc_cd}/{stock_code}`** [Delete]: 특정 보유 잔고 삭제 (포트폴리오 강제 초기화용)

### 🏷️ ⑥ 종목 마스터 API (`be/routers/stock.py`) - `stock_cache` 테이블
- **`GET /api/stock/search`** [Search]: 부분 검색 키워드 기반 동적 종목 초고속 인메모리식 자동완성 검색
- **`GET /api/stock/lookup`** [Lookup]: 6자리 주식 코드로 한글 종목명 매핑 조회
- **`POST /api/stock/sync-master`** [Sync]: 수동 종목 마스터 강제 재크롤링 및 로컬 마스터 캐시 최신화
- **`POST /api/stock/master`** [Create]: 커스텀 종목 마스터 레코드 수동 생성
- **`PUT /api/stock/master/{stock_code}`** [Update]: 커스텀 종목 마스터 정보 수정
- **`DELETE /api/stock/master/{stock_code}`** [Delete]: 종목 마스터 레코드 소프트 딜리트 (`dt_deleted` 마킹)

### 📊 ⑦ 주가 OHLCV API (`be/routers/stock_ohlcv.py`) - `stock_ohlcv_cache` 테이블
- **`GET /api/stock_ohlcv`** [Read OHLCV]: 특정 종목의 과거 시계열 조회 (즉시 캐시 고속 반환 후 BackgroundTasks 크롤러 백그라운드 수집 실행)
- **`GET /api/stock_ohlcv/{stock_code}/{trade_date}`** [Read One]: 특정 종목의 특정 영업일 OHLCV 단일 행 상세 조회
- **`POST /api/stock_ohlcv`** [Create]: 특정 일자의 시고저종, 거래량, 거래대금, 등락률 임의 생성/입력
- **`PUT /api/stock_ohlcv/{stock_code}/{trade_date}`** [Update]: 특정 일자의 주가(등락률, 거래대금 포함) 정보 수정
- **`DELETE /api/stock_ohlcv/{stock_code}/{trade_date}`** [Delete]: 특정 일자의 주가 캐시 레코드 삭제
- **`POST /api/stock/refresh-prices`** [Refresh All]: 보유한 모든 주식의 실시간 현재가 및 지표 외부 수집 및 DB 캐시 1분 간격 동기화

### 🤖 ⑧ AI 추천 API (`be/routers/recommendation.py`) - `recommendation` 테이블
- **`GET /api/recommendation`** [Read All]: 오늘 날짜 기준 AI 포트폴리오 권장 추천 종목 목록 조회
- **`GET /api/recommendation/{stock_code}`** [Read One]: 특정 AI 추천 종목 단일 상세 조회
- **`POST /api/recommendation`** [Create]: 신규 AI 추천 종목 등록
- **`PUT /api/recommendation/{stock_code}`** [Update]: 추천 내용/사유/점수 수정
- **`DELETE /api/recommendation/{stock_code}`** [Delete]: 추천 종목 소프트 딜리트 (`dt_deleted` 마킹)
- **`PATCH /api/recommendation/{stock_code}/feedback`** [Feedback]: 투자자의 의견 피드백 점수(0~5) 부여 (0점일 시 즉시 소프트 딜리트 연쇄)

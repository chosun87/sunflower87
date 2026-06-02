# 백엔드 및 DB 리팩토링 구현 계획서

## 1. 개요
현재 `sunflower87` 백엔드는 레거시 DB 스키마(예약어 포함, 복수형 테이블명, 3NF 미적용)와 파편화된 라우터로 구성되어 있습니다. 본 계획서는 기획된 설계도(`db_developer_plan.md`, `backend_developer_plan.md`)를 바탕으로 백엔드 로직과 데이터베이스를 전면 개편합니다.

> [!WARNING]
> 이미 존재하는 `sunflower87.db`의 데이터를 잃지 않고 마이그레이션해야 합니다. 따라서 `database.py` 개편 후 반드시 안전한 `migrate.py` 작성 및 실행이 선행되어야 합니다.

## 2. 세부 진행 단계

### 1단계: DB 모델 전면 개편 (`database.py`)
- 모든 테이블 단수형 이름(table_name)으로 변경: `account`, `transaction`, `stock`, `stock_cache`, `stock_ohlcv_cache`, `recommendation`.
- 신규 테이블 추가: `transaction_cash`, `account_balance_daily`.
- 예약어 필드 `dt_` 접두어로 통합 (e.g. `date` -> `dt_trade`, `type` -> `trade_type`).
- 3NF 적용: `stock_name`을 `stock_cache`에만 남기고 나머지에서 참조 제거.
- `stock_ohlcv_cache`에 `trading_value`, `fluctuation_rate` 추가.

### 2단계: 안전한 데이터 마이그레이션 스크립트 작성 (`migrate.py`)
- 기존 DB(`sunflower87.db`)에서 `transactions`, `stocks`, `account` 등의 데이터를 메모리로 읽어 백업합니다.
- SQLAlchemy `drop_all` / `create_all`을 통해 신규 스키마로 덮어씌웁니다.
- 메모리에 있는 데이터를 신규 스키마 규격(`dt_trade`, `INTEGER` 캐스팅 등)에 맞게 가공하여 Insert 합니다.
- 마이그레이션 스크립트 실행 후 데이터 무결성(Data Integrity)을 확인합니다.

### 3단계: 상수화 및 Pydantic 스키마 정의 (`constants.py`, `schemas.py`)
- `constants.py` 신설: `TradeType`, `CashType`, `MarketType` Enum 정의.
- `schemas.py`: 8개 테이블에 대한 입출력 스키마(Request/Response DTO)를 `ApiResponse` 규격에 맞게 전면 재작성합니다.

### 4단계: 비즈니스 코어 로직 분리 (`portfolio.py`)
- `portfolio_service.py`를 `portfolio.py`로 이름 변경.
- 주가 동기화, 평단가 연산(이동평균법), 일자별/계좌별 잔고 완전 역산(`recalculate_portfolio_for_account`) 함수를 재정비합니다.
- `transaction_cash`가 포트폴리오 예수금에 미치는 연산식을 구현합니다.

### 5단계: FastAPI 라우터 단수화 및 규격 맞춤 (`routers/`)
기존 복수형 파이썬 파일을 단수형으로 분리/이름 변경하고 내부 API Endpoints를 기획서와 동기화합니다.
- `account.py` (CRUD 및 `/daily-balances` 생성/조회)
- `transaction.py` (매매 CRUD 및 역산 트리거)
- `transaction_cash.py` (현금 흐름 CRUD 및 역산 트리거)
- `stock.py` (보유 잔고 및 종목 마스터)
- `stock_ohlcv.py` (캔들 캐시 및 1분 폴링 `/refresh-prices` 트리거)
- `recommendation.py` (AI 추천 CRUD)
- `be/git/git_task.py`, `be/git/git_service.py` (경로 이동 및 역할 분리)

## 3. 검증 계획
- **자동 마이그레이션 테스트**: `migrate.py` 스크립트를 직접 실행하여 오류 없이 구동되고 SQLite 테이블 형태가 TO-BE로 바뀌는지 확인합니다.
- **API Health Check**: `uvicorn`으로 로컬 서버를 가동한 뒤 Swagger UI(`http://localhost:8000/docs`)에 모든 API가 올바른 규격(Schema)으로 노출되는지 육안 점검합니다.

## 4. 사용자 피드백 요청 (User Review Required)
> [!IMPORTANT]
> 백엔드 개발의 가장 중요한 뼈대입니다. 특히 1~2단계 진행 시 기존 데이터베이스 스키마가 완벽히 재구성되므로, 본 계획서를 승인해주시면 **`database.py` 수정과 `migrate.py` 작성을 최우선으로 진행**하겠습니다. 계획이 적절한지 승인해 주시기 바랍니다.

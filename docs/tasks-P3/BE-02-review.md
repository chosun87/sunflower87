# BE-02 리뷰: 설계 문서와 실제 코드(be) 간 구현 차이 및 누락 분석

제공해주신 프로젝트 기획/설계 문서 5종(`BE-01_Backend_Refactoring_Task.md`, `BE-01_implementation_plan.md`, `db_developer_plan.md`, `backend_developer_plan.md`, `project_analysis.md`)을 모두 면밀히 읽고, 현재 개발된 `be` (백엔드) 폴더 내의 소스 코드와 대조하여 분석했습니다.

데이터베이스 모델(`database.py`), DTO 스키마(`schemas.py`), 공통 상수(`constants.py`) 등의 뼈대는 설계서의 요구사항(3NF, 테이블명 단수화, 예약어 탈피 및 `dt_` 접두어 적용)을 완벽하게 충족하며 훌륭하게 구현되어 있습니다.

하지만 **REST API 라우터(`be/routers/`) 부분에서 설계 문서(특히 `backend_developer_plan.md`)에 명시된 다수의 엔드포인트가 아직 미구현(누락) 상태이거나 경로명이 다른 점**을 발견했습니다.

아래는 설계서와 실제 코드 간의 **차이점 및 누락되어 개설이 필요한 부분**을 정리한 내용입니다.

## 1. `account.py` (계좌 및 일자별 잔고 API)
**누락된 일자별 잔고(AccountDailyBalance) CRUD 엔드포인트:**
- `GET /api/accounts/{acc_cd}/daily-balances/{trade_date}` (특정 날짜 단일 조회) - **개설 필요**
- `POST /api/accounts/{acc_cd}/daily-balances` (커스텀 잔고 스냅샷 강제 생성/주입) - **개설 필요**
- `PUT /api/accounts/{acc_cd}/daily-balances/{trade_date}` (잔고 스냅샷 수치 수정) - **개설 필요**
- `DELETE /api/accounts/{acc_cd}/daily-balances/{trade_date}` (잔고 스냅샷 삭제) - **개설 필요**

## 2. `transaction.py` (주식 매매 거래 API)
**경로(Path) 차이점:**
- 기획서에는 생성 엔드포인트가 `POST /api/transactions/add`로 되어 있으나, 실제 코드(`router.post("")`)는 `POST /api/transactions`로 구현되어 있습니다. (설계서에 맞출지, 현재의 완전한 RESTful 패턴을 유지할지 결정 필요)

## 3. `transaction_cash.py` (현금 거래 API)
**누락된 엔드포인트:**
- `GET /api/transaction_cash/{id}` (특정 현금 거래 단일 상세 조회) - **개설 필요**
- `PUT /api/transaction_cash/{id}` (특정 현금 거래 수정) - **개설 필요**

**경로(Path) 차이점:**
- 기획서에는 prefix가 `/api/transactions_cash`(복수형)로 되어 있으나, 코드에는 `/api/transaction_cash`(단수형)로 선언되어 있습니다. (테이블명과 동일하게 단수형을 유지하는 것이 좋아 보입니다)
- 생성 엔드포인트가 기획서는 `/add`를 포함하지만, 코드는 `POST ""`로 되어있습니다.

## 4. `stock.py` (보유 잔고 및 종목 마스터 API)
**가장 누락이 많은 라우터입니다. 현재 `/portfolio`와 `/masters` 엔드포인트만 존재합니다.**
- `GET /api/stocks` (전체/특정 계좌 보유 잔고 목록 조회) - **개설 필요**
- `GET /api/stocks/{acc_cd}/{stock_code}` (특정 종목 보유고 단일 조회) - **개설 필요**
- `POST /api/stocks` (임의 보유 잔고 수동 생성) - **개설 필요**
- `PUT /api/stocks/{acc_cd}/{stock_code}` (수동 편집) - **개설 필요**
- `DELETE /api/stocks/{acc_cd}/{stock_code}` (특정 보유 잔고 삭제) - **개설 필요**
- `GET /api/stocks/search` (종목명 초고속 인메모리 검색) - **개설 필요**
- `GET /api/stocks/lookup` (코드로 한글명 조회) - **개설 필요**
- `POST /api/stocks/sync-master` (수동 마스터 강제 재크롤링) - **개설 필요**
- `POST /api/stocks/master` (커스텀 종목 마스터 생성) - **개설 필요**
- `PUT /api/stocks/master/{stock_code}` (커스텀 마스터 수정) - **개설 필요**
- `DELETE /api/stocks/master/{stock_code}` (마스터 소프트 딜리트) - **개설 필요**

## 5. `stock_ohlcv.py` (주가 OHLCV 캐시 API)
**누락된 엔드포인트:**
- `GET /api/stock_ohlcv` (특정 종목의 과거 시계열 전체 조회, *현재 `{stock_code}` path parameter로만 구현됨*) - **보완 필요**
- `GET /api/stock_ohlcv/{stock_code}/{trade_date}` (특정 영업일 단일 상세 조회) - **개설 필요**
- `POST /api/stock_ohlcv` (수동 주가 생성) - **개설 필요**
- `PUT /api/stock_ohlcv/{stock_code}/{trade_date}` (수동 주가 수정) - **개설 필요**
- `DELETE /api/stock_ohlcv/{stock_code}/{trade_date}` (캐시 레코드 삭제) - **개설 필요**

**경로(Path) 차이점:**
- 기획서에는 `POST /api/stocks/refresh-prices` 로 1분 단위 동기화를 정의했으나, 코드는 `stock_ohlcv.py` 내의 `POST /refresh` (즉, `/api/stock_ohlcv/refresh`)로 구현되어 있습니다.

## 6. `recommendation.py` (AI 추천 API)
**누락된 엔드포인트:**
- `GET /api/recommendations/{stock_code}` (단일 상세 조회) - **개설 필요**
- `PATCH /api/recommendations/{stock_code}/feedback` (투자자 의견 피드백 점수 부여 기능) - **개설 필요**

---

### 💡 요약 및 권장 사항
현재 DB 모델 및 Pydantic 스키마 설계는 모두 완성되어 있으므로 비즈니스 로직 적용에 무리가 없습니다. **누락된 CRUD 라우터들을 추가로 개설**하고 기획서에 명시된 라우터 경로(Path) 규칙(예: `/add` 접미사를 쓸 것인지, 순수 REST 방식을 쓸 것인지)에 대한 기준만 한 번 더 확립하여 개발을 진행하면 될 것 같습니다.

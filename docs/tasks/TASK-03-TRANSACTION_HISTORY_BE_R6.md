# TASK-03: SQLite 내 account 테이블 신설 및 acc_code 기반 자산 격리 API 구현 (_BE_R6)

- **작성일:** 2026. 05. 17
- **작성자:** 기획자 MOON(무니)
- **승인자:** 의사결정권자 SUN(써니)
- **담당자:** EARTH-BE(어띠베)

---

## 📌 [COMMON] 공통 요구사항
- **계좌 마스터 데이터베이스화:** 하드코딩 방식의 계좌 관리를 철회하고, SQLite DB 내에 `account` 테이블을 신설하여 계좌 데이터를 관리한다.
- **네이밍 컨벤션 표준화:** 계좌 테이블의 컬럼명은 지정된 약어 규칙을 준수하며, 타 테이블(`transactions`, `stocks`)과의 외래키 연결 고리는 **`acc_code`**로 전면 통일하여 명확성을 확보한다.

---

## 🌍 [BE_TASK] 백엔드 상세 구현 지침

### 1. 작업 디렉토리: `be/`

### 2. SQLite 데이터베이스 `account` 테이블 신설 (Schema)
`SQLAlchemy` 모델을 활용하여 아래 스펙에 지정된 명칭 그대로 계좌 마스터 테이블을 생성하라.
- **`account` 테이블 정의:**
  - `acc_cd`: String (Primary Key, 내부 관리용 계좌 고유 코드 - 예: 'A001', 'A002')
  - `acc_nm`: String (계좌 별칭 - 예: '주식계좌 1', '연금계좌')
  - `acc_company_nm`: String (증권사/금융기관명 - 예: '미래에셋증권')
  - `acc_order`: Integer (사용자 화면 노출 정렬 순서, Default: 1)
  - `cash_balance`: Float (계좌 내 보유 현금 예수금 잔액, Default: 0.0)
  - `dt_created`: DateTime (계좌 등록 일시, 기본값: 현재시각)
  - `dt_deleted`: DateTime (계좌 삭제/해지 일시, Nullable)

### 3. 연관 테이블 외래키(FK) 연동 패치
- `transactions` 및 `stocks` 테이블에 존재하던 기존 계좌 식별 컬럼(`account_number` 등)을 전부 **`acc_code` (String)** 로 전면 교체하라. (이 `acc_code` 값은 `account` 테이블의 `acc_cd` 값을 참조한다.)
- `stocks(현재고)` 테이블은 계좌별 보유 잔고 격리를 위해 `acc_code` + `code`(종목코드) 복합 키(Composite Key) 구조를 유지하라.

### 4. API 엔드포인트 개정 및 자산 연동 (FastAPI)
- **`GET /api/accounts`:** `account` 테이블에서 `dt_deleted`가 없는 활성 계좌들을 정렬 순서(`ORDER BY acc_order ASC`)대로 조회하여 반환하라.
- **`POST /api/transactions/add`:**
  - 수신 DTO의 계좌 식별 파라미터명을 `acc_code`로 정의하라.
  - 매수/매도 트랜잭션 가동 시, `stocks` 테이블에서 `WHERE acc_code = :acc_code AND code = :code` 조건으로 현재고를 보정하라.
  - **예수금 연동:** 매수 시에는 해당 계좌의 `cash_balance`에서 (수량 × 단가)만큼 차감하고, 매도 시에는 합산하도록 단일 트랜잭션 내에서 `account` 테이블도 동시 업데이트하라.

---

## 🏁 완료 조건
1. `sunflower87.db` 내에 지정된 7개 약어 규격의 `account` 테이블이 정상 생성되는가?
2. `transactions` 및 `stocks` 테이블의 계좌 매핑 키가 `acc_code`로 완벽히 리팩토링되었는가?
3. Python 소스코드에 `black` 포맷터 및 `flake8` 린트 규칙이 에러 없이 통과되는가?

# [Phase 7] 데이터베이스 및 OHLCV 데이터 분리 개편 기획서

## 1. 개요
* **목적**: 테이블 명칭을 직관적으로 변경하고, 일별(Daily) 데이터와 실시간(Current) 데이터를 분리하여 시스템 안정성과 관리 효율성을 증대합니다.
* **주요 변경 사항**:
  1. 테이블명 변경 (`account_balance_daily` -> `account_balance_daily`, `stock_ohlcv_cache` -> `stock_ohlcv_daily`)
  2. 실시간 시세 전용 테이블 신설 (`stock_ohlcv_current`)
  3. OHLCV 테이블 컬럼 재정비 (테이블 용도별 컬럼 차별화 적용)
  4. Daily/Realtime 데이터 분리에 따른 데이터 수집 및 조회 프로세스 분리 적용

## 2. 상세 기획 내용

### 2.1. 테이블명 변경 및 신설
1. **account_balance_daily** (기존: `account_balance_daily`)
   - 네이밍 규칙 통일 (`명사_명사_주기` 형태 적용)
2. **stock_ohlcv_daily** (기존: `stock_ohlcv_cache`)
   - pykrx API를 통해 수집되는 **일일 시/고/저/종가 및 거래량** 데이터만 저장하도록 목적 명확화.
   - 추가 속성: `dt_updated` (수신 및 업데이트 일시 기록용 컬럼)
3. **stock_ohlcv_current** (신규)
   - 네이버 API를 통해 수집되는 **실시간** 시/고/저/종가, 거래량 데이터 저장 전용.
   - 추가 속성: `dt_updated` (수신 및 업데이트 일시 기록용 컬럼)

### 2.2. OHLCV 관련 컬럼 정리 (테이블별 분리 정책)
- **`stock_ohlcv_daily`**: pykrx API에서 기본 제공하는 데이터이므로 기존 컬럼인 `trading_value`(거래대금), `fluctuation_rate`(등락률)를 모두 **유지**합니다.
- **`stock_ohlcv_current`**: 네이버 실시간 API 응답 구조에 맞게 테이블 스키마를 구성합니다.
  - `trading_value` 컬럼: **제거** (사용하지 않음)
  - 기존 `fluctuation_rate` 대신 네이버 API 응답 명칭에 맞춰 **`change_rate`**(등락률, cr)와 **`change_value`**(대비/전일비, cv) 컬럼을 **신규 추가**하여 저장합니다.

### 2.3. Daily 데이터와 실시간 데이터 분리에 따른 프로세스 변경
- **데이터 수집 로직 분리**: 
  - `Daily`: 장 마감 후 또는 자정 등 정해진 배치 시간에만 pykrx API를 호출하여 `stock_ohlcv_daily` 업데이트.
  - `Real-time`: 장 운영 시간 중에는 네이버 API를 호출하여 `stock_ohlcv_current`를 지속적으로 갱신.
- **조회 및 응답 분리**:
  - 사용자에게 과거 차트나 일별 변동 내역을 제공할 때는 `stock_ohlcv_daily` 참조하고, 오늘 날짜 데이터를 같이 보여줘야 하는 경우엔 `stock_ohlcv_current`를 UNION 하여 보여줍니다.
  - 사용자 화면에서 현재가 위젯 등을 렌더링할 때는 `stock_ohlcv_current` 우선 참조.

---

## 3. 담당자별 작업 지시서

### @DB (데이터베이스 전문가 - SQLite)
- [ ] `account_balance_daily` 테이블을 `account_balance_daily`로 RENAME 하는 마이그레이션 스크립트 작성.
- [ ] `stock_ohlcv_cache` 테이블을 `stock_ohlcv_daily`로 RENAME.
- [ ] `stock_ohlcv_daily` 테이블에 `dt_updated` (DATETIME) 컬럼 추가 마이그레이션 적용.
- [ ] 신규 테이블 `stock_ohlcv_current` 생성 스크립트 작성 (`dt_updated`, `change_rate`, `change_value` 포함 / `trading_value`, `fluctuation_rate` 제외).
- [ ] `stock_ohlcv_daily` 테이블은 기존대로 `trading_value`, `fluctuation_rate` 컬럼 유지.

### @BE (백엔드 개발자 - Python/FastAPI)
- [ ] 애플리케이션 내 ORM 모델(SQLAlchemy 등) 이름 변경 (`account_balance_daily`, `stock_ohlcv_daily`).
- [ ] 신규 테이블 `stock_ohlcv_current`에 대응하는 ORM 모델 추가.
- [ ] **데이터 수집 로직 수정**:
  - 기존 pykrx 로직: `stock_ohlcv_daily` 저장 및 `dt_updated` 반영하도록 수정.
  - 네이버 API 연동 로직: 실시간 데이터 수집 시 `stock_ohlcv_current`에 저장하고 `dt_updated` 반영하도록 구현.
- [ ] **API 응답 매핑 수정**: 
  - `_daily` 수집 로직은 기존 유지 (`trading_value`, `fluctuation_rate`).
  - `_current` 수집 로직은 네이버 API의 `cr` 필드를 `change_rate`에, `cv` 필드를 `change_value`에 매핑하여 저장.
- [ ] FE 파트에서 과거/실시간 OHLCV 데이터를 용도에 맞게 효율적으로 호출할 수 있도록 분리된 조회 API 제공 및 `BE-API 규격서.md` 갱신.

### @FE (프론트엔드 개발자 - React)
- [ ] `account_balance_daily` 등 BE API 응답 JSON 키값이 변경되는 경우, 화면의 데이터 바인딩 일괄 수정.
- [ ] 과거 데이터(차트 등)와 실시간 현재가를 요청하는 API 엔드포인트 변경에 맞춰 쿼리(fetch) 분리 작업.

---

## 개발자 의견
> **@DB**: (내용을 입력해주세요)

> **@BE**: (내용을 입력해주세요)

> **@FE**: (내용을 입력해주세요)

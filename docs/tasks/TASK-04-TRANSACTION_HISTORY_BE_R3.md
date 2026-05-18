# TASK-04: 세금+수수료(tax_fee) 필드 확장 및 시계열 자산 평가 API 구현 (_BE_R3)

- **작성일:** 2026. 05. 18
- **작성자:** 기획자 MOON(무니)
- **승인자:** 의사결정권자 SUN(써니)
- **담당자:** EARTH-BE(어띠베)

---

## 📌 [COMMON] 공통 요구사항
- **원장 데이터 스키마 확장 (★핵심):** 매매 내역 기록 시 거래 비용을 정밀 반영하기 위해 세금 및 수수료 통합 필드인 **`tax_fee`**를 추가한다.
- **네이밍 컨벤션 표준화:** 계좌 마스터 정보 조회 시 DB 컬럼명과 API 응답 객체의 Key(Alias) 명칭을 인위적 변형 없이 `acc_cd`, `acc_nm`, `acc_company_nm`으로 1:1 일치시킨다.
- **16시 마감 타임윈도우 적용:** 당일 최종 시세가 확정되는 오후 4시(16:00)를 기준으로 60거래일치 데이터 수집 대상 종료일을 동적으로 제어한다.

---

## 🌍 [BE_TASK] 백엔드 상세 구현 지침

### 1. SQLite 거래 원장 테이블 스키마 개정 (`transactions`)
- `transactions` 테이블에 세금 및 수수료를 적재할 신규 컬럼을 추가하라.
  - **`tax_fee` (INTEGER 또는 REAL, DEFAULT 0)**
- 매매 기록 등록 API(`POST /api/transactions/add`)의 Request Body(Pydantic 모델) 규격에 `tax_fee` 필드를 신설하고, 원장 데이터 인서트 쿼리에 이를 바인딩하라.

### 2. 계좌 마스터 조회 API 데이터 매핑 규칙 (Alias 통일)
- `GET /api/accounts` API 응답 작성 시 변수명 변형 규칙을 철저히 금지하고 컬럼명과 완전하게 일치시켜 송출하라.
  ```python
  account_response = {
      "acc_cd": row["acc_cd"],
      "acc_nm": row["acc_nm"],
      "acc_company_nm": row["acc_company_nm"],
      "cash_balance": row["cash_balance"]
  }
  ```

### 3. 16시 기준 동적 날짜 역산 및 하이브리드 수집 파이프라인
- `get_exact_trade_date_limits()` 유틸리티 함수를 가동하여 16시 이전에는 전일 종가, 16시 이후에는 당일 확정 종가를 기점으로 정확히 60거래일치 행을 확보하라.
- 거래일 기준 공백이 120일 이하인 종목 재매수 시 유실된 구간만 백필(Backfill)하고, 120일 초과 시 과거 캐시를 `DELETE` 후 일괄 재적재하라.

---

## 🏁 완료 조건
1. `POST /api/transactions/add` 호출 시 `tax_fee` 데이터가 SQLite 원장 테이블에 정상적으로 인서트되는가?
2. API 응답 JSON의 Key값이 `acc_nm`, `acc_company_nm`으로 DB 원장 명칭과 1:1 매핑되어 출력되는가?
3. 모든 데이터 핸들러에서 계좌 식별자는 `acc_cd` 표준을 예외 없이 준수하는가?

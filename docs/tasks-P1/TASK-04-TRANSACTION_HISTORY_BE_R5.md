# TASK-04: 총 매수금액 0원(Zero) 및 분모 제어 예외 처리 자산 평가 API 구현 (_BE_R5)

- **작성일:** 2026. 05. 19
- **작성자:** 기획자 MOON(무니)
- **승인자:** 의사결정권자 SUN(써니)
- **담당자:** EARTH-BE(어띠베)

---

## 📌 [COMMON] 공통 요구사항
- **Zero-Value 예외 처리 (★최종 확정):** 신규 계좌이거나 특정 종목을 전량 매도하여 총 매수금액 또는 보유수량이 `0`인 경우, 시스템 내부적으로 `ZeroDivisionError`가 발생하지 않도록 완벽한 널 방어 분기 처리를 수행한다.
- **네이밍 컨벤션 표준화:** 계좌 마스터 정보 조회 시 DB 컬럼명과 API 응답 객체의 Key(Alias) 명칭은 무조건 `acc_cd`, `acc_nm`, `acc_company_nm` 표준을 고수한다.

---

## 🌍 [BE_TASK] 백엔드 상세 구현 지침

### 1. 자산 평가 API (`GET /api/accounts`) Zero-Value 방어 정산 쿼리 개정
어띠베는 DB에서 거래 내역을 합산할 때 매수 이력이 없는 경우(`NULL`) 또는 총합이 `0`인 경우를 대비해 아래 예외 처리 알고리즘을 반드시 적용하라.

* **총 매수금액 (`total_purchase_amt`) 0원 방어:**
    - SQL `COALESCE(SUM(quantity * price + tax_fee), 0)` 처리를 통해 거래 내역이 없으면 무조건 `0`을 반환하도록 설계하라.
* **매입평단가 (`avg_price`) 및 수익률 (`return_rate`) 계산 예외 처리:**
    - **[Case 1] 보유수량(`quantity`)이 0이거나 총 매수금액이 0인 경우:**
      - `avg_price = 0`
      - `return_rate = 0.0`
      - 으로 강제 셋팅하여 0으로 나누는 런타임 크래시를 원천 방어하라.
    - **[Case 2] 정상 자산인 경우:**
      - `avg_price = total_purchase_amt / quantity`
      - `return_rate = ((total_eval_amt - total_purchase_amt) / total_purchase_amt) * 100`

### 2. SQLite 거래 원장 테이블 스키마 (`transactions`)
- `transactions` 테이블의 세금 및 수수료 컬럼 `tax_fee` (INTEGER, DEFAULT 0) 및 매매 등록 API(`POST /api/transactions/add`)의 데이터 인서트 바인딩 구조를 견고히 유지하라.

### 3. 계좌 마스터 조회 API 데이터 매핑 및 16시 타임윈도우 유틸리티
- `GET /api/accounts` API 응답 Key명은 DB 컬럼명과 동일하게 `acc_cd`, `acc_nm`, `acc_company_nm`, `cash_balance`로 출력하라.
- `get_exact_trade_date_limits()` 유틸리티 함수를 가동하여 16시 이전에는 전일 종가, 16시 이후에는 당일 확정 종가를 기점으로 정확히 60거래일치 행을 확보하라.

---

## 🏁 완료 조건
1. 매매 기록이 전혀 없는 신규 계좌 조회 시 `total_purchase_amt`, `avg_price`, `return_rate`가 에러 없이 정확히 `0`으로 서빙되는가?
2. API 응답 JSON의 Key값이 `acc_nm`, `acc_company_nm`으로 DB 원장 명칭과 1:1 매핑되어 출력되는가?
3. 모든 데이터 핸들러에서 계좌 식별자는 `acc_cd` 표준을 예외 없이 준수하는가?

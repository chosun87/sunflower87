# Account Daily Balance 산출 및 백필(Backfill) 제안

과거부터 현재까지 계좌의 일자별 잔고(`account_daily_balance`)를 생성하고 유지하기 위한 계산 방법 및 아키텍처 제안입니다. 

## 1. 산출 로직 설계 (이벤트 소싱 기반)

계좌별로 모든 현금/주식 거래 내역을 시간순으로 재생(Replay)하여 매일 자정(장 마감 후) 기준의 스냅샷을 생성합니다.

### 상태(State) 관리 요소
일별 스냅샷을 찍기 위해 메모리에서 다음 상태를 유지하며 날짜별로 시뮬레이션합니다.
*   **`current_cash_balance`**: 현재 현금 잔고 (초기 0부터 시작)
*   **`holdings`**: 보유 주식 목록 (종목코드 -> 보유 수량)
*   **`total_principal`**: 누적 투자 원금 (총 입금액 - 총 출금액)

### 일간(Daily) 시뮬레이션 알고리즘
1.  **영업일(Trading Days) 목록 산출**: `stock_ohlcv_cache`에 존재하는 `trade_date`를 고유값(DISTINCT)으로 추출하여, 과거부터 현재까지 **실제 장이 열린 영업일(주말, 공휴일 제외)** 목록만 순회합니다.
2.  **당일 거래 반영**: 기준일(`D`)에 발생한 모든 `Transaction`(주식 매매)과 `TransactionCash`(입출금, 배당 등) 내역을 상태에 반영합니다.
    *   입출금 발생 시: `current_cash_balance` 및 `total_principal` 업데이트
    *   주식 매수/매도 발생 시: `current_cash_balance` 차감/증가 및 `holdings` 수량 업데이트
3.  **종가(Close Price) 매핑**: 기준일(`D`)의 종가를 `stock_ohlcv_cache` 테이블에서 조회합니다.
    *   *주의:* 주말이나 공휴일처럼 당일 종가 데이터가 없는 경우, **가장 최근 영업일의 종가**를 가져와야 합니다. (예: 일요일 잔고 계산 시 금요일 종가 사용)
4.  **일별 스냅샷 지표 계산**:
    *   `stock_eval_balance` (주식 평가금) = $\sum (\text{보유 수량} \times \text{당일 기준 종가})$
    *   `total_balance` (총 자산) = `current_cash_balance` + `stock_eval_balance`
    *   `return_rate` (수익률) = `(total_balance - total_principal) / total_principal * 100`
5.  **DB 저장**: 계산된 지표를 `account_daily_balance` 테이블에 `trade_date = D` 로 INSERT/UPDATE 합니다.

---

## 2. 데이터 최신화 트리거 정책 (When to calculate)

과거 데이터 백필(Backfill)이 완료된 이후, 최신 일간 잔고를 유지하기 위한 3가지 동작 방식을 제안합니다.

*   **배치 스케줄러 (Daily Batch)**: 매일 장 마감 이후 또는 자정(00:00)에 스케줄러(예: APScheduler)가 동작하여 전일자 잔고 스냅샷을 자동으로 생성합니다.
*   **과거 내역 수정 시 자동 연쇄 계산 (Cascading Recalculation)**: 사용자가 과거의 주식 거래나 입출금 내역을 추가/수정/삭제하는 경우, **해당 거래일자부터 오늘까지의 일간 잔고 스냅샷을 모두 다시 계산(Overwrite)**하도록 이벤트 핸들러를 추가합니다.
*   **Lazy Loading (접속 시 검증)**: 대시보드 진입 시, 어제 일자의 `account_daily_balance` 레코드가 없다면 즉시 어제까지의 계산 로직을 백그라운드로 돌리거나 동기적으로 돌려 누락을 방지합니다.

---

> [!IMPORTANT]
---

## 3. 사용자 피드백 반영 (의사결정 완료)

1. **원금 계산 기준**: **순 입금액 (총 DEPOSIT - 총 WITHDRAW)** 기준으로 산출하여 수익률(`return_rate`)을 계산합니다. 이자, 배당금 등은 수익으로만 산정됩니다.
2. **최신화 동기화 시점 (하이브리드 방식)**:
   - **백엔드 시작 시점 (Startup)**: FastAPI 앱 구동 시 1회 전체 계좌에 대해 누락된 잔고 동기화를 수행합니다. (프론트엔드 API 호출 불필요)
   - **자정 배치 스케줄러 (Midnight Batch)**: 서버가 24시간 실행될 경우를 대비해, 매일 새벽(예: 00시 30분)에 스케줄러(`APScheduler`)가 돌아가며 전날까지의 데이터를 채워 넣습니다.
3. **휴장일 처리**: `stock_ohlcv_cache`의 `trade_date`를 순회 기준으로 삼아 **주말, 공휴일 등 실제 휴장일은 자동으로 스냅샷 생성 대상에서 제외**됩니다.

# 04_kpi_dashboard_plan.md: 대시보드 KPI(핵심 성과 지표) 산출 로직 및 API 기획서

프론트엔드 대시보드 최상단에 노출될 **4대 핵심 KPI(오늘, 금월, 금년, 총 누적 수익)**를 정확하게 계산하고 반환하기 위한 백엔드 API 설계 및 비즈니스 로직 기획입니다.

## 1. 비즈니스 로직: 투자 원금 및 수익금 산정 기준

정확한 수익률을 계산하려면 주가 변동에 의한 자산 증가와, 사용자가 단순히 돈을 입금해서 자산이 증가한 것을 완벽히 분리해야 합니다. (이를 **외부 현금 흐름(External Cash Flow) 통제**라고 합니다.)

### 📌 총 평가 자산 및 총 투자 원금 정의
- **총 평가 자산 (Total Asset)** = `계좌 예수금(cash_balance)` + `Σ (보유주식 수량 × 실시간 현재가)`
- **총 투자 원금 (Total Principal)** = `Σ 입금(DEPOSIT)` - `Σ 출금(WITHDRAW)`
  - *참고 1: 각 계좌의 최초 자본금(`initial_cash`)은 0으로 시작하므로, 원금은 순수 누적 입출금액만으로 산정됩니다.*
  - *참고 2: 이자(INTEREST)와 배당금(DIVIDEND)은 사용자가 외부에서 투입한 원금이 아니라 투자 활동으로 발생한 **수익**이므로 원금에 합산하지 않고, 자산 증가(즉, 수익금 증가)로만 잡힙니다.*
- **총 투자 수익금 (Total Profit)** = `총 평가 자산` - `총 투자 원금`
- **총 수익률 (Total Return Rate)** = (`총 투자 수익금` / `총 투자 원금`) × 100 (%)

### 📌 기간별 수익금 및 수익률 정의 (오늘 / 금월 / 금년)
특정 기간(예: 금월)의 수익(단순 자산 증가분)을 계산하기 위해 **기초 자산(해당 기간 직전일의 최종 자산)**과 **기말 자산(현재 실시간 자산)**을 직접 비교합니다.

- **기초 자산 ($A_{start}$)**: `account_balance_daily` 테이블에서 해당 기간 직전 영업일의 `total_balance` 스냅샷을 조회합니다.
  - **오늘**: 전일(어제)의 최종 잔고 스냅샷 대비 금일 최종 잔고
  - **금월**: 전월 마지막 날의 최종 잔고 스냅샷 대비 금일 최종 잔고
  - **금년**: 작년 마지막 날의 최종 잔고 스냅샷 대비 금일 최종 잔고
- **기말 자산 ($A_{end}$)**: 실시간 총 평가 자산 (위에서 구한 Total Asset)

#### 🧮 공식 (Formula)
- **기간 투자 수익금 (Period Profit)** = $A_{end} - A_{start}$
- **기간 수익률 (Period Return Rate)** = `Period Profit` / $A_{start}$ × 100 (%)
  *(단순 스냅샷 비교 방식으로 기간 내 순입금액(Net Deposit)은 수식에서 제외합니다. 단, 기초 자산이 0일 경우 수익률은 0%로 간주합니다.)*

---

## 2. 신규 API 엔드포인트 명세

위 수식을 백엔드에서 고속 연산하여 프론트엔드로 전달할 전용 엔드포인트를 신설합니다.

### 🌐 `GET /api/dashboard/kpi`
- **위치**: `be/routers/dashboard.py` (신규 파일)
- **설명**: 전체 계좌를 합산한 대시보드용 4대 KPI 종합 지표 반환 (특정 계좌만 보고 싶을 경우 `?acc_cd=` 쿼리 파라미터 지원)
- **내부 로직 (Internal Process)**:
  1. `account`, `stock` 테이블을 바탕으로 **현재 실시간 총 자산** 연산
  2. `transaction_cash` 테이블을 조회해 오늘/이번달/올해 기간 동안의 **순입금액(Net Deposit)** 집계
  3. `account_balance_daily` 테이블에서 어제, 전월 말, 전년 말의 **기초 자산 스냅샷** 조회
  4. 4가지 지표에 대해 위 공식에 따라 병렬 계산 후 DTO 조립
- **Response Payload (JSON)**:
```json
{
  "status": "success",
  "data": {
    "today": {
      "profit": 150000,
      "return_rate": 0.52
    },
    "this_month": {
      "profit": 1250000,
      "return_rate": 4.15
    },
    "this_year": {
      "profit": -500000,
      "return_rate": -1.25
    },
    "total": {
      "total_asset": 35000000,
      "total_principal": 30000000,
      "profit": 5000000,
      "return_rate": 16.67
    }
  }
}
```

---

## 3. 구현 프로세스 (Implementation Steps)

1. **`be/schemas.py` 업데이트**: `DashboardKPIData`, `DashboardKPIResponse` 등 중첩 JSON 규격에 맞는 Pydantic Response 모델 신규 선언
2. **`be/portfolio.py` 확장**: `get_dashboard_kpi(db, acc_cd=None)` 형태의 전용 금융 연산 엔진 함수 신규 작성 (날짜 연산 및 쿼리 최적화 포함)
3. **`be/routers/dashboard.py` 라우터 신설**: 프론트엔드 대시보드 전용 라우터 생성 및 `GET /api/dashboard/kpi` 탑재 (FastAPI `main.py`에 라우터 등록 추가)
4. (향후) 프론트엔드 연동 및 대시보드 카드 렌더링

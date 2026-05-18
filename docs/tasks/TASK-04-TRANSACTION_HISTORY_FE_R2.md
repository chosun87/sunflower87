# TASK-04: 시점 분기형 종가 기반 자산 평가 및 고도화된 그리드 스타일링 UI 구현 (_FE_R2)

- **작성일:** 2026. 05. 18
- **작성자:** 기획자 MOON(무니)
- **승인자:** 의사결정권자 SUN(써니)
- **담당자:** EARTH-FE(어띠페)

---

## 📌 [COMMON] 공통 요구사항
- **글로벌 파이낸스 디자인 톤 적용:** 주가 상승/평가익/매수는 파란색(`var(--blue-600)`), 주가 하락/평가손/매도는 빨간색(`var(--red-600)`)으로 컬러 브레이크를 적용한다.
- **가시성 극대화:** 정렬 규칙(Align), 모노스페이스 폰트 클래스(`.monospace`), PrimeReact `Badge`를 적극 활용하여 금융 대시보드의 데이터 Scannability(독해 가시성)를 확보한다.
- **네이밍 컨벤션:** 계좌 고유 식별자 명칭은 무조건 **`acc_cd`** 표준을 고수한다.

---

## 🌍 [FE_TASK] 프런트엔드 상세 구현 지침

### 1. 작업 디렉토리: `fe/`

### 2. [탭 1: 보유 자산 상세] DataTable 컬럼 확장 및 스타일 스펙
보유 자산 상세 그리드의 컬럼 순서 및 인라인 스타일을 아래 규격에 한 치의 오차도 없이 맞추어라.

* **컬럼 구성 및 순서:**
    1. **종목코드** (`code`) : `align-left`, `.monospace` 클래스 적용
    2. **종목명** (`name`) : `align-left`
    3. **보유수량** (`quantity`) : `align-right`, `.monospace` 클래스 적용, 천 단위 콤마
    4. **현재가** (`current_price`) : `align-right`, `.monospace` 클래스 적용, 천 단위 콤마
    5. **매입평단가** (`avg_price`) : `align-right`, `.monospace` 클래스 적용, 천 단위 콤마
    6. **총 평가금액** (`quantity * current_price`) : `align-right`, `.monospace` 클래스 적용, 천 단위 콤마
    7. **총 매수금액** (`quantity * avg_price`) : `align-right`, `.monospace` 클래스 적용, 천 단위 콤마
    8. **총 평가손익** : `align-right`, `.monospace` 클래스 적용, 천 단위 콤마
       - 연산 결과가 **플러스(+)이면 `color: var(--blue-600)`**, **마이너스(-)이면 `color: var(--red-600)`** 적용
    9. **수익률** : `align-right`, `.monospace` 클래스 적용, `.toFixed(2)` 포맷
       - 연산 결과가 **플러스(+)이면 `color: var(--blue-600)`**, **마이너스(-)이면 `color: var(--red-600)`** 적용

### 3. [탭 2: 매매 내역 히스토리] DataTable 컬럼 스타일 스펙
기존 컬럼 순서를 엄격히 유지하되, 세부 스타일 기획 사양을 결합하라.

* **포맷터 및 정렬 규칙:**
    - 날짜, 시간, 수량, 단가, 금액 등 숫자로 구성된 모든 컬럼에 **`.monospace`** 클래스를 주입하라.
    - 수량, 단가, 거래 금액 컬럼은 우측 정렬(`text-align: right`)로 배치하라.
* **★ 구분 컬럼 디자인 (`Badge` 도입):**
    - `@components/PrimeReact`에서 **`Badge`** 컴포넌트를 import 하라.
    - **매수(BUY):** `<Badge value="매수" severity="info" style={{ backgroundColor: 'var(--blue-600)', color: '#fff' }} />`
    - **매도(SELL):** `<Badge value="매도" severity="danger" style={{ backgroundColor: 'var(--red-600)', color: '#fff' }} />`

### 4. API 연동 및 예수금(Cash Balance) 레이아웃
- 계좌 선택 Dropdown은 `optionValue="acc_cd"` 규격으로 호출 바디를 유지하라.
- 테이블 상단 배너에 `cash_balance` 현금 잔고 뷰를 깔끔하게 출력하고, 매매 모달이 닫히는 즉시 `fetchAccountData()`를 통해 탭 1, 탭 2의 데이터가 동시에 백필 및 리프레시되는 구조를 양립하라.

---

## 🏁 완료 조건
1. 보유 자산 테이블의 컬럼 순서가 기획서 명세와 일치하며 수량/금액 라인이 우측으로 깔끔하게 정렬되는가?
2. 총 평가손익과 수익률, 매매 구분의 컬러 라인이 플러스=파란색(`--blue-600`), 마이너스=빨간색(`--red-600`) 규칙을 정확하게 따르는가?
3. 모든 숫자형 데이터 컬럼 텍스트에 고정폭 글꼴 클래스(`.monospace`)가 누락 없이 주입되었는가?

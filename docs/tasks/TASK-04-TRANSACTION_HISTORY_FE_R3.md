# TASK-04: API 규격 정규화 및 가시성 고도화 그리드 스타일링 UI 구현 (_FE_R3)

- **작성일:** 2026. 05. 18
- **작성자:** 기획자 MOON(무니)
- **승인자:** 의사결정권자 SUN(써니)
- **담당자:** EARTH-FE(어띠페)

---

## 📌 [COMMON] 공통 요구사항
- **백엔드 API 규격 완벽 동기화 (★핵심):** 백엔드 R2의 네이밍 정규화 정책에 따라, 계좌 조회(`GET /api/accounts`) 시 응답 데이터의 Key값이 **`acc_nm`** 및 **`acc_company_nm`**으로 전달되므로, 프런트엔드는 임의의 맵핑(`acc_name` 등)을 전면 제거하고 백엔드 Key 규격을 1:1로 바인딩한다.
- **글로벌 파이낸스 디자인 톤 적용:** 주가 상승/평가익/매수는 파란색(`var(--blue-600)`), 주가 하락/평가손/매도는 빨간색(`var(--red-600)`)으로 컬러 브레이크를 일관되게 적용한다.
- **가시성 통제:** 정렬 규칙(Align), 고정폭 폰트 클래스(`.monospace`), PrimeReact `Badge`를 전격 도입한다.
- **네이밍 컨벤션:** 계좌 고유 식별자 명칭은 소스코드 전반에서 무조건 **`acc_cd`** 표준명만 사용한다.

---

## 🌍 [FE_TASK] 프런트엔드 상세 구현 지침

### 1. 작업 디렉토리: `fe/`

### 2. 계좌 선택 Dropdown 및 예수금 배너 데이터 바인딩 수정
- **Dropdown 컴포넌트 규격 싱크:** `GET /api/accounts` API 응답 구조 변동에 맞춰 아래 사양으로 맵핑하라.
  - 노출 라벨: `optionLabel="acc_nm"` (기존 `acc_name`에서 수정)
  - 실제 바인딩 Value: `optionValue="acc_cd"`
- **예수금 및 증권사 출력:** 배너 영역에 계좌 정보 렌더링 시 **`acc_company_nm`** 필드를 활용하여 소속 증권사명을 표기하라.

### 3. [탭 1: 보유 자산 상세] DataTable 컬럼 확장 및 스타일 스펙
보유 자산 상세 그리드의 컬럼 순서, 정렬 및 인라인 스타일을 아래 규격에 기계적으로 일치시켜라.

* **컬럼 구성 및 순서:**
    1. **종목코드** (`code`) : `align-left`, `.monospace` 클래스 적용
    2. **종목명** (`name`) : `align-left`
    3. **보유수량** (`quantity`) : `text-align: right`, `.monospace` 클래스 적용, 천 단위 콤마(`toLocaleString()`)
    4. **현재가** (`current_price`) : `text-align: right`, `.monospace` 클래스 적용, 천 단위 콤마
    5. **매입평단가** (`avg_price`) : `text-align: right`, `.monospace` 클래스 적용, 천 단위 콤마
    6. **총 평가금액** (`quantity * current_price`) : `text-align: right`, `.monospace` 클래스 적용, 천 단위 콤마
    7. **총 매수금액** (`quantity * avg_price`) : `text-align: right`, `.monospace` 클래스 적용, 천 단위 콤마
    8. **총 평가손익** : `text-align: right`, `.monospace` 클래스 적용, 천 단위 콤마
       - 연산 결과(평가금액 - 매수금액)가 **플러스(+)이면 `color: var(--blue-600)`**, **마이너스(-)이면 `color: var(--red-600)`** 적용
    9. **수익률** : `text-align: right`, `.monospace` 클래스 적용, 소수점 아래 둘째 자리 제한(`.toFixed(2)`)
       - 연산 결과가 **플러스(+)이면 `color: var(--blue-600)`**, **마이너스(-)이면 `color: var(--red-600)`** 적용

### 4. [탭 2: 매매 내역 히스토리] DataTable 컬럼 스타일 스펙
기존 컬럼 순서를 엄격히 유지하되, 아래 스타일 가이드라인을 강제 주입하라.

* **포맷터 및 정렬 규칙:**
    - 날짜, 시간, 수량, 단가, 금액 등 숫자로 구성된 모든 컬럼에 **`.monospace`** 클래스를 적용하라.
    - 수량, 단가, 거래 금액 컬럼은 우측 정렬(`text-align: right`)로 배치하라.
* **구분 컬럼 디자인 (`Badge` 도입):**
    - `@components/PrimeReact`에서 **`Badge`** 컴포넌트를 호출하라.
    - **매수(BUY):** `<Badge value="매수" style={{ backgroundColor: 'var(--blue-600)', color: '#fff' }} />`
    - **매도(SELL):** `<Badge value="매도" style={{ backgroundColor: 'var(--red-600)', color: '#fff' }} />`

### 5. API 트랜잭션 수립 및 락(Lock) 핸들러
- 매매 폼 등록 완료 제출 시 계좌 키 파라미터명은 반드시 **`acc_cd`** 규격으로 JSON Body를 감싸 송출하라.
- 등록 처리 중 지연이 발생할 때 중복 클릭을 차단하기 위해 등록 버튼에 `loading={isSubmitting}` 속성을 활성화하라. 모달이 닫히면 `fetchAccountData()`를 강제 리프레시하라.

---

## 🏁 완료 조건
1. Dropdown 및 배너의 데이터 바인딩 Key가 `acc_nm`, `acc_company_nm` 프로토콜과 정밀하게 일치하는가?
2. 보유 자산 상세 그리드의 9개 컬럼 순서 및 숫자의 우측 정렬 규칙이 기획서 사양과 완벽히 일치하는가?
3. 총 평가손익, 수익률, 매매 구분의 색상 반전 규칙이 플러스/매수=파란색(`--blue-600`), 마이너스/매도=빨간색(`--red-600`)으로 명밀하게 표현되는가?

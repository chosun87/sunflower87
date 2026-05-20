# TASK-04: 매매 히스토리 세금+수수료 컬럼 주입 및 가시성 고도화 UI 구현 (_FE_R4)

- **작성일:** 2026. 05. 18
- **작성자:** 기획자 MOON(무니)
- **승인자:** 의사결정권자 SUN(써니)
- **담당자:** EARTH-FE(어띠페)

---

## 📌 [COMMON] 공통 요구사항
- **매매 히스토리 그리드 확장 (★핵심):** 백엔드 원장 스펙 변동에 맞춰 [탭 2: 매매 내역 히스토리] DataTable에 세금+수수료(**`tax_fee`**) 컬럼을 정밀 배치한다.
- **글로벌 파이낸스 디자인 톤 적용:** 주가 상승/평가익/매수는 파란색(`var(--blue-600)`), 주가 하락/평가손/매도는 빨간색(`var(--red-600)`)으로 컬러 브레이크를 일관되게 적용한다.
- **가시성 통제 규칙:** 수량과 금액은 우측 정렬(`align-right`), 숫자형 컬럼은 고정폭 폰트 클래스(`.monospace`)를 엄격하게 바인딩한다.

---

## 🌍 [FE_TASK] 프런트엔드 상세 구현 지침

### 1. 작업 디렉토리: `fe/`

### 2. [탭 2: 매매 내역 히스토리] DataTable 컬럼 확장 및 정렬 스타일 규칙
기존 컬럼 순서를 유지하되, 지정된 위치에 세금+수수료 컬럼을 추가하고 스타일 가이드를 강제 주입하라.

* **컬럼 스타일 셋업 지침:**
    - 날짜, 시간, 수량, 단가, 금액, **세금+수수료** 등 숫자로 구성된 모든 데이터 셀에 **`.monospace`** 클래스를 적용하라.
    - 수량, 단가, 거래 금액, **세금+수수료** 컬럼은 우측 정렬(`text-align: right`)로 일관되게 배치하라.
* **구분 컬럼 디자인 (`Badge` 도입):**
    - **매수(BUY):** `<Badge value="매수" style={{ backgroundColor: 'var(--blue-600)', color: '#fff' }} />`
    - **매도(SELL):** `<Badge value="매도" style={{ backgroundColor: 'var(--red-600)', color: '#fff' }} />`

### 3. [탭 1: 보유 자산 상세] DataTable 컬럼 순서 사양 (R3 규격 승계)
1. **종목코드** (`code`) : `align-left`, `.monospace`
2. **종목명** (`name`) : `align-left`
3. **보유수량** (`quantity`) : `align-right`, `.monospace`, 콤마 포맷
4. **현재가** (`current_price`) : `align-right`, `.monospace`, 콤마 포맷
5. **매입평단가** (`avg_price`) : `align-right`, `.monospace`, 콤마 포맷
6. **총 평가금액** : `align-right`, `.monospace`, 콤마 포맷
7. **총 매수금액** : `align-right`, `.monospace`, 콤마 포맷
8. **총 평가손익** : `align-right`, `.monospace`, 콤마 포맷 (+ 이면 `--blue-600`, - 이면 `--red-600`)
9. **수익률** : `align-right`, `.monospace`, `.toFixed(2)` (+ 이면 `--blue-600`, - 이면 `--red-600`)

### 4. API 규격 정규화 및 수동 등록 폼 수정
- `GET /api/accounts` 연동 시 응답 객체의 Key값인 `acc_nm` 및 `acc_company_nm`을 Dropdown과 배너에 그대로 매핑하라. (임의 변형 금지)
- 매매 수동 등록 모달 창에 세금+수수료 입력용 InputNumber 컴포넌트를 신설하고, 제출 시 JSON Body에 **`tax_fee`** 키값으로 실어 `POST /api/transactions/add`로 전송하라. (계좌 키명은 `acc_cd` 고수)

---

## 🏁 완료 조건
1. 매매 내역 히스토리 탭에 세금+수수료 컬럼이 숫자의 우측 정렬 및 `.monospace` 서체 스타일과 함께 완벽히 렌더링되는가?
2. 매매 등록 폼에서 세금+수수료를 입력하여 전송 시 백엔드로 `tax_fee` 파라미터가 유실 없이 도달하는가?
3. 계좌 맵핑 Key 표준인 `acc_cd`, `acc_nm`, `acc_company_nm` 정규 규격이 프런트 단에서 빈틈없이 연동되는가?

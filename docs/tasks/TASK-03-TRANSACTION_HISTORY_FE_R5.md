# TASK-03: 매매 내역 CRUD 완비 및 계좌 연동 UI 통합 구현 (_FE_R5)

- **작성일:** 2026. 05. 17
- **작성자:** 기획자 MOON(무니)
- **승인자:** 의사결정권자 SUN(써니)
- **담당자:** EARTH-FE(어띠페)

---

## 📌 [COMMON] 공통 요구사항
- **UI 로컬라이징:** 매매 등록 창의 Calendar 컴포넌트 언어 설정을 한국어(`ko`)로 변경한다.
- **멀티 계좌 및 CRUD 완비:** 매매 기록 시 대상 계좌를 지정할 수 있는 Dropdown을 제공하고, 이미 등록된 내역에 대한 수정 및 삭제가 가능한 완벽한 원장 관리 UI를 구축한다.

---

## 🌍 [FE_TASK] 프런트엔드 상세 구현 지침

### 1. 작업 디렉토리: `fe/`

### 2. Calendar 한국어(ko) 로컬라이징 및 Dropdown 추가
- `@components/PrimeReact`에서 제공하는 로컬라이징 API(`addLocale`)를 활용하여 요일/월을 한글 딕셔너리로 세팅하고, Calendar 컴포넌트에 `locale="ko"` 속성을 부여하라.
- 등록 폼 내에 **`Dropdown`** 컴포넌트를 추가하고, 기존 계좌 조회 API(`GET /api/accounts`)의 결과 데이터를 options에 바인딩하라. (`optionLabel="alias"`, `optionValue="account_number"` 필수)

### 3. 거래 내역 테이블(DataTable) 컬럼 확장 및 [수정 / 삭제] 액션 구현
- 메인 대시보드 하단 `TabView` 내 거래 내역 `DataTable`에 **[거래 계좌] 컬럼을 신설**하여 어떤 계좌의 내역인지 배지 또는 텍스트로 노출하라.
- 테이블 최우측에 액션 컬럼을 신설하고 편집(warning)/쓰레기통(danger) 버튼을 배치하라.
  - **삭제:** 쓰레기통 클릭 시 PrimeReact **`ConfirmDialog`**를 띄워 최종 컨펌 후 `DELETE /api/transactions/{id}`를 호출하라.
  - **수정:** 편집 클릭 시 기존 등록 Dialog를 재활용하여 기존 데이터(계좌, 종목, 수량, 단가, 일시)를 Form에 바인딩하여 팝업을 오픈하고, 저장 시 `PUT /api/transactions/{id}`를 호출하라.

### 4. 상태 동기화 (Data Refresh)
- 등록, 수정, 삭제 요청이 성공할 때마다 대시보드 상위 컴포넌트의 자산 데이터 및 거래 내역 데이터를 즉시 **`Refetch`** 하여 화면 전체의 데이터 싱크를 실시간으로 맞추어라.

---

## 🏁 완료 조건
1. Calendar 렌더링 시 한글 요일이 정상 노출되며, 계좌 선택 Dropdown에 3개 계좌가 바인딩되는가?
2. 거래 내역 삭제/수정 완료 시 대시보드의 총자산과 보유 종목 테이블이 화면 깜빡임 없이 실시간 동기화되는가?
3. 모든 컴포넌트 호출 규칙 및 Lint/Prettier 포맷터 규칙을 철저히 준수했는가?

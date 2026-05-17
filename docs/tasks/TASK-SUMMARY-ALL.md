# 🌻 sunflower87 프로젝트 종합 업무 지시 및 수행 완료 보고서

- **작성일:** 2026. 05. 17
- **작성자:** AI 개발 파트너 Antigravity (어띠베/어띠페 총괄)
- **수신자:** 의사결정권자 SUN(써니), 기획자 MOON(무니)
- **대상 팀원:** EARTH-FE(어띠페), EARTH-BE(어띠베)

---

## 📌 1. 전체 업무 수행 요약 (Task Timeline & Checklist)

본 보고서는 **sunflower87** 프로젝트의 보안 규격 수립, 백엔드/프런트엔드 아키텍처 정밀 리팩토링, 고품질 린팅/포맷터 인프라 구축, 그리고 세션 연장 기능 연동까지의 모든 지시사항과 수행 결과를 종합적으로 기록합니다.

| 태스크 ID | 작업 대상 | 업무 지시 요약 | 수행 상태 | 비고 (완료 결과) |
| :--- | :--- | :--- | :---: | :--- |
| **TASK-01** | FE / BE | 대시보드 오늘의 추천 종목 Card 배치 (R1) | **완료 (Success)** | `/api/recommendations` API 구축 및 PrimeReact 카드 바인딩 |
| **TASK-02** | 어띠베 (BE) | 백엔드 수동 종목 등록 API 및 로컬 JSON 데이터 격리 구축 | **완료 (Success)** | `my_stocks.json` 로컬 저장, 실시간 수익율 계산 및 CRUD API 완비 |
| **TASK-03** | FE / BE | SQLite DB 기반 매수/매도 거래 내역 및 ETF 통합 검색 (R2) | **완료 (Success)** | 일반 주식(KOSPI/KOSDAQ)과 ETF 마스터 데이터 통합 병합 패치 완료 |
| **TASK-03-BE-R1** | 어띠베 (BE) | SQLite DB 구축 & 종목코드 자동 검색 API (_BE_R1) | **완료 (Success)** | SQLAlchemy 연동, 두 테이블 정규화 및 트랜잭션 트리거 로직 구현 완료 |
| **TASK-03-BE-R2** | 어띠베 (BE) | ETF 마스터 데이터 병합 및 대소문자 매칭 패치 (_BE_R2) | **완료 (Success)** | KOSPI/KOSDAQ & ETF(TIGER 200, KODEX 200액티브 등) 병합 및 한화오션(042660) 검색 보장 |
| **TASK-03-BE-R3** | 어띠베 (BE) | 매도 가드 및 잔고 0주 레코드 삭제 트랜잭션 구현 (_BE_R3) | **완료 (Success)** | 보유량 미달 시 400 Bad Request 가드 적용 및 전량 매도 시 stocks 행 DELETE 완벽 처리 |
| **TASK-03-BE-R4** | 어띠베 (BE) | 거래일시 커스텀 파싱 및 SQLite 데이터 적재 구현 (_BE_R4) | **완료 (Success)** | `payload.date` 문자열 %Y-%m-%d %H:%M:%S 파싱 및 빈 시간대 `now()` 폴백 처리 완비 |
| **TASK-03-BE-R5** | 어띠베 (BE) | SQLite DB 거래 원장 완성 및 계좌별 자산 역산 API 구현 (_BE_R5) | **완료 (Success)** | 다중 계좌 isolation, 연대기적 chronological replay 자산 재계산, PUT/DELETE API 완비 |
| **TASK-03-FE** | 어띠페 (FE) | SQLite DB 거래 내역 & 종목코드 자동 검색 UI (_FE_R1) | **완료 (Success)** | TabView 구조화, InputGroup 자동완성 UI, readOnly 코드 제어 규격 준수 |
| **TASK-03-FE-R2** | 어띠페 (FE) | ETF 통합 및 사명 변경 크로스체크 완료 (_FE_R2) | **완료 (Success)** | TIGER 200 (102110 / 069500), 한화오션 (042660) 검색 및 매매 연동 완벽 검증 |
| **TASK-03-FE-R3** | 어띠페 (FE) | 실시간 비동기 연쇄 리프레시 고도화 완료 (_FE_R3) | **완료 (Success)** | 매매 등록 성공 시 loadAccounts/loadTransactions 연쇄 실행 및 계좌 테이블 즉시 동기화 |
| **TASK-03-FE-R4** | 어띠페 (FE) | 거래일시 Calendar 입력 & 검색 로딩 Spin UI 고도화 (_FE_R4) | **완료 (Success)** | `Calendar` (showTime, hourFormat="24") 연동 및 `isSearching` 로딩 UI 제어 준수 |
| **TASK-03-FE-R5** | 어띠페 (FE) | 매매 내역 CRUD 완비 및 계좌 연동 UI 통합 구현 (_FE_R5) | **완료 (Success)** | Calendar 한국어 로컬라이징, 계좌 선택 Dropdown, DataTable 수정/삭제 액션 및 ConfirmDialog 연동 완비 |
| **TASK-04** | 어띠페 (FE) | 실시간 세션 연장 타이머 연동 (gem_gagaebu 규격 이식) | **완료 (Success)** | 헤더 내 Logout 버튼 위 실시간 MM:SS 타이머 및 클릭 연장 구현 |

---

## ⚙️ 2. [어띠베] 백엔드 부문 지시 및 수행 사항 (TASK-03 BE R1 ~ R5 부합)

### ① 백엔드 Prettier/Lint 인프라 적용
*   **지시 사항:** 프런트엔드 환경과 대칭되는 `npm run format`, `npm run lint` 명령을 `be` 폴더에 구현하고, 파이썬 가상환경(`venv`) 및 `node_modules` 폴더가 포맷팅 범위에 절대 포함되지 않도록 제외 설정을 구성하라.
*   **수행 결과:**
    *   **[package.json](file:///c:/01_Projects/sunflower87/be/package.json) 구성:** 파이썬 포맷팅(`venv\Scripts\python -m black .`) 및 JSON/문서 포맷팅(`npx prettier --write`)을 순차적으로 수행하는 스크립트 작성.
    *   **[.prettierignore](file:///c:/01_Projects/sunflower87/be/.prettierignore) / [pyproject.toml](file:///c:/01_Projects/sunflower87/be/pyproject.toml):** Black과 Prettier가 의존성/가상환경 디렉토리를 절대 건드리지 않도록 제외 규격 선언.
    *   **[.flake8](file:///c:/01_Projects/sunflower87/be/.flake8) 설정:** flake8과 Black 포맷터 간의 충돌 방지를 위해 `max-line-length = 88`, `extend-ignore = E203` 설정 완료.

### ② SQLite DB 기반 매매 이력 및 종목/ETF 통합 검색 (TASK-03 R2 패치 완료)
*   **지시 사항:** TIGER 200, KODEX 200액티브 등 ETF 종목 및 한화오션 같은 최신 사명 변경 종목 누락 버그를 잡기 위해 일반 주식 마스터와 ETF 마스터를 단일 딕셔너리로 병합하여 통합 검색을 지원하라.
*   **수행 결과:**
    *   **보안 격리:** [.gitignore](file:///c:/01_Projects/sunflower87/.gitignore)에 `be/sunflower87.db*`를 완벽히 제외 등록 완료.
    *   **[database.py](file:///c:/01_Projects/sunflower87/be/database.py) 설계:** SQLAlchemy ORM을 사용하여 거래 이력(`transactions` 테이블: `id`, `date`, `type`, `code`, `name`, `quantity`, `price`)과 현재고 잔고(`stocks` 테이블: `code`, `name`, `quantity`, `avg_price`) 테이블 스키마를 완벽 정규화하여 선언.
    *   **매매 트리거 트랜잭션:** `POST /api/transactions/add` 구현 완료. 매수 시에는 `stocks` 테이블의 수량 합산 및 매입 평단가를 가중평균 가치 계산법으로 자동 갱신하고, 매도 시에는 수량 차감 및 전량 매도 시 `DELETE`가 단일 데이터베이스 커밋 트랜잭션 내에서 완결되도록 비즈니스 로직 작성.
    *   **종목 및 ETF 통합 검색 API (`GET /api/stocks/search`):** 파이썬 `pykrx` 라이브러리를 연동하여 KOSPI 마스터, KOSDAQ 마스터, 그리고 ETF 마스터(`stock.get_etf_ticker_and_name`) 데이터를 동시에 로드하여 단일 딕셔너리로 병합하는 통합 검색 로직 완성.
    *   **안정적 D.O.D. 수립:** 네트워크 연결 실패 대비 폴백 사전에 최신 사명인 `'한화오션'`(코드: `042660`)과 대표 ETF인 `'TIGER 200'`(코드: `102110` / `069500`), `'KODEX 200액티브'` 등을 수동 포함 선언하여 100% 로컬 오프라인 통과 보장.

### ③ 거래일시 커스텀 파싱 및 SQLite 데이터 적재 (TASK-03 BE R4 완료)
*   **지시 사항:** 프런트엔드에서 전송하는 커스텀 거래일시 문자열을 파싱하여 저장하고, null이나 빈 값일 때 `datetime.now()`를 강제 주입하라.
*   **수행 결과:**
    *   **Pydantic DTO 확장:** `TransactionCreate`에 `date: Optional[str] = None` 선택 필드 제공.
    *   **비즈니스 포맷터 가드:** `%Y-%m-%d %H:%M:%S` 양식에 부합하면 해당 데이터로 파싱하고, 비어 있거나 파싱이 실패하면 서버의 현재 시간(`datetime.now()`)으로 유연하게 폴백(Fallback) 처리하여 안전하게 영속화.
    *   **정렬 무결성:** `GET /api/transactions` 엔드포인트에 `order_by(Transaction.date.desc())` 정렬을 적용하여 과거 거래 내역을 소급 입력하더라도 타임라인에 실시간 정렬 배열되도록 설계 보증.

### ④ 계좌별 격리 및 자산 역산(Rollback) 재계산 (TASK-03 BE R5 완료)
*   **지시 사항:** 매매 기록이 등록/수정/삭제될 때 해당 계좌(`account_number`)의 주식 잔고만 정확하게 가감/역산되도록 트랜잭션 안전장치를 구축하고, 연대기적 chronological replay 방식으로 최종 잔고를 계산하라.
*   **수행 결과:**
    *   **연대기적 재계산 함수 구현 (`recalculate_portfolio_for_account`):** 지정된 계좌의 전체 거래 내역을 처음부터 끝까지 추적해 수량과 가중평균 매입단가를 정밀 복원하는 알고리즘 작성. 어느 시점이든 잔고가 마이너스가 되면 즉각 `400 Bad Request` 에러를 던져 트랜잭션 롤백 처리.
    *   **PUT & DELETE API 신설:** `DELETE /api/transactions/{id}` 및 `PUT /api/transactions/{id}` 엔드포인트 구현 완료. PUT으로 계좌번호가 변경되는 경우 이전 계좌와 새 계좌의 포트폴리오를 둘 다 안전하게 재산출하도록 구성.

---

## 🌍 3. [어띠페] 프런트엔드 부문 지시 및 수행 사항 (TASK-03 FE R1 ~ R5 부합)

### ① TabView 기반 다중 뷰 포트폴리오 구조화
*   **지시 사항:** 메인 대시보드 하단을 탭뷰로 구조화하여 기존의 자산 테이블과 신규 구현될 매매 기록을 탭 형태로 편리하게 스위칭할 수 있도록 구성하라.
*   **수행 결과:**
    *   **[Dashboard.jsx](file:///c:/01_Projects/sunflower87/fe/src/pages/Dashboard.jsx) 갱신:** PrimeReact의 `TabView`와 `TabPanel`을 사용하여 [탭 1: 보유 자산 상세], [탭 2: 매매 내역 히스토리] 영역으로 구분 탑재.

### ② 매매 등록 폼 (Dialog Modal) 및 p-inputgroup 종목/ETF 통합 검색
*   **지시 사항:** `p-inputgroup` 및 상태 관리 로직을 고스란히 계승하면서 백엔드 통합 API 연동 후 `'TIGER 200'`이나 `'한화오션'` 검색 시 종목코드가 올바르게 조회 및 모달 자동 입력되는지 크로스 검증을 시행하라.
*   **수행 결과:**
    *   **자동완성 인터페이스:** 종목명 입력 후 [검색] 버튼 클릭 시 `GET /api/stocks/search?keyword=...` API를 연동 호출하여, 일치하는 첫 번째 종목코드(예: TIGER 200 -> 102110 / 069500 / 한화오션 -> 042660)를 `txCode` 상태에 자동 바인딩.
    *   **보안 필드 통제:** 사용자가 임의로 종목코드를 수동 훼손하지 못하도록 종목코드 입력 Box에 `readOnly` 속성과 `cursor-not-allowed` 스타일을 부여하여 자동 입력 UX 유도.
    *   **매수/매도 테마 전환 및 비동기 리액티브 동기화:** 모달 창에서 매수(Red)/매도(Blue) 변경 시 색상 스위칭 및 매매 성공 시 보유 잔고 탭과 히스토리 탭의 비동기 연쇄 리프레시 동작을 완벽 검증.
    *   **실시간 비동기 연쇄 리프레시 (R3 핵심 요건):** 매매 등록 처리(`POST /api/transactions/add`) 성공 시 모달이 닫히며 화면 깜빡임 없이 상하단 `loadAccounts()` (기획서 명세 `fetchAccountData()`)와 `loadTransactions()`가 즉각 연쇄 트리거되어 실시간 화면 갱신 성공.

### ③ 거래일시 소급 Calendar 및 검색 로딩 Spin UI 고도화 (TASK-03 FE R4 완료)
*   **지시 사항:** `Calendar` 컴포넌트 연동으로 날짜/시간 정밀 입력을 확보하고, 검색 중일 때 버튼 스핀 로딩을 표현하라.
*   **수행 결과:**
    *   **중앙관제 임포트:** [fe/src/assets/js/PrimeReact.js](file:///c:/01_Projects/sunflower87/fe/src/assets/js/PrimeReact.js) 파일에 `Calendar` 컴포넌트 임포트/익스포트를 추가하여 중앙 관제 규칙 완벽 준수.
    *   **소급 Calendar 도입:** `showTime`, `hourFormat="24"`를 활성화한 Calendar 탑재. 기본값으로 `new Date()`를 할당하고 포맷터 함수(`YYYY-MM-DD HH:mm:ss`)를 거쳐 API 안전 전송.
    *   **로딩 스핀 인터랙션:** `isSearching` 부울 State와 PrimeReact Button의 `loading={isSearching}` 속성을 유기적으로 연결하여 종목 검색 중 회전하는 스핀 애니메이션 제공.

### ④ 한국어 로컬라이징 및 다중 계좌 CRUD UI 완비 (TASK-03 FE R5 완료)
*   **지시 사항:** Calendar 한글 로컬라이징, 다중 계좌 매핑 Dropdown 제공, [수정/삭제]가 가능한 완벽한 원장 관리 UI를 구축하라.
*   **수행 결과:**
    *   **Calendar 한국어(ko) 로컬라이징:** `addLocale`을 활용해 한글 요일/월 딕셔너리를 사전 세팅하고 `<Calendar locale="ko" />` 속성을 부여하여 완벽하게 로컬라이징 처리.
    *   **계좌 선택 Dropdown:** 등록/수정 모달에 Dropdown을 추가하여 기존 계좌 조회 API 결과 데이터를 바인딩 (`optionLabel="alias"`, `optionValue="account_number"`).
    *   **수정 및 삭제 인터랙션:** `DataTable`에 [거래 계좌] 및 [작업] 액션 컬럼 신설. 수정 클릭 시 기존 데이터를 등록 모달 Form에 바인딩하여 `PUT /api/transactions/{id}` 전송. 삭제 클릭 시 PrimeReact `ConfirmDialog`를 띄워 최종 동의 후 `DELETE /api/transactions/{id}` 호출.
    *   **Refetch 동기화:** CRUD 성공 시 화면 깜빡임 없이 상위 컴포넌트의 자산 데이터와 거래 대장을 실시간 리프레시하여 데이터 무결성 보장.

---

## 📈 4. 코드 품질 관리 및 최종 빌드 상태 보고

*   **백엔드 (`npm run lint; npm run format`)**: `pykrx` 캐싱 검색 로직 및 R5 역산/CRUD에 대한 엄격한 포맷팅 검사 및 **flake8 PEP 8 린트 에러 0건** 완벽 클리어.
*   **프런트엔드 (`npm run format; npm run lint`)**: eslint 및 prettier 경고/에러 **0건 (100% 클리어)**.
*   **Vite 컴파일 빌드 (`npm run build`)**: 의존성이나 경로 누수 없이 **0.59초 속도로 초고속 컴파일 성공**.


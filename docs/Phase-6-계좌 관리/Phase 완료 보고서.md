# Phase 6: 계좌 관리 기능 완료 보고서

## 1. 개요
* **기획 목적**: 사용자가 자신의 계좌를 등록, 조회, 수정, 삭제할 수 있는 '계좌 관리 기능'을 제공하여 전체 자산 및 일일 잔고 동기화의 기반 데이터를 마련하기 위함입니다.
* **주요 작업 내용**: 계좌 관리 CRUD(Create, Read, Update, Delete) 백엔드 로직 및 프론트엔드 UI 화면 구현, 소프트 삭제(Soft Delete) 적용.

## 2. 최종 산출물 및 변경 사항 요약

### 2.1 Database (DB 파트)
* 기존 `account` 테이블 스키마를 100% 수용하여 활용
* 무결성 유지를 위해 물리적 삭제 대신 `dt_deleted` 컬럼에 타임스탬프를 기록하는 **소프트 삭제(Soft Delete)** 방식을 완벽하게 적용 

### 2.2 Backend (BE 파트)
* **계좌 관리 API 엔드포인트 구현 완료** (`be/routers/account.py`)
  * `GET /api/accounts/`: 계좌 목록 조회 (`include_deleted` 옵션을 통한 활성/비활성 데이터 분리 지원)
  * `POST /api/accounts/`: 계좌 신규 등록 (계좌코드 중복 방지 및 예외 처리 로직 포함)
  * `PUT /api/accounts/{acc_cd}`: 계좌 정보(계좌명, 금융사명, 정렬 순서 등) 수정 
  * `DELETE /api/accounts/{acc_cd}`: 계좌 삭제 시 DB의 `dt_deleted` 값을 통한 소프트 삭제 처리
* API 입출력 검증을 위한 **Pydantic Schema 업데이트** (`be/schemas.py`)
* `be/main.py`에 account router 추가 연동 완료

### 2.3 Frontend (FE 파트)
* **API 호출 통신 연동 완료** (`fe/src/api/accountApi.ts`)
* **계좌 관리 신규 UI 컴포넌트 개발 및 라우팅 완료**
  * `fe/src/pages/AccountList.tsx`: 메인 계좌 목록 페이지 (라우팅: `/account`)
  * `fe/src/components/AccountList/AccountListCmpt.tsx`: PrimeReact의 `DataTable`을 활용한 목록 표출 및 "삭제 계좌 포함" 체크박스 필터 구현
  * `fe/src/components/AccountList/AccountDialog.tsx`: 계좌 등록 및 수정을 위한 인라인 폼 모달(Dialog) 구현
* **UI/UX 개선 및 예외처리 방어 로직 반영**
  * 기존 '주식 매매 내역' 및 '입출금 내역' 화면과 완벽히 동일한 통일성 있는 레이아웃 
  * PrimeReact의 `confirmDialog` 및 `showNotice`를 활용하여 작업(삭제/저장) 전 사용자 재확인 과정 및 결과 피드백 토스트 알림 적용
* 좌측 네비게이션 메뉴(`fe/src/data/SidebarData.ts`)에 **'계좌 관리' 메뉴 등록 완료** 및 App 라우팅 적용 완료

## 3. 향후 방향
* Phase 6에서 기획한 개발 요구사항은 소스코드에 100% 반영되었습니다.
* 미리 작성해 둔 QA 시나리오(TC-01 ~ TC-06)를 토대로 FE/BE 연동을 최종 점검하시면 됩니다.
* 향후 Phase에서 '계좌별 일일 잔고 정산' 스케줄러 기능과 본 데이터를 연동할 때 안정성을 지속 모니터링할 예정입니다.

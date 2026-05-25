# 🌻 sunflower87 리팩토링 기획 대화록 (tasks-3)

본 문서는 **sunflower87** 프로젝트의 아키텍처 개편 및 프리미엄 대시보드 리팩토링을 위해 진행된 고가치 기획 대화(**Conversation ID: c37dfe14-cc5e-4d87-953c-45710d57529f**)의 종합 요약 및 핵심 의결 사항 아카이브입니다.

---

## 📅 대화 정보
*   **대화 제목 (Title)**: `tasks-3`
*   **프로젝트 경로**: `C:\01_projects\sunflower87`
*   **연동 대화 ID**: `c37dfe14-cc5e-4d87-953c-45710d57529f`
*   **최종 동기화 일시**: 2026-05-24

---

## 💡 핵심 요구사항 및 리팩토링 의결 사안

### 1. 백엔드 폴더 구조 개편 및 파일 단수화 (`be/git` 디렉토리 신설)
*   **파일명 단수화 규칙**: 모든 파이썬 파일명과 DB 테이블명은 파이썬 표준 관례에 따라 **단수형**으로 명명 통일합니다. (예: `account.py`, `transaction.py`, `portfolio.py` 등)
*   **태스크 및 형상관리 도메인 격리**: 
    - `/be/routers/tasks.py`를 **`be/git/git_task.py`**로 이름 변경하고,
    - `/be/git_service.py`를 **`be/git/git_service.py`**로 이동하여,
    - 이들을 기획 태스크 및 Git 형상관리를 전문으로 하는 **`/be/git`** 전용 디렉토리 하위에 격리 통합합니다.

### 2. 1분 주기 실시간 주가 연쇄 동기화 아키텍처 (`Trigger-and-Refetch Pattern`)
*   **한계점 극복**: 백엔드에서 실시간 주가를 1분마다 리프레시하더라도 프론트엔드가 리로드되지 않으면 화면에 즉시 보이지 않는 문제를 해결하기 위해 **연쇄 리밸리데이션(Trigger-and-Refetch)** 패턴을 도입합니다.
*   **상호작용 시퀀스**:
    ```
    [Front-end React Dashboard]
          │
          │ 1) 1분 주기 setInterval 타이머 동작
          ▼
    [POST /api/stocks/refresh-prices] (BE 트리거)
          │
          │ 2) pykrx 연계 주가 수집 및 DB/Cache 갱신
          ▼
    [Response: {"status": "success", "updated": [...]}] (BE 성공 응답)
          │
          │ 3) 리스폰스 수신 즉시 무비동기 연쇄 리플로우
          ▼
    [GET /api/accounts] (계좌/자산 정보 Refetch)
          │
          │ 4) 최신 평가 손익 및 자산 데이터 수신
          ▼
    [React State Revalidation] ➔ 새로고침 없이 화면 실시간 동적 렌더링
    ```
*   **기대 효과**: 새로고침 없이 대시보드상의 주가 배지, 평가손익률 배지, 통합 총자산 금액 등이 1분마다 자동으로 살아 움직이듯 무진동 갱신 렌더링됩니다.

### 3. 데이터베이스 제3정규화(3NF) 및 8개 테이블 대칭형 RESTful CRUD API
*   **3정규화(3NF) 준수**: `transaction`, `stock` 테이블에 중복 저장되던 한글 종목명(`stock_name`) 컬럼을 영구 제거하고, 종목 마스터 테이블인 **`stock_cache`**만을 SSM(Single Source of Truth)으로 삼아 동적 JOIN을 수행합니다.
*   **1:1 완전 대칭형 CRUD**: 단순 조회를 넘어 시스템의 투명한 관리와 디버깅 무결성을 위해 데이터베이스 내 모든 8개 자원에 대해 완벽한 RESTful CUD API를 제공합니다.
    1.  `account` [계좌 마스터]
    2.  `transaction` [주식 매매 내역]
    3.  `transaction_cash` [현금 입출금/이자/배당 원장]
    4.  `account_daily_balance` [일자별 잔고 스냅샷]
    5.  `stock` [보유 자산 실시간 잔고]
    6.  `stock_cache` [종목 검색 마스터 딕셔너리]
    7.  `stock_ohlcv_cache` [주가 시고저종 캐시]
    8.  `recommendation` [AI 추천 및 투자자 피드백]

### 4. 시계열 회계 무결성 가드 (`Chronological Self-Healing`)
*   **자가 치유 엔진**: 과거 날짜의 자산 변동(매매 거래 또는 현금 원장 추가/수정/삭제)이 일어날 시 발생할 장부 왜곡을 방기하기 위해, 해당 계좌의 과거 기존 시계열 스냅샷 전체를 완전히 Purge하고 연대기순으로 자동 재산출하여 재생성(Purge & Rebuild)하는 트리거를 구축합니다.
*   **설정 모달 내 정산 단추 이식**: 계좌 설정 다이얼로그(`SettingsDialog.jsx`) 내 각 계좌 카드 오른쪽에 FontAwesome 새로고침 단추(`fas fa-sync-alt`)와 함께 **"잔고 재정산"** 버튼을 탑재하여 언제든 수동 자가치유 기동을 보장합니다.

### 5. 엔터프라이즈급 프리미엄 UI/UX 및 ApexCharts 바인딩
*   **드래그 앤 드롭 카드 셔플 (`SortableJS`)**: 대시보드의 주요 패널 카드들을 타이틀 바(`.card-title`)를 드래그 핸들로 하여 브라우저 상에서 자유롭게 셔플하며, 정렬 배치를 `localStorage`에 보관하여 유지합니다. (우측 상단 전체화면 Maximize/Minimize 버튼 완비)
*   **계좌별 수익 아코디언**: PrimeReact `Accordion`을 사용하여 탭 헤더 상에 계좌명과 더불어 계좌별 '총수익', '오늘수익', '예수금' 핵심 지표를 동적으로 병렬 출력합니다.
*   **3대 독립 카드 격리 분리**: `StockDetail.jsx` 내 기존 TabView를 폐기하고, (1)보유 자산 카드, (2)주식 매매 내역 카드, (3)계좌 입출금 내역 카드(`transaction_cash`)를 각각 독립적인 프리미엄 카드로 완전히 단독 분리 배치합니다.
*   **160일 페치 & 80일 뷰포트 드래그 페닝**: 주가 OHLCV 로드 시 단 한 번의 통신으로 160거래일 주가를 pre-fetch한 뒤 화면의 초기 뷰포트는 최근 80거래일로 강제 제한하여 렌더링하고, 사용자가 마우스 드래그로 Panning할 때 메모리에 적재된 과거 주가가 끊김 없이 자연스럽게 노출되도록 설계합니다.

---

## 🛠️ 향후 구현 시나리오 (실행 승인 대기 단계)
본 tasks-3 대화록의 기획 명세에 기반하여 DB 마이그레이션 모듈 및 백엔드 라우터, React/TypeScript 프론트엔드의 최종 구현 및 패키지 설치 작업이 기동을 위한 최종 **'승인'** 또는 **'실행해'**의 지시를 기다리는 상태입니다.

# 🎨 프론트엔드 개발자 전용 개발 계획서 (Frontend Developer Plan)

본 계획서는 **sunflower87** 프로젝트 리팩토링 중 TypeScript 타입 안전성 확보, 공통 동적 상수 연동, API 통신 모듈 업데이트, 160일 페치 및 80일 뷰포트 강제 ApexCharts 렌더링, 설정(Settings) 화면 및 호출 연동, 그리고 프리미엄 대시보드 룩앤필(Look & Feel)을 구현하는 프론트엔드 개발자 전용 명세서입니다.

---

## 1. 프론트엔드 프로젝트 스캐폴딩 및 핵심 스택

본 프로젝트의 프론트엔드(`fe`) 환경은 밑바닥부터 새로 구축하는 대신, 당사가 기획한 핵심 기술 스택과 완벽하게 일치하는 사전 제작 템플릿인 **`gem_dashboard` 샘플 소스를 베이스 보일러플레이트(Base Boilerplate)로 채택**하여 Direct Injection 방식으로 이식합니다.

### 🚀 `gem_dashboard` 직접 이식 (Direct Injection) 전략
*   **방식**: `C:\01_Projects\gem_dashboard`의 원본 소스 전체(`package.json`, `src` 등)를 `sunflower87/fe/` 디렉토리 최상단(Root)에 통째로 복사하여 프로젝트 뼈대로 사용합니다.
*   **이점**: Vite + React 기반의 필수 설정과 초기 레이아웃(Sidebar, Header, Layout)이 완성되어 있으므로, 셋업 시간을 극적으로 단축하고 비즈니스 로직 구현에 즉각 집중할 수 있습니다.
*   **버전 관리**: 이식 직후 형상 관리(Git)를 통해 원본 상태를 보존하며, 이후 본 계획서의 명세에 맞추어 점진적으로 컴포넌트와 페이지를 깎아나가는(Refactoring) 방식으로 개발합니다.

### 📦 핵심 기술 스택 명세 (`gem_dashboard` 내장 기준)
| 분류 | 기술 / 패키지 명칭 | 용도 및 적용 범위 |
| :--- | :--- | :--- |
| **코어 & 빌드** | **React 19, Vite 8** | 초고속 HMR 지원 선언적 UI 프레임워크 및 빌드 툴 |
| **타입 시스템** | **TypeScript** | API 스키마 타입 안정성 강제 및 빌드 타임 컴파일 검증 |
| **UI 프레임워크**| **PrimeReact, PrimeFlex** | 엔터프라이즈급 UI 컴포넌트 및 유틸리티 레이아웃 배치 |
| **스타일링** | **SCSS (Sass)** | 고성능 CSS 확장 및 변수 제어 |
| **데이터 시각화**| **ApexCharts** | 주가 OHLCV 콤보 차트 및 자산 잔고 추이 렌더링 |
| **벡터 아이콘** | **FontAwesome Free** | 사이드바 메뉴, 계좌 입출금 상태 등 전역 아이콘 수록 |
| **드래그앤드롭** | **SortableJS** | 대시보드 카드 순서 및 계좌 정렬 연동 |

---

## 2. 프리미엄 메인 대시보드 (Dashboard) 룩앤필 구현 계획

메인 대시보드 화면(`Dashboard.jsx`)은 미려하고 세련된 시각적 레이아웃과 고도로 동적인 인터랙션 카드를 통해 프리미엄 모니터링 환경을 제공합니다. (Mockup 이미지(dashboard.png) 레이아웃 100% 반영)

```
┌────────────────────────────────────────────────────────────────────────┐
│  [홈]   [ Dashboard ] Campaign Insights                                  │
│ ┌──┐ ┌────────────────────────────────────────────────────────────────┐ │
│ │  │ │ [투자수익-금일]  [투자수익-금월]  [투자수익-금년]  [통합 총자산]   │ │
│ ├──┤ ├────────────────────────────────────────────────────────────────┤ │
│ │  │ │ ┌───────────────────────────────────┐ ┌──────────────────────┐ │ │
│ │  │ │ │ ≡ 계좌별 수익 현황 (Main Card)      │ │ ≡ 차트 분석 (Sub)    │ │ │
│ │  │ │ │ ┌───────────────────────────────┐ │ │  [Candlestick/Line]  │ │ │
│ │  │ │ │ │ Accordion Tab (계좌별)         │ │ │                      │ │ │
│ │  │ │ │ └───────────────────────────────┘ │ │                      │ │ │
│ │  │ │ └───────────────────────────────────┘ └──────────────────────┘ │ │
│ │  │ │ ┌───────────────────────────────────┐ ┌──────────────────────┐ │ │
│ │  │ │ │ ≡ 최근 주식 매매 내역 (Footer 1)   │ │ ≡ AI 추천 (Footer 2) │ │ │
│ │  │ │ └───────────────────────────────────┘ └──────────────────────┘ │ │
│ └──┘ └────────────────────────────────────────────────────────────────┘ │
└────────────────────────────────────────────────────────────────────────┘
```

### 1) 상단 KPI 블럭 구성 (4개 블럭)
대시보드 헤더 직하단에 카드로 구성된 4가지 핵심 재무 지표를 일렬로 배치합니다.
*   **투자수익-금일**: 오늘 하루 동안 발생한 평가 손익 및 실현 손익 합산액 (FontAwesome 화살표 아이콘 및 컬러링 연동).
*   **투자수익-금월**: 이번 달 누적 투자 손익 금액.
*   **투자수익-금년**: 올해 누적 투자 손익 금액.
*   **통합 총자산**: 보유 계좌의 전체 예수금과 주식 평가 가치를 합산한 실시간 자산 총액.

### 2) 드래그 앤 드롭 카드 배치 (`sortablejs` 적용)
KPI 블럭 하단의 메인/서브/푸터 카드들은 모듈화되어 정렬 상태가 유지됩니다.
*   **드래그 핸들 바인딩**: 각 카드의 **타이틀 바(`card-title`)를 드래그 핸들(Drag Handle)**로 사용해 마우스 클릭 드래그로 손쉽게 위치를 바꿀 수 있습니다.
*   **화면 최대화 (Maximize)**: 모든 카드의 우측 상단 구석에 화면 최대화 토글 아이콘(FontAwesome `fas fa-expand` / `fas fa-compress`)을 제공하여 원클릭으로 꽉 찬 모니터 레이아웃 뷰를 제공합니다.

### 3) 메인 카드: 계좌별 수익 현황
대시보드 좌측 메인을 지키는 중심 카드 컴포넌트입니다.
*   **컨텐츠 레이아웃**: PrimeReact **`Accordion`** 컴포넌트를 이식합니다.
*   **계좌별 탭 분리**: 등록된 계좌마다 물리적인 `AccordionTab`을 자동 매핑합니다.
*   **헤더 요약 표시**: AccordionTab의 Header 타이틀 영역에 단순히 계좌명만 표시하는 것이 아니라, 해당 계좌의 **'총수익'**, **'오늘수익'**, **'예수금'** 핵심 요약 정보를 미려한 폰트와 크기로 정렬 노출합니다.
*   **보유 자산 Datatable**: AccordionTab 내부에는 해당 계좌 소속의 **"보유 자산"** Datatable이 배치됩니다.
*   **필터링 체크박스**: Datatable 바로 위 왼쪽 상단 끝에 **"보유수 0주 포함" 체크박스**를 배치하여, 매도 후 잔고가 0주가 된 기록도 체크 여부에 따라 토글 표시할 수 있는 필터 핸들러를 구현합니다.

### 4) 서브 카드: 차트/시계열 분석
대시보드 우측 서브 영역에 배치되며 선택된 주체에 따라 반응형 차트를 렌더링합니다.
*   **종목 선택 시 (Combo Chart 구현)**: 해당 종목의 과거 OHLCV 데이터 수집 규격을 기반으로 상단에는 **캔들 차트 (Candlestick Chart)**, 하단에는 **거래량 바 차트 (Bar Chart)**가 결합된 단일 콤보 차트(Single Combo Chart)를 렌더링합니다.
    *   **다중 Y축 (Dual Y-axis) 겹침 렌더링**: X축(시간)은 완벽히 공유하되 Y축은 분리합니다. 미려한 룩앤필을 위해 거래량(Bar)의 Y축 최대값(max)을 실제 최대 거래량의 약 3~4배로 넉넉히 설정합니다.
    *   이를 통해 거래량 바가 전체 차트 높이의 하단 25~30% 영역까지만 그려지도록 제한하여, 주가 캔들(상단 70~75%)과 시각적 간섭 없이 부드럽게 오버랩(겹침)되는 최신 핀테크 앱 스타일의 레이아웃을 구현합니다.
*   **계좌 선택 시**: 해당 계좌의 날짜별 자산 잔고 추이 및 수익률 역사를 선형/면적형 차트(**Line/Area Chart**)로 부드러운 애니메이션과 함께 드로잉합니다.

### 5) 푸터 카드 (2개 카드로 단일화 구성)
메인카드, 서브카드 하단에는 3개가 아닌 **2개의 카드**를 나란히 배치하여 화면 균형을 유지합니다.
*   **푸터 카드 (1): 최근 주식 매매 내역**: 
    *   사용자의 전체 주식 거래 대장 중 **최근 3건**의 매매 이력만 간략하게 요약 리스팅합니다.
    *   카드 타이틀 오른쪽의 크게보기 버튼 왼쪽에 미니멀한 **"더보기" (Show More)** 링크 아이콘 버튼을 장착합니다. 클릭 시 전체 거래 대장 페이지인 **"주식 매매 내역"** 화면으로 네비게이션됩니다.
*   **푸터 카드 (2): AI 추천**:
    *   포트폴리오 AI 추천 목록을 리스팅하고, 투자자의 의견 평점 피드백(`investor_score`, 0~5점)을 제출하는 폼을 연동합니다. 0점 선택 시 반려(반투명 블러 혹은 애니메이션 슬라이드 아웃) 처리를 집행합니다.

### 6) 프리미엄 Sidebar 메뉴 구성 (FontAwesome 아이콘 바인딩)
좌측 고정 네비게이션 사이드바는 FontAwesome Free 웹 아이콘을 활용하여 고급스러운 아이콘 메뉴 세트를 노출합니다.
1.  **`홈`** (`Home`): 대시보드 메인 화면 이동 (아이콘: `fas fa-chart-line` / `fas fa-home`)
2.  **`보유 자산 상세`** (`Holdings Detail`): 전체 소유 주식 상세 현황 테이블 이동 (아이콘: `fas fa-briefcase`)
3.  **`주식 매매 내역`** (`Stock Transaction`): 기존 매매 내역 히스토리 (아이콘: `fas fa-exchange-alt`)
4.  **`계좌 입출금 내역`** (`Cash Transaction`) **[NEW]**: 신설된 `transaction_cash` 테이블 데이터 렌더링용 전용 내역 페이지 이동 (아이콘: `fas fa-wallet`)
5.  **`설정`** (`Settings`): 계좌 추가, 수정, 삭제 및 순서 정렬 전용 팝업/화면 이동 (아이콘: `fas fa-cog`)

---

## 3. 설정 (Settings) 화면 및 Account CRUD 구현 계획

사용자가 계좌 관리 및 표시 순서를 드래그하여 제어할 수 있는 계좌 환경을 완벽 구현합니다.
*   **설정 팝업 다이얼로그 (Settings Component)**:
    *   **계좌 목록 정렬**: 계좌 리스트를 노출하며, 좌측 드래그 핸들을 사용하여 카드를 드래그 앤 드롭 정렬할 수 있는 `SortableJS`를 적용합니다. 드롭 즉시 백엔드의 정렬 인덱스(`acc_order`) 업데이트 API를 호출하여 데이터 정합성을 영구 동기화합니다.
    *   **계좌 추가**: 증권사명, 계좌 번호 코드, 계좌 명칭, 최초 투자 원금(`initial_cash`)을 기입하는 PrimeReact 검증 폼을 탑재합니다.
    *   **계좌 수정**: 인라인 입력 수정을 제공하여 명칭 및 투자 원금 변동을 통제합니다.
    *   **계좌 삭제**: 경고 컨펌 모달을 출력한 뒤 확인 시 소프트 딜리트(`dt_deleted` 세팅) API를 호출해 연대기에서 데이터를 지우지 않고 잔고 정산에서만 격리합니다.

---

## 4. 보유 자산 상세 및 거래 내역 카드 분리 설계

주식 상세 모니터링 페이지 및 자산 관리 뷰에서 기존의 탭 레이아웃을 폐기하고, 시각적 주목도와 독립성이 보장되는 **개별 카드 단위 레이아웃**으로 전면 해체 및 분리 구현합니다.

*   **보유 자산 카드 (Card 1)**:
    *   기존 "보유 자산 상세" 탭을 완전히 격리하여 독립된 아름다운 카드로 단독 렌더링합니다.
    *   보유량, 평균단가, 현재가, 평가 손익률이 수치별 컬러 그라데이션 배지와 함께 테이블화됩니다.
*   **주식 매매 내역 카드 (Card 2)**:
    *   기존 "매매 내역 히스토리" 명칭을 **`주식 매매 내역`**으로 명확하게 갱신하고 독립 카드로 분리합니다.
    *   주식 매수/매도 이력만을 집중 필터링하여 일시 역순으로 출력합니다.
*   **계좌 입출금 내역 카드 (Card 3) [NEW]**:
    *   신설된 `transaction_cash` 테이블에 저장된 입금, 출금, 이자, 배당, 수수료 등의 현금 이동 로그만을 전용으로 필터링하여 일지 형태로 노출하는 신규 독립 카드 컴포넌트입니다.
    *   유형별 FontAwesome Free 아이콘 매핑 배지를 이식합니다.

---

## 5. 타입 안전성 (TypeScript) 도입 및 상수/API 모듈 동기화

### 📐 [tsconfig.json](file:///C:/01_projects/sunflower87/fe/tsconfig.json) 신설
```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["DOM", "DOM.Iterable", "ES2020"],
    "module": "ESNext",
    "skipLibCheck": true,

    /* Bundler mode */
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",

    /* Linting */
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true
  },
  "include": ["src"]
}
```

#### [MODIFY] [Dashboard.jsx](file:///C:/01_projects/sunflower87/fe/src/pages/Dashboard.jsx) *(TypeScript 파일 Dashboard.tsx로 리팩토링 전환)*
- **🚨 1분 단위 실시간 연쇄 업데이트 엔진 (Trigger-and-Refetch)**:
  - 사용자가 로그인 상태일 때, 1분(`60,000ms`) 간격으로 백그라운드 타이머(`setInterval`)를 가동합니다.
  - 타이머가 작동할 때마다 백엔드의 현재가 수집 API(`POST /api/stocks/refresh-prices`)를 백그라운드 호출(Trigger)합니다.
  - 이 API 호출이 성공적으로 응답을 받으면, 프론트엔드는 즉시 계좌 및 포트폴리오 데이터를 조회하는 `GET /api/accounts` API를 리스폰스 즉시 연쇄 호출(Refetch)하여 React 상태를 재평가(Revalidation)합니다.
  - 이를 통해 새로고침 없이 대시보드의 주가, 평가 손익률, 통합 총자산이 1분마다 실시간으로 살아 숨 쉬듯 화면에 갱신 렌더링되는 프리미엄 UX를 제공합니다.
- **상단 4대 KPI 블럭 렌더링**: 투자수익-금일, 투자수익-금월, 투자수익-금년, 통합 총자산을 상단에 일렬 노출하며, 전일 대비 상승/하락에 따라 FontAwesome 화살표 아이콘과 색상 스타일링을 결합합니다.

### 📐 [api.ts](file:///C:/01_projects/sunflower87/fe/src/types/api.ts) 신설
```typescript
export interface Account {
  acc_cd: string;
  acc_nm: string;
  acc_company_nm: string;
  acc_order: number;
  cash_balance: number;
  initial_cash: number;
  dt_created: string;
  dt_deleted: string | null;
}

export interface Transaction {
  id: number;
  acc_cd: string;
  dt_trade: string;
  trade_type: "BUY" | "SELL";
  stock_code: string;
  stock_name?: string; // 3NF JOIN 동적 결합
  quantity: number;
  price: number;
  tax_fee: number;
  dt_deleted: string | null;
}

export interface TransactionCash {
  id: number;
  acc_cd: string;
  dt_cash: string;
  cash_type: "DEPOSIT" | "WITHDRAW" | "INTEREST" | "DIVIDEND" | "FEE";
  amount: number;
  description: string | null;
  dt_deleted: string | null;
}

export interface Stock {
  stock_code: string;
  acc_cd: string;
  stock_name?: string; // 3NF JOIN 동적 결합
  quantity: number;
  avg_price: number; // INTEGER 정수
  current_price: number;
  purchase_amount: number; // INTEGER 정수
}

export interface StockOhlcv {
  stock_code: string;
  trade_date: string;
  open_price: number;
  high_price: number;
  low_price: number;
  close_price: number;
  volume: number;
  trading_value: number;
  fluctuation_rate: number;
}

export interface Recommendation {
  stock_code: string;
  stock_name?: string; // 3NF JOIN 동적 결합
  tag: string;
  reason: string;
  score: number;
  dt_recommended: string;
  dt_deleted: string | null;
  investor_score: number | null;
}

export interface ApiResponse<T> {
  status: "success" | "error";
  message?: string;
  data?: T;
  results?: T;
}
```
*   **API 연동부 (`fe/src/api/index.js`) 개편**:
    *   백엔드의 명칭 변경에 매치되도록 REST URL 경로를 `/api/transactions_cash` 등으로 복수형 갱신 완료합니다.
    *   API 페이로드 요청 생성 시 `dt_trade`/`trade_type`/`dt_cash`/`cash_type` 규격을 준수하도록 전면 개정합니다.

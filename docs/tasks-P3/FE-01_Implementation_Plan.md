# [FE-01] 프론트엔드 대시보드 이식 및 구현 계획서

## 1. 개요
준비된 대시보드 템플릿(`gem_dashboard`)을 `sunflower87/fe` 환경으로 이식합니다. 사용자님의 지적대로 루트 경로의 기존 설정파일을 건드리지 않고, 오직 `src` 레벨에서의 융합(Direct Injection)을 수행하여 환경 불안정성을 원천 차단합니다.

## 2. 유지 및 보호 정책 (Must Preserve)

### 2-1. 기존 `fe` 소스 중 필수 유지 대상 (Root 레벨 및 기존 로직)
*   **Root 설정 파일 완전 보존**: `fe/` 루트에 있는 `.env`, `vite.config.js`, `tsconfig.json`, `eslint.config.js` 등의 기존 환경 설정 파일은 **절대 덮어쓰거나 변경하지 않습니다.**
*   **`fe/src/api/index.ts`**: 백엔드 통신 규격이 담긴 핵심 Fetch/Axios 모듈 보존.
*   **`fe/src/components/Dashboard/AssetDetailTab.tsx`**: 기 구현된 계좌별 주식 보유 현황(수익률, 평가손익 자동 계산) 테이블 컴포넌트 보존.

### 2-2. `gem_dashboard` 골격 보존 대상 (가져올 템플릿 로직)
*   **`main.tsx`, `App.tsx`**: 라우팅 및 테마 렌더링을 관장하는 진입점 원본 보존.
*   **구글 로그인 관련 모듈**: `Login.tsx` 및 관련 Context 등 인증 모듈 원본 보존.
*   **`Dashboard.tsx`**: 연관 API가 아직 BE에 없으므로 UI 템플릿 원본 상태를 그대로 유지.

## 3. [보유 자산] 메뉴 구현 방안 (`StockList.tsx`)

템플릿의 `src/pages/StockList.tsx`는 현재 더미 데이터를 출력하고 있습니다. 이를 실제 백엔드 연동 페이지로 개편합니다.

1.  **API 연동 (`/api/stocks/portfolio`)**
    *   `useEffect`를 통해 마운트 시 보존된 `api/index.ts`를 호출하여 백엔드 데이터를 가져옵니다.
    *   백엔드 로직(`portfolio.py`)에서 이미 `acc_order` 순으로 데이터를 정렬 응답하므로, 그대로 활용합니다.
2.  **`AssetDetailTab.tsx` 이식 및 교체**
    *   기존 더미 `<DataTable>` 렌더링 부분을 제거합니다.
    *   보존된 `AssetDetailTab` 컴포넌트를 삽입하고 응답받은 `accounts` 데이터를 Props로 전달합니다.
    *   **경로 호환성 수정**: `AssetDetailTab.tsx` 내부의 프라임리액트 등 UI 임포트 경로를 템플릿의 규격(`@/assets/ts/PrimeReact` 등)에 맞게 동기화합니다.

## 4. 세부 이식 절차 (Execution Steps)

1.  **소스 및 의존성 병합 준비**: 
    *   기존 `fe/src/api/index.ts`와 `AssetDetailTab.tsx`를 임시 백업합니다.
    *   `gem_dashboard/package.json` 라이브러리 검토 (기존 `fe` 패키지로 충분함을 사전 확인 완료).
2.  **선별적 덮어쓰기 이식**: 
    *   `gem_dashboard/src/`와 `gem_dashboard/public/` 내부 파일만 `fe/`의 해당 경로로 복사합니다. (**루트 설정 파일은 절대 건드리지 않음**)
3.  **자산 복구 및 컴포넌트 리팩토링**: 
    *   백업해둔 `index.ts`와 `AssetDetailTab.tsx`를 `fe/src/` 내 알맞은 위치에 배치합니다.
    *   `StockList.tsx` 코드를 수정하여 `AssetDetailTab`과 연결합니다.
4.  **동작 검증**: `npm install` 후 `npm run dev`로 구동하여 프론트엔드가 기존 설정 하에서 오류 없이 빌드되고 보유 자산 메뉴가 출력되는지 확인합니다.

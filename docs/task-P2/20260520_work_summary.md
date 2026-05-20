# 2026-05-20 작업 요약

## 개요
오늘은 `fe`와 `be`를 동시에 정리하며 다음 목표를 수행했습니다:
- 프론트엔드 `Dashboard` 페이지를 동적 컴포넌트 로딩으로 전환
- React Hook lint 경고 및 `useEffect` 비동기 초기화 문제 수정
- 백엔드에서 `Prettier` 대신 `Black` 기반 포맷터 사용 체계로 전환
- `isort`와 `ruff`를 도입해 Python 코드 품질 검사/정리를 강화
- `npm run format` / `npm run lint` 명령으로 백엔드에서 실행 가능하도록 스크립트 구성

## 변경 사항 요약

### Frontend
- `fe/src/pages/Dashboard.jsx`
  - `AssetSummaryCard`, `AIRecommendationSection`, `AssetDetailTab`, `TransactionHistoryTab`, `TransactionDialog`를 `React.lazy`로 동적 임포트 전환
  - 전체 렌더를 `Suspense`로 감싸 로딩 폴백 제공
  - `useEffect` 초기화 로직을 내부 async 함수(`initializePage`)로 이동
  - `fetchAccountData` 및 `loadTransactions`를 `useCallback`으로 안정화
  - `transactionFilters`를 `useRef`로 추적하여 최신 상태 유지
  - `handleSearchStock`에서 예외 재던지기 시 `cause`를 포함하도록 수정

### Backend
- `be/.prettierrc` 제거
- `be/pyproject.toml`
  - 기존 `Black` 설정 유지
  - `isort` 설정 추가
  - `ruff` 설정 추가 및 `line-length`/`lint` 섹션으로 정리
- `be/package.json`
  - `format:isort`, `format:black`, `format` 스크립트 추가
  - `lint:ruff`, `lint` 스크립트 추가
- `be/requirements.txt`
  - `ruff`, `isort` 추가
- 가상환경(`be/venv`)에 `ruff`와 `isort` 설치

## 주요 파일
- `fe/src/pages/Dashboard.jsx`
- `be/pyproject.toml`
- `be/package.json`
- `be/requirements.txt`

## 실행 명령

### 백엔드 format
```powershell
cd C:\01_Projects\sunflower87\be
npm run format
```

### 백엔드 lint
```powershell
cd C:\01_Projects\sunflower87\be
npm run lint
```

### 개별 실행
```powershell
cd C:\01_Projects\sunflower87\be
.\venv\Scripts\python -m black .
.\venv\Scripts\python -m isort .
.\venv\Scripts\python -m ruff check .
```

## 결과
- `Dashboard.jsx` React 동적 임포트 및 hook 초기화 관련 lint 경고 제거
- 백엔드에서 `ruff` 설정 오류(`W503`, TOML 파싱 오류) 수정
- `npm run lint`가 `ruff check .`로 정상 동작
- Python 백엔드 포맷/린트 흐름을 `Black`/`isort`/`ruff`로 정리

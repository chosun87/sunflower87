# [FE-01] 프론트엔드 이식 및 구현 작업 체크리스트

## 1단계: 기존 자산 안전 백업 - 완료 ✅
- [x] `fe/src/api/index.ts` 백업
- [x] `fe/src/components/Dashboard/AssetDetailTab.tsx` 백업

## 2단계: 선별적 덮어쓰기 이식 (Direct Injection) - 완료 ✅
- [x] `gem_dashboard/src/*` -> `fe/src/` 로 복사
- [x] `gem_dashboard/public/*` -> `fe/public/` 로 복사 (루트 파일 보존)

## 3단계: 자산 복구 및 컴포넌트 연동 (`StockList.tsx`) - 완료 ✅
- [x] `index.ts`, `AssetDetailTab.tsx` 원위치 복구
- [x] `AssetDetailTab.tsx` Import 경로 동기화 (`js/PrimeReact` -> `ts/PrimeReact`)
- [x] `StockList.tsx` API(`/api/stocks/portfolio`) 연동 및 `AssetDetailTab` 부착

## 4단계: 동작 검증 - 완료 ✅
- [x] 프론트엔드 구동 시작 (`npm run dev` 백그라운드 프로세스 동작 중)
- [x] "보유자산" 메뉴 정상 출력 여부 점검 (백엔드 API 연동 성공)

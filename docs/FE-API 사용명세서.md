# 프론트엔드 API 사용 명세서 (FE-API 사용명세서)

### 1. 일일 잔고 동기화 API 호출
* **호출되는 API:** `POST /api/accounts/sync_account_daily_balance`
* **Source 파일명:** `src/api/index.ts`, `src/pages/SyncDailyBalance.tsx`
* **호출사유:** 사용자가 '데이터 관리' 화면에서 특정 기간(`start_date` ~ `end_date`)을 지정하여 전체 계좌의 일일 잔고 및 수익률을 강제로 재계산 및 동기화하기 위함.
* **테스트 결과:** ✅ **PASS** (TC-04 UI 연동 및 예외 차단 완벽히 통과 - 2026.05.29 완료)

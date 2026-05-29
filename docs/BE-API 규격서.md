# 백엔드 API 규격서 (BE-API 규격서)

## 내부 API

### 1. 전체 계좌 일일 잔고 동기화
* **API명:** 전체 계좌 일일 잔고 동기화
* **Method:** `POST`
* **URI:** `/api/accounts/sync_account_daily_balance`
* **파라미터:** (Body - JSON)
  ```json
  {
    "start_date": "YYYY-MM-DD", // Optional
    "end_date": "YYYY-MM-DD"    // Optional
  }
  ```
* **테스트 결과:** ✅ **PASS** (TC-01, TC-02, TC-03 통과 - 2026.05.29 완료)

### 2. 특정 계좌 일일 잔고 동기화
* **API명:** 특정 계좌 일일 잔고 동기화
* **Method:** `POST`
* **URI:** `/api/accounts/{acc_cd}/sync_account_daily_balance`
* **파라미터:**
  * Path: `acc_cd` (계좌 코드)
  * Body - JSON:
    ```json
    {
      "start_date": "YYYY-MM-DD", // Optional
      "end_date": "YYYY-MM-DD"    // Optional
    }
    ```
* **테스트 결과:** ✅ **PASS** (TC-01, TC-02, TC-03 통과 - 2026.05.29 완료)

## 외부 API
(현재 추가된 항목 없음)

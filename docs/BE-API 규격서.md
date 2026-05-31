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
  * Path: `acc_cd` (계좌코드)
  * Body - JSON:
    ```json
    {
      "start_date": "YYYY-MM-DD", // Optional
      "end_date": "YYYY-MM-DD"    // Optional
    }
    ```
* **테스트 결과:** ✅ **PASS** (TC-01, TC-02, TC-03 통과 - 2026.05.29 완료)

### 3. 계좌 목록 조회
* **API명:** 계좌 목록 조회
* **Method:** `GET`
* **URI:** `/api/accounts`
* **파라미터:** 
  * Query: `include_deleted` (boolean, Optional, default: false) - 삭제된 계좌 포함 여부
* **테스트 결과:** ✅ **PASS** (2026.05.30 완료)

### 4. 단일 계좌 조회
* **API명:** 단일 계좌 조회
* **Method:** `GET`
* **URI:** `/api/accounts/{acc_cd}`
* **파라미터:** 
  * Path: `acc_cd` (계좌코드)
* **테스트 결과:** ✅ **PASS** (2026.05.30 완료)

### 5. 계좌 등록
* **API명:** 계좌 등록
* **Method:** `POST`
* **URI:** `/api/accounts`
* **파라미터:** (Body - JSON)
  ```json
  {
    "acc_cd": "string",
    "acc_nm": "string",
    "acc_company_nm": "string",
    "dt_opened": "YYYY-MM-DD", // Optional
    "acc_order": 1 // Optional
  }
  ```
* **테스트 결과:** ✅ **PASS** (2026.05.30 완료)

### 6. 계좌 수정
* **API명:** 계좌 수정
* **Method:** `PUT`
* **URI:** `/api/accounts/{acc_cd}`
* **파라미터:**
  * Path: `acc_cd` (계좌코드)
  * Body - JSON:
    ```json
    {
      "acc_nm": "string", // Optional
      "acc_company_nm": "string", // Optional
      "dt_opened": "YYYY-MM-DD", // Optional
      "acc_order": 1 // Optional
    }
    ```
* **테스트 결과:** ✅ **PASS** (2026.05.30 완료)

### 7. 계좌 삭제 (소프트 삭제)
* **API명:** 계좌 삭제
* **Method:** `DELETE`
* **URI:** `/api/accounts/{acc_cd}`
* **파라미터:**
  * Path: `acc_cd` (계좌코드)
* **테스트 결과:** ✅ **PASS** (2026.05.30 완료)

## 외부 API
(현재 추가된 항목 없음)

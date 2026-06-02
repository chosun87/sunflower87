# 백엔드 API 규격서 (BE-API 규격서)

## 내부 API

### 1. 전체 계좌 일일 잔고 동기화
* **API명:** 전체 계좌 일일 잔고 동기화
* **Method:** `POST`
* **URI:** `/api/accounts/sync_balance_daily`
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
* **URI:** `/api/accounts/{acc_cd}/sync_balance_daily`
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

## OHLCV (Phase 7)

### 8. 종목별 과거 차트(Daily) 및 실시간(Current) 데이터 조회
* **API명:** OHLCV 데이터 조회
* **Method:** `GET`
* **URI:** `/api/stock_ohlcvs`
* **파라미터:** 
  * Query: `code` (string, 필수) - 종목코드
  * Query: `start_date` (string, Optional) - 조회 시작일 (YYYY-MM-DD)
  * Query: `end_date` (string, Optional) - 조회 종료일 (YYYY-MM-DD)
* **특징:** 오늘 날짜가 조회 기간에 포함될 경우 `stock_ohlcv_current` 데이터가 UNION 되어 반환됨. (fluctuation_rate -> fluctuation_rate 로 매핑됨)

### 9. 실시간 현재가 수집 및 갱신
* **API명:** 실시간 OHLCV 갱신
* **Method:** `POST`
* **URI:** `/api/stock_ohlcvs/current`
* **특징:** 보유 종목들에 대해 네이버 실시간 주식 데이터를 수집하여 `stock_ohlcv_current` 테이블에 저장 및 갱신합니다.

## 외부 API

### 1. pykrx 라이브러리 (한국거래소 정보 크롤링)
* **API명:** 일자별 주가(OHLCV) 조회
* **함수명:** `stock.get_market_ohlcv_by_date(start_date, end_date, ticker)`
* **용도:** 특정 종목의 과거 시고저종, 거래량, 거래대금, 등락률 데이터를 장 종료 후 수집하여 `stock_ohlcv_daily`에 저장할 때 사용.
* **비고:** Python 라이브러리 형태이므로 내부 함수로 호출되어 실행.

### 2. 네이버 금융 실시간 주가 API
* **API명:** 네이버 국내주식 실시간 시세
* **Method:** `GET`
* **URI:** `https://polling.finance.naver.com/api/realtime/domestic/stock/{code}`
* **파라미터:** 
  * Path: `code` (6자리 종목코드)
* **응답 주요 데이터:** `closePrice`(현재가/종가), `openPrice`(시가), `highPrice`(고가), `lowPrice`(저가), `accumulatedTradingVolume`(거래량), `fluctuationsRatio`(등락률, cr), `fluctuations`(대비, cv) 등
* **용도:** 장중 실시간 현재가 데이터를 수집하여 `stock_ohlcv_current`에 갱신 및 저장할 때 사용.

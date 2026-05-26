# BE-02 리뷰 (업데이트됨): 설계 문서와 실제 코드(be) 간 구현 차이 및 누락 분석

본 문서는 새롭게 확립된 **"테이블명/py파일명은 단수형, API 라우트 경로는 복수형"** 이라는 명확한 규칙 하에 수정된 `project_analysis.md`를 기준으로, 현재 개발된 `be` (백엔드) 폴더 내의 소스 코드를 다시 한 번 대조하고 분석한 결과입니다.

## 📌 규칙 준수 현황 점검
- **테이블명 (단수형):** `database.py` 내의 모든 테이블이 단수형(`account`, `transaction`, `transaction_cash` 등)으로 올바르게 설계되어 있습니다. (✅ 통과)
- **파이썬 파일명 (단수형):** `routers/` 하위의 파일들이 모두 단수형(`account.py`, `transaction.py` 등)으로 올바르게 분리되어 있습니다. (✅ 통과)
- **API 라우트 경로 (복수형):** 일부 라우터에서 API Prefix가 단수형으로 설정되어 있어 **수정이 필요**합니다.

---

## 🚀 수정이 필요한 코드 부분 및 누락된 엔드포인트

### 1. `account.py` (API Prefix: `/api/accounts` - ✅ 올바름)
**누락된 일자별 잔고(AccountDailyBalance) CRUD 엔드포인트:**
- `GET /api/accounts/{acc_cd}/daily-balances/{trade_date}` (특정 날짜 단일 조회) - **개설 필요**
- `POST /api/accounts/{acc_cd}/daily-balances` (커스텀 잔고 스냅샷 강제 생성/주입) - **개설 필요**
- `PUT /api/accounts/{acc_cd}/daily-balances/{trade_date}` (잔고 스냅샷 수치 수정) - **개설 필요**
- `DELETE /api/accounts/{acc_cd}/daily-balances/{trade_date}` (잔고 스냅샷 삭제) - **개설 필요**

### 2. `transaction.py` (API Prefix: `/api/transactions` - ✅ 올바름)
- **누락 없음**: 기획서가 `POST /api/transactions`로 업데이트됨에 따라, 실제 코드(`router.post("")`)와 기획서가 완벽하게 일치합니다.

### 3. `transaction_cash.py` (API Prefix 수정 필요 ⚠️)
- **Prefix 문제:** 현재 코드의 라우터 Prefix가 `/api/transaction_cash`(단수형)로 설정되어 있습니다. 이를 복수형인 **`/api/transaction_cashes`** 로 수정해야 합니다.
- **생성 엔드포인트:** 코드의 `POST ""` 방식이 업데이트된 기획서와 일치합니다.
**누락된 엔드포인트:**
- `GET /api/transaction_cashes/{id}` (단일 상세 조회) - **개설 필요**
- `PUT /api/transaction_cashes/{id}` (현금 거래 수정) - **개설 필요**

### 4. `stock.py` (API Prefix: `/api/stocks` - ✅ 올바름)
**누락이 가장 많은 라우터입니다. (현재 `/portfolio`, `/masters` 만 존재)**
- `GET /api/stocks` - **개설 필요**
- `GET /api/stocks/{acc_cd}/{stock_code}` - **개설 필요**
- `POST /api/stocks` - **개설 필요**
- `PUT /api/stocks/{acc_cd}/{stock_code}` - **개설 필요**
- `DELETE /api/stocks/{acc_cd}/{stock_code}` - **개설 필요**
- `GET /api/stocks/search` - **개설 필요**
- `GET /api/stocks/lookup` - **개설 필요**
- `POST /api/stocks/sync-master` - **개설 필요**
- `POST /api/stocks/master` - **개설 필요**
- `PUT /api/stocks/master/{stock_code}` - **개설 필요**
- `DELETE /api/stocks/master/{stock_code}` - **개설 필요**

### 5. `stock_ohlcv.py` (API Prefix 수정 필요 ⚠️)
- **Prefix 문제:** 현재 코드의 Prefix가 `/api/stock_ohlcv`(단수형)로 설정되어 있습니다. 이를 복수형인 **`/api/stock_ohlcvs`** 로 수정해야 합니다.
**누락된 엔드포인트:**
- `GET /api/stock_ohlcvs/{stock_code}/{trade_date}` - **개설 필요**
- `POST /api/stock_ohlcvs` - **개설 필요**
- `PUT /api/stock_ohlcvs/{stock_code}/{trade_date}` - **개설 필요**
- `DELETE /api/stock_ohlcvs/{stock_code}/{trade_date}` - **개설 필요**
**경로 차이점:**
- 기획서에는 `POST /api/stocks/refresh-prices` 로 정의되어 있으나 코드는 현재 `stock_ohlcv.py` 내의 `/refresh` (즉, `/api/stock_ohlcvs/refresh`)로 되어 있습니다. 이 부분은 기획서에 맞춰 이동하거나 유지할지 결정이 필요합니다.

### 6. `recommendation.py` (API Prefix: `/api/recommendations` - ✅ 올바름)
**누락된 엔드포인트:**
- `GET /api/recommendations/{stock_code}` (단일 상세 조회) - **개설 필요**
- `PATCH /api/recommendations/{stock_code}/feedback` (피드백 기능) - **개설 필요**

---

### 💡 최종 액션 플랜
1. **API Prefix 일괄 수정:** `transaction_cash.py` 와 `stock_ohlcv.py` 의 라우터 Prefix를 복수형(`cashes`, `ohlcvs`)으로 변경.
2. **누락 API 일괄 개설:** 위 리스트업된 누락 API 엔드포인트들을 모두 각 모듈에 추가하여 완벽한 RESTful CRUD 구현 완성.

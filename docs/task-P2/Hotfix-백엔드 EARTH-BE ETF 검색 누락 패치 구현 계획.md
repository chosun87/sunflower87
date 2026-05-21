# 🌍 [Hotfix] 백엔드 EARTH-BE ETF 검색 누락 패치 구현 계획

현재 `be/database.py`의 `init_db()` 함수에서는 서버 기동 시 KOSPI 및 KOSDAQ 종목들을 `pykrx`의 `get_market_price_change_by_ticker`를 통해 수집하여 `cache_stocks`에 시딩하고 있습니다. 이때 ETF 티커 리스트(`etf_tickers`)를 획득하기는 하나, KOSPI나 KOSDAQ 리스트에 존재하지 않는 순수 ETF 종목들(예: 396500)을 `cache_stocks` 테이블에 독립적으로 적재하는 루프가 누락되어 있습니다. 이로 인해 신규 검색 API에서 해당 ETF들이 검색되지 않는 문제가 발생했습니다.

## Proposed Changes

### `be/database.py`

#### [MODIFY] database.py
`init_db()` 내의 데이터베이스 시딩 프로세스를 아래와 같이 보강합니다.

1. **ETF 전용 적재 루프 추가:** 
   KOSPI와 KOSDAQ 데이터 적재 완료 직후, `etf_tickers`를 순회하는 루프를 추가합니다.
2. **동적 이름 조회 및 병합 (Upsert):**
   기존 KOSPI/KOSDAQ 루프에서 이미 처리된 ETF 종목은 건너뛰고, 처리되지 않은 ETF 종목들에 대해 `pykrx.stock.get_etf_ticker_name(ticker)`를 호출하여 이름을 구합니다.
3. **무결성 방어 (Self-Healing):**
   새로 수집된 ETF 종목은 `market="ETF"`로 지정하여 `cache_stocks` 테이블에 안전하게 적재(`db.add`)합니다. 단일 조회가 과도한 API 호출 부하를 일으킬 수 있으므로, 이미 DB에 존재하는(오프라인 마스터 등에서 유래한) 종목은 `pykrx` 이름 조회를 생략하도록 최적화합니다.

## User Review Required

- **[성능/부하 이슈]** `pykrx.stock.get_etf_ticker_name(ticker)`를 개별 호출하게 되면, 상장된 수백 개의 ETF에 대해 순차적 호출이 발생하여 첫 서버 기동 시(`lifespan`) 약간의 딜레이가 생길 수 있습니다. 이를 방지하기 위해 **1) 이미 캐시된 종목은 조회 생략**하고 **2) KOSPI/KOSDAQ 데이터프레임에 이미 이름이 포함된 경우는 병합**하는 로직을 기본으로 적용하겠습니다. 이 접근 방식에 동의하시나요?

## Verification Plan

### Manual Verification
1. 서버를 재기동하여 `init_db()` 라이프스팬 시딩이 정상 수행되는지 로그를 확인합니다.
2. `GET /api/stocks/search?keyword=396500` 호출을 통해 "TIGER 반도체TOP10" 종목이 `market="ETF"` 플래그와 함께 정상 반환되는지 확인합니다.

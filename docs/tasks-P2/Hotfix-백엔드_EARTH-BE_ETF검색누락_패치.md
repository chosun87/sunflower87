# 🌍 [Hotfix] 백엔드 EARTH-BE(어씨베) 긴급 패치 지시서

- **작성자:** 기획자 MOON(무니)
- **수신자:** 백엔드 개발자 EARTH-BE(어씨베)
- **프로젝트 명:** sunflower87 통합 자산 관리 대시보드 고도화
- **이슈 항목:** 신규 추가된 종목 검색 API에서 ETF 종목(예: 396500 TIGER 반도체TOP10) 검색 누락 현상 발생

---

## 🚨 원인 분석 (Root Cause)
- 현재 백엔드 코어 데이터 소스인 `pykrx` 라이브러리의 특성상, 일반 주식(KOSPI, KOSDAQ)과 ETF의 티커(Ticker) 리스트를 반환하는 함수가 완전히 분리되어 있습니다.
- 서버 기동 시(`lifespan` 초기화 단계) 종목 마스터(`cache_stocks`) 테이블을 시딩(Seeding)하는 과정에서 `stock.get_market_ticker_list()`만 호출하고, **ETF 종목을 조회하는 로직이 누락**되어 DB에 적재되지 않은 것이 확실합니다.

## 🛠️ 조치 지시 사항 (Action Items)
1. **종목 마스터 시딩 로직 확장:**
   - 종목 데이터를 수집하여 `cache_stocks` 테이블에 밀어 넣는 초기화 로직에 ETF 수집 로직을 추가하십시오.
   - *pykrx 호출 참고:* `stock.get_etf_ticker_list(date)`를 호출하여 ETF 종목 코드 리스트를 확보하십시오.
2. **데이터 병합 및 적재 (Upsert):**
   - 기존 KOSPI, KOSDAQ 리스트와 신규로 수집한 ETF 리스트를 병합(Merge)하여 `cache_stocks`에 적재하십시오.
   - P1 원장에 명시된 '마켓 정보(KOSPI/KOSDAQ/ETF) 자동 식별' 로직을 보강하여, 병합된 종목이 ETF일 경우 `market` 컬럼에 'ETF' 값이 정확히 기입되도록 자가 치유(Self-Healing)를 수행하십시오.
3. **무결성 테스트:**
   - 로컬 DB 초기화(또는 캐시 강제 갱신) 후, 검색 API를 통해 `396500` 코드를 입력했을 때 "TIGER 반도체TOP10"이 정상적으로 반환되는지 확인한 뒤 커밋하십시오.

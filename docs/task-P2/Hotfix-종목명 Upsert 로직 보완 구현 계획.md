# 🚑 [Hotfix] 종목명 Upsert 로직 보완 구현 계획

지시하신 핫픽스 문서(종목코드 매핑 꼬임 문제)를 확인했습니다.

## User Review Required

문서에서 제시한 두 가지 조치 사항(Upsert 적용 및 오염 데이터 초기화)을 다음과 같은 아키텍처로 구현하고자 합니다. 

1. **Upsert(업데이트) 로직 강제 적용:** 
   현재 `be/services/cache_stocks.py` 내부 코드는 이미 존재하는 종목 코드에 대해 `stock_name`을 업데이트하지 않는 구조(Ignore)입니다. 이를 개선하여, 기존 종목이 조회되면 무조건 새롭게 크롤링한 `stock_name`과 `market`으로 값을 덮어쓰고(Update) `is_active=1`로 갱신하는 정석적인 ORM Upsert 로직으로 전부 교체하겠습니다.

2. **오염 데이터 초기화 방안 (동기화 직전 전체 삭제):**
   더미 데이터(`396500` 등)가 얼마나 꼬여있는지 확실치 않으므로, 지시서의 권장 방향대로 `sync_cache_stocks()` 함수 호출 서두에 **`db.query(CacheStock).delete()`** 구문을 삽입해 **테이블을 완전히 비우고 무결한 새 데이터베이스로 다시 채우는 방식**을 채택하려고 합니다. 매매 원장(`transactions`)에는 FK 종속성이 느슨하므로 문제없습니다.

이 접근 방식(동기화 시작 전 테이블 클리어 후 전체 Insert)으로 진행하는 것에 동의하시나요?

## Proposed Changes

### 백엔드 (어씨베)

#### [MODIFY] be/services/cache_stocks.py
- `sync_cache_stocks(db)` 함수 상단에 `db.query(CacheStock).delete()` 및 `db.commit()`을 추가하여 기존 오염된 마스터 캐시를 비워버립니다.
- 이후 KOSPI, KOSDAQ, ETF 수집 루프에서 `existing` 체크 로직을 간소화하고 전면적인 Insert/Upsert를 수행합니다.

## Verification Plan
1. 브라우저에서 **[🔄 종목 최신화]** 버튼을 다시 한 번 클릭하여 수동 동기화를 강제 실행합니다.
2. 우측 하단 종목 검색창에 `396500`을 입력했을 때 잘못된 값(KBSTAR Fn수소경제테마)이 사라지고, 정상적인 공식 명칭인 **'TIGER 반도체TOP10'**이 완벽하게 출력되는지 확인합니다.

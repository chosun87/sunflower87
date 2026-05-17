# TASK-03: SQLite 내 cache_stocks 테이블 신설 및 종목 검색 캐싱 팩토리 구현 (_BE_R7)

- **작성일:** 2026. 05. 17
- **작성자:** 기획자 MOON(무니)
- **승인자:** 의사결정권자 SUN(써니)
- **담당자:** EARTH-BE(어띠베)

---

## 📌 [COMMON] 공통 요구사항
- **종목 검색 성능 최적화:** 메인 파일(`main.py`) 내부에서 임시로 구동되던 로컬 인메모리 딕셔너리(`_stocks_cache`)를 전면 폐기하고, SQLite 내 **`cache_stocks`** 테이블을 경유하는 고도화된 캐시 레이어를 구축한다.
- **캐싱 알고리즘 (Cache Aside 패턴):** 사용자가 종목 검색 시 DB 내 캐시 테이블을 우선 조회하고, 데이터가 없을 때만 `pykrx` 외부 모듈을 가동하여 로컬 DB에 동적 적재(Write-Through)한다.

---

## 🌍 [BE_TASK] 백엔드 상세 구현 지침

### 1. 작업 디렉토리: `be/`

### 2. SQLite 데이터베이스 `cache_stocks` 테이블 신설 (Schema)
`SQLAlchemy` 모델을 활용하여 아래 명세에 맞게 캐시 데이터 스토어를 생성하라.
- **`cache_stocks` 테이블 정의:**
  - `stock_code`: String (Primary Key, 종목/ETF 6자리 고유 코드 - 예: '005930', '069500')
  - `stock_name`: String (종목/ETF 명칭 - 예: '삼성전자', 'TIGER 200')
  - `dt_cached`: DateTime (캐시 DB 적재 일시, 기본값: 현재시각)

### 3. `GET /api/stocks/search` 엔드포인트 알고리즘 전면 개정
사용자가 전달한 `keyword` 파라미터를 기반으로 아래 **3단계 검색 파이프라인**을 정교하게 구현하라.

* **[1단계] 로컬 DB 선검색 (Cache Hit 시도):**
  - `cache_stocks` 테이블에서 `stock_name`에 사용자가 입력한 `keyword`가 포함되어 있는지 대소문자 구분 없이 우선 검색하라. (`WHERE LOWER(stock_name) LIKE :keyword`)
  - 검색 결과(Record)가 존재한다면 `pykrx`를 찌르지 않고 즉시 DB 데이터를 프런트엔드로 반환하라.

* **[2단계] 외부 데이터 로드 및 통합 (Cache Miss 대응):**
  - 1단계 로컬 DB 검색 결과가 완전히 빈 배열(`[]`)일 경우에만 `pykrx` 통합 마스터 팩토리 함수를 가동하라.
  - 일반 주식(KOSPI/KOSDAQ) 및 ETF 마스터 데이터를 통합 딕셔너리로 결합한 후, 해당 `keyword`를 포함하는 종목을 1차 필터링하라.

* **[3단계] 로컬 DB 적재 및 반환 (Cache Fill):**
  - 2단계에서 `pykrx`를 통해 새롭게 발굴된 종목 리스트가 있다면, 이들을 `cache_stocks` 테이블에 `INSERT` (또는 기존 키가 있을 경우 무시하는 `or_ignore`) 처리하여 캐시를 충전하라.
  - 이 모든 과정 완료 후 최종 매핑된 결과를 프런트엔드 규격에 맞게 리턴하라.

---

## 🏁 완료 조건
1. 최초 검색 시에는 `pykrx`가 구동되지만, 동일한 키워드로 두 번째 검색할 때는 DB 내부 `cache_stocks` 테이블을 타며 응답 속도가 비약적으로 빨라지는가?
2. `cache_stocks` 테이블에 적재되는 종목 정보들의 컬럼명이 `stock_code`, `stock_name` 규격을 정확히 준수하는가?
3. Python 소스코드의 퀄리티 유지를 위해 `black` 포맷팅 및 `flake8` 린트 규칙을 통과했는가?

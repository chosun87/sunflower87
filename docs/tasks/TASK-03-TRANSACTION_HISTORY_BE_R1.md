# TASK-03: SQLite DB 기반 매수/매도 거래 내역 및 종목코드 자동 검색 API 구현 (_BE_R1)

- **작성일:** 2026. 05. 17
- **작성자:** 기획자 MOON(무니)
- **승인자:** 의사결정권자 SUN(써니)
- **담당자:** EARTH-BE(어띠베)

---

## 📌 [COMMON] 공통 요구사항
- 데이터의 영속성과 대용량 통계 가공을 위해 파일 기반 관계형 데이터베이스인 **SQLite**를 전면 도입하고 `be/sunflower87.db` 파일로 격리 관리한다. (.gitignore 필수 등록)

## 🌍 [BE_TASK] 백엔드 상세 구현 지침
- **데이터베이스 스키마 설계:**
  - `transactions` 테이블: `id`(PK), `date`, `type`(BUY/SELL), `code`, `name`, `quantity`, `price`
  - `stocks` 테이블 (현재고): `code`(PK), `name`, `quantity`, `avg_price`
- **종목 검색 엔드포인트 신설:**
  - `GET /api/stocks/search?keyword={검색어}` 구현.
  - `pykrx` 라이브러리의 `stock.get_market_ticker_and_name()`를 활용하여 일반 주식 시장 마스터에서 종목명을 부분 일치 검색하여 6자리 코드를 리턴하라.
- **트랜잭션 API 구현:**
  - `POST /api/transactions/add` 호출 시 거래 내역을 적재함과 동시에 매수/매도 구분에 따라 `stocks` 테이블의 보유 수량과 평단가를 자동 계산하여 `UPSERT` 하는 비즈니스 로직을 단일 DB 트랜잭션으로 묶어 처리하라.

## 🏁 완료 조건
1. 매수 기록 등록 시 `transactions`와 `stocks` 테이블의 데이터 정합성이 깨지지 않고 저장되는가?
2. `be/sunflower87.db` 파일이 Git 추적에서 제외되었는가?

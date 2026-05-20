# 🌍 sunflower87 백엔드 EARTH-BE(어씨베) 코어 아키텍처 원장

- **Tech Stack:** FastAPI, SQLite, SQLAlchemy, pykrx
- **설계 철학:** 1인 환경 최적화(Single Worker), 완벽한 데이터 무결성, 자가 치유(Self-Healing)

## 📌 1. 데이터베이스 및 스키마 구조
- **SQLite 테이블 구성:** `account` (계좌), `transactions` (매매원장), `stocks` (보유잔고), `cache_stocks` (종목마스터), `stock_ohlcv_cache` (주가시계열).
- **무결성 검증:** Pydantic 계층에서 거래 수량/단가는 무조건 양수(Positive)로 검증한다.

## 📌 2. 기동 최적화 및 Lifespan 설계
- **Lifespan 기반 기동:** `init_db()` 및 마이그레이션(Schema Evolution)은 FastAPI의 `lifespan` 컨텍스트 매니저 내부에서 단 1회만 가동하여 중복 로그인을 방지한다.
- **자가 치유 (Self-Healing):** 서버 구동 시 종목 데이터 중 누락된 `market` 정보(KOSPI/KOSDAQ/ETF)를 자동 식별하여 채워 넣고, 시딩 중 에러 시 `db.rollback()`을 호출해 세션을 보호한다.

## 📌 3. 차트 데이터 수급 (80-Day Buffer)
- 20일 이동평균선(20MA)을 프론트엔드에서 계산하기 위해, API(`GET /api/stocks/ohlcv`)는 60일치가 아닌 **최소 80~100일치의 여유 버퍼 데이터**를 오름차순(ASC)으로 정렬하여 송출한다.
- 120일 기준의 Gap Backfill(빈틈 메우기) 또는 Purge(초기화 후 재수집) 알고리즘을 유지한다.

## 📌 4. 거래 원장 및 세금 처리
- **세금+수수료(`tax_fee`) 방어:** 매수 시 원금에 더해 차감하고, 매도 시 수익금에서 차감하여 예수금(`cash_balance`)을 정밀 역산한다.
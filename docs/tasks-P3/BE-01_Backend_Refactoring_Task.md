# [BE-01] 백엔드 및 DB 리팩토링 작업 체크리스트

## 1단계: DB 모델 전면 개편 (`database.py`) - 완료 ✅
- [x] `database.py` 모델 단수형 명칭 변경 및 컬럼 규격 통일
- [x] 신규 원장 모델 (`transaction_cash`, `account_daily_balance`) 신설
- [x] `stock_ohlcv_cache`에 `trading_value`, `fluctuation_rate` 추가 적용

## 2단계: 안전한 데이터 마이그레이션 (`migrate.py`) - 완료 ✅
- [x] `migrate.py` 작성 (기존 레거시 데이터 백업 -> 테이블 드랍 -> 재생성 -> 타입/명칭 변환 후 삽입)
- [x] 스크립트 실행 및 결과 검증 (3 accounts, 148 transactions 성공적 이식)

## 3단계: 상수화 및 Pydantic 스키마 정의 - 완료 ✅
- [x] `constants.py` 생성 및 Enum 정의 (`TradeType`, `CashType`, `MarketType` 등)
- [x] `schemas.py` 8개 테이블에 맞춰 전면 재작성 (명칭 단수화, `ApiResponse` 제네릭 래퍼 도입 등)

## 4단계: 비즈니스 코어 로직 분리 (`portfolio.py`) - 완료 ✅
- [x] `portfolio.py`로 이름 변경 및 리팩토링 (레거시 `portfolio_service.py` 삭제)
- [x] 예수금 및 이동평균 산정, 일자별 잔고 자동 연산 연대기 역산(Self-Healing) 로직 완벽 구현

## 5단계: FastAPI 라우터 단수화 및 규격 맞춤 - 완료 ✅
- [x] `be/git/` 디렉토리 하위로 마크다운 태스크 모듈 이전 (`git_task.py`, `git_service.py`)
- [x] `account.py`, `transaction.py`, `transaction_cash.py`, `stock.py`, `stock_ohlcv.py`, `recommendation.py` 분리 및 레거시 라우터 완전 삭제
- [x] `main.py` 라우터 마운트 경로 재설정 및 연동 완료

## 6단계: 구동 검증 - 완료 ✅
- [x] 백엔드 서버 구동 시작 (`uvicorn` 백그라운드 프로세스)
- [x] Swagger UI 연동 대기중 (`http://localhost:8000/docs`)

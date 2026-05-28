# 계좌 입출금 내역 및 현금 잔고 동기화 BE 개발 계획서

본 계획서는 `transaction_cash` 테이블 정상화에 따른 `initial_cash` 컬럼의 역할 대체 및 현금 잔고(`cash_balance`) 동기화 방안(백엔드)을 담고 있습니다.

## 1. 개요 및 요구사항 확인

1. **`initial_cash` 불필요 여부**
   - **결론: 불필요합니다.** 현재 `initial_cash`는 포트폴리오 자산을 계산할 때 현금 잔고의 '시작점(Base)' 역할을 합니다. 모든 현금 입출금을 `transaction_cash`에 'DEPOSIT(입금)' 등으로 기록하면, 이 내역들을 합산하는 것만으로 초기 잔고를 대체할 수 있습니다. 따라서 `initial_cash`는 사용 중단(Deprecated) 처리합니다.
2. **`transaction_cash` 레코드 추가 시 `cash_balance` 업데이트 여부**
   - **결론: 이미 자동으로 업데이트되도록 설계되어 있습니다.** 백엔드의 `portfolio_service.py` 내부 `recalculate_portfolio_for_account` 함수를 확인한 결과, 주식 매매 내역과 현금 입출금 내역(`transaction_cash`)을 모두 합산하여 `account.cash_balance`를 업데이트하도록 로직이 구현되어 있습니다. 즉, API를 통해 현금 매매 내역 을 추가/수정/삭제하면 자동으로 계좌의 현금 잔고가 동기화됩니다.

## 2. 상세 개발 계획

### 2.1 마이그레이션 정책 및 동의 필요 사항 (User Review Required)
기존에 입력되어 있던 `account` 테이블의 `initial_cash` 데이터 보존을 위해 마이그레이션을 진행합니다.
- 기존 `initial_cash` 금액만큼을 `transaction_cash`에 '초기 입금' 내역으로 자동 추가합니다.
- 이후 포트폴리오 계산 시 `initial_cash`의 참조를 0으로 강제합니다.

### 2.2 구현 상세 (Proposed Changes)

#### [MODIFY] `be/services/portfolio_service.py`
- `recalculate_portfolio_for_account` 함수 내에서 `cash_balance = float(account.initial_cash or 0.0)` 로직을 `cash_balance = 0.0` 으로 변경하여 `initial_cash` 의존성을 완전히 제거합니다.

#### [NEW] 데이터베이스 마이그레이션 스크립트 작성 (`be/migrate_cash.py` 등)
- 기존 `account`의 `initial_cash` 값을 조회하여 0보다 큰 경우, 해당 금액을 `transaction_cash` 테이블의 `DEPOSIT` 매매 내역 (적요: "초기 입금액 마이그레이션")으로 일괄 신규 생성하는 스크립트를 작성하여 1회 실행합니다.

#### API 검증
- 기존 작성된 `be/routers/transaction_cash.py`의 CRUD API가 프론트엔드 연동에 문제없이 정상 동작하는지 검증합니다.

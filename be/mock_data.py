from datetime import datetime
from database import SessionLocal, Stock


def get_enriched_accounts_data() -> dict:
    """SQLite 데이터베이스 account 및 stocks 테이블의 데이터를 로드하고 실시간 수익률 및 평가액을 계산하여 프런트엔드 규격에 맞춰 반환합니다."""
    db = SessionLocal()
    try:
        from database import Account, Stock

        # 1. 활성 계좌 목록 로드 (dtDeleted IS NULL, accOrder ASC)
        db_accounts = (
            db.query(Account)
            .filter(Account.dtDeleted == None)
            .order_by(Account.accOrder.asc())
            .all()
        )

        # 2. 보유 주식 목록 로드
        db_stocks = db.query(Stock).all()

        # 모의 현재가 매핑 (없을 경우 매입 평단가의 +5% 적용)
        current_prices = {
            "005930": 77000,  # 삼성전자
            "000660": 147000,  # SK하이닉스
            "005380": 250000,  # 현대차
            "035420": 185000,  # 네이버
            "360750": 14250,  # TIGER 미국S&P500
            "069500": 34650,  # KODEX 200
        }

        # 계좌별 주식 분배 사전 초기화
        account_stocks_map = {acc.accCode: [] for acc in db_accounts}

        # DB에 존재하는 주식을 각각의 계좌 번호에 따라 올바르게 분배 및 계산
        for stock in db_stocks:
            acct_code = stock.accCode or "A001"
            if acct_code not in account_stocks_map:
                account_stocks_map[acct_code] = []

            code = stock.code
            name = stock.name
            quantity = stock.quantity
            avg_price = stock.avg_price

            # 현재가와 수익률 계산
            current_price = current_prices.get(code, int(avg_price * 1.05))
            eval_profit_rate = (
                round(((current_price - avg_price) / avg_price) * 100, 2)
                if avg_price > 0
                else 0.0
            )

            account_stocks_map[acct_code].append(
                {
                    "code": code,
                    "name": name,
                    "quantity": quantity,
                    "avg_price": avg_price,
                    "current_price": current_price,
                    "eval_profit_rate": eval_profit_rate,
                }
            )

        accounts = []
        overall_total_eval = 0

        # 각 계좌별로 계산 및 DTO 조립
        for acc in db_accounts:
            stocks_list = account_stocks_map.get(acc.accCode, [])

            # 주식 평가액 계산
            stocks_purchase = sum(s["quantity"] * s["avg_price"] for s in stocks_list)
            stocks_eval = sum(s["quantity"] * s["current_price"] for s in stocks_list)

            # 총 평가금액 (주식 평가액 + 현금 잔고)
            total_eval = stocks_eval + acc.cashBalance
            # 총 매입금액 (주식 매입금액 + 현금 잔고)
            total_purchase = stocks_purchase + acc.cashBalance

            # 수익률 계산
            profit_rate = (
                round(((total_eval - total_purchase) / total_purchase) * 100, 2)
                if total_purchase > 0
                else 0.0
            )

            accounts.append(
                {
                    "id": acc.accCode,
                    "account_number": acc.accCode,
                    "alias": f"[{acc.accCompanyName}] {acc.accName}",
                    "balance": acc.cashBalance,  # 예수금 잔액 전달
                    "total_eval": total_eval,  # 총 평가액
                    "profit_rate": profit_rate,  # 계좌 총 수익률
                    "stocks": stocks_list,
                }
            )
            overall_total_eval += total_eval

        return {
            "status": "success",
            "total_asset": overall_total_eval,
            "accounts": accounts,
        }
    finally:
        db.close()


def get_mock_recommendations() -> dict:
    """기획자 MOON(무니)의 R1 명세 데이터 규격 준수 (date 및 data 키 포맷)

    오늘 날짜를 YYYYMMDD 포맷으로 동적 생성하여 전달합니다.
    """
    current_date = datetime.now().strftime("%Y%m%d")
    return {
        "status": "success",
        "date": current_date,
        "data": [
            {
                "name": "삼성전자",
                "code": "005930",
                "tag": "가치주",
                "reason": "외국인 최근 5일 연속 순매수세 유입 및 20일 이동평균선 지지 확인.",
                "score": 92,
            },
            {
                "name": "현대차",
                "code": "005380",
                "tag": "저PBR/배당",
                "reason": "정부 밸류업 프로그램 최대 수혜 예상. PBR 0.6배 수준으로 극심한 저평가 상태.",
                "score": 88,
            },
            {
                "name": "네이버",
                "code": "035420",
                "tag": "기술주",
                "reason": "RSI 지수 30 부근으로 단기 과매도 구간 진입에 따른 기술적 반등 기대.",
                "score": 85,
            },
        ],
    }

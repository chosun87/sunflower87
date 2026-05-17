from datetime import datetime

# SUN님의 미래에셋 3개 계좌 예시 데이터 (보안을 위해 계좌명만 노출)
# MOON 기획자님의 Mock 데이터 규격 준수
ACCOUNTS_DATA = {
    "status": "success",
    "total_asset": 150000000,
    "accounts": [
        {
            "id": "acc_01",
            "alias": "미래에셋 주식 종합 (일반)",
            "balance": 50000000,
            "total_eval": 55000000,
            "profit_rate": 10.0,
            "stocks": [
                {
                    "name": "삼성전자",
                    "code": "005930",
                    "quantity": 100,
                    "avg_price": 70000,
                    "current_price": 77000,
                    "eval_profit_rate": 10.0,
                },
                {
                    "name": "SK하이닉스",
                    "code": "000660",
                    "quantity": 30,
                    "avg_price": 140000,
                    "current_price": 147000,
                    "eval_profit_rate": 5.0,
                },
            ],
        },
        {
            "id": "acc_02",
            "alias": "미래에셋 ISA (절세)",
            "balance": 40000000,
            "total_eval": 38000000,
            "profit_rate": -5.0,
            "stocks": [
                {
                    "name": "TIGER 미국S&P500",
                    "code": "360750",
                    "quantity": 200,
                    "avg_price": 15000,
                    "current_price": 14250,
                    "eval_profit_rate": -5.0,
                }
            ],
        },
        {
            "id": "acc_03",
            "alias": "미래에셋 연정저축펀드",
            "balance": 60000000,
            "total_eval": 63000000,
            "profit_rate": 5.0,
            "stocks": [
                {
                    "name": "KODEX 200",
                    "code": "069500",
                    "quantity": 150,
                    "avg_price": 33000,
                    "current_price": 34650,
                    "eval_profit_rate": 5.0,
                }
            ],
        },
    ],
}


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

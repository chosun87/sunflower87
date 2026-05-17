from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# 보안 지침: 환경변수 로드
load_dotenv()

app = FastAPI(title="sunflower87 API")

# Phase 1: 로컬 개발 환경용 CORS 허용
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/accounts")
def get_miraeasset_accounts():
    # SUN님의 미래에셋 3개 계좌 예시 데이터 (보안을 위해 계좌명만 노출)
    # MOON 기획자님의 Mock 데이터 규격 준수
    return {
        "status": "success",
        "total_asset": 150000000,  # 3개 계좌 총자산
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


@app.get("/api/recommendations")
def get_ai_recommendations():
    # 기획자 MOON(무니)의 R1 명세 데이터 규격 준수
    return {
        "status": "success",
        "recommendations": [
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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

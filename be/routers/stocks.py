from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db, CacheStock
from sqlalchemy import func
from datetime import datetime, timedelta

router = APIRouter(prefix="/api/stocks", tags=["Market Stock"])


def get_offline_stocks() -> dict:
    """인터넷 차단, 스크래퍼 오동작 및 서비스 지연을 대비한
    상위 150+개 주요 우량 KOSPI, KOSDAQ 주식 및 대표 ETF 오프라인 마스터 사전입니다.
    """
    return {
        # KOSPI 대형주
        "005930": "삼성전자",
        "000660": "SK하이닉스",
        "373220": "LG에너지솔루션",
        "207940": "삼성바이오로직스",
        "005380": "현대차",
        "000270": "기아",
        "068270": "셀트리온",
        "105560": "KB금융",
        "055550": "신한지주",
        "005490": "POSCO홀딩스",
        "035420": "NAVER",
        "006400": "삼성SDI",
        "051910": "LG화학",
        "035720": "카카오",
        "012330": "현대모비스",
        "000810": "삼성화재",
        "066570": "LG전자",
        "086790": "하나금융지주",
        "003550": "LG",
        "015760": "한국전력",
        "032830": "삼성생명",
        "000100": "유한양행",
        "034730": "SK",
        "018260": "삼성에스디에스",
        "034020": "두산에너빌리티",
        "010950": "S-Oil",
        "090430": "아모레퍼시픽",
        "011200": "HMM",
        "010130": "고려아연",
        "009150": "삼성전기",
        "033780": "KT&G",
        "030200": "KT",
        "017670": "SK텔레콤",
        "259960": "크래프톤",
        "450080": "에코프로머티",
        "096770": "SK이노베이션",
        "323410": "카카오뱅크",
        "377300": "카카오페이",
        "028260": "삼성물산",
        "004020": "현대제철",
        "036570": "엔씨소프트",
        "009830": "한화솔루션",
        "042660": "한화오션",
        "272210": "한화시스템",
        "352820": "하이브",
        "079550": "LIG넥스원",
        "010140": "삼성중공업",
        "000720": "현대건설",
        "011780": "금호석유",
        "001040": "CJ",
        "097950": "CJ제일제당",
        "021240": "코웨이",
        "008770": "호텔신라",
        "071050": "한국금융지주",
        "005935": "삼성전자우",
        "307900": "한화에어로스페이스",
        "001450": "한화",
        "161390": "한국타이어앤테크놀로지",
        "089900": "롯데지주",
        "023530": "롯데쇼핑",
        "011170": "롯데케미칼",
        "007070": "GS",
        "078930": "GS",
        "006800": "미래에셋증권",
        "005940": "NH투자증권",
        "039490": "키움증권",
        "016360": "삼성증권",
        "001800": "한진칼",
        "002790": "아모레퍼시픽그룹",
        "008560": "메리츠금융지주",
        "003490": "대한항공",
        "020560": "아시아나항공",
        "051900": "LG생활건강",
        "000120": "CJ대한통운",
        "000990": "DB하이텍",
        "003000": "부광약품",
        "014680": "한솔케미칼",
        "011070": "LG이노텍",
        "010780": "아이에스동서",
        "285130": "SK케미칼",
        "316140": "우리금융지주",
        "361610": "SK아이이테크놀로지",
        "383220": "F&F",
        "012750": "에스원",
        "004170": "신세계",
        "069960": "현대백화점",
        "026960": "동서",
        "007310": "오뚜기",
        "004370": "농심",
        "000080": "하이트진로",
        "005250": "녹십자홀딩스",
        "006280": "녹십자",
        "001630": "종근당",
        "128940": "한미약품",
        "192820": "코스맥스",
        "047050": "포스코인터내셔널",
        "003240": "태광산업",
        "001130": "대한제강",
        "000060": "메리츠화재",
        "006260": "LS",
        "010120": "LS일렉트릭",
        "012630": "HDC현대산업개발",
        "001740": "SK네트웍스",
        "023590": "다우기술",
        "002380": "KCC",
        "005830": "DB손해보험",
        "000150": "두산",
        "271560": "오리온",
        "003030": "세아제강",
        "008350": "남선알미늄",
        "009240": "한샘",
        "005260": "동부건설",
        "001430": "세아베스틸지주",
        "005070": "코스모신소재",
        "009420": "한올바이오파마",
        "019170": "신풍제약",
        "004800": "효성",
        "298020": "효성티앤씨",
        "298050": "효성첨단소재",
        "298000": "효성화학",
        "079160": "CJ CGV",
        "035760": "CJ ENM",
        # KOSDAQ 대표 성장주
        "247540": "에코프로비엠",
        "086520": "에코프로",
        "058470": "리노공업",
        "022100": "포스코DX",
        "036930": "주성엔지니어링",
        "041510": "에스엠",
        "035900": "JYP Ent.",
        "122870": "와이지엔터테인먼트",
        "253450": "스튜디오드래곤",
        "196170": "알테오젠",
        "145020": "휴젤",
        "214150": "클래시스",
        "086900": "메디톡스",
        "005290": "동진쎄미켐",
        "036830": "솔브레인",
        "036490": "에스에프에이",
        "033640": "네패스",
        "038500": "컴투스",
        "078340": "컴투스홀딩스",
        "053030": "바이넥스",
        "060250": "NHN KCP",
        "035600": "KG이니시스",
        "039200": "오스코텍",
        "068760": "셀트리온제약",
        "293480": "카카오게임즈",
        "215600": "신흥에스이씨",
        # 한국 대표 ETF 시리즈
        "069500": "KODEX 200",
        "494890": "KODEX 200액티브",
        "102110": "TIGER 200",
        "252670": "KODEX 200선물인버스2X",
        "114800": "KODEX 인버스",
        "122630": "KODEX 레버리지",
        "233740": "KODEX 코스닥150레버리지",
        "251340": "KODEX 코스닥150선물인버스",
        "305720": "TIGER 2차전지테마",
        "371460": "TIGER 차이나전기차SOLACTIVE",
        "133690": "TIGER 미국나스닥100",
        "360750": "TIGER 미국S&P500",
        "381170": "TIGER 미국테크TOP10 INDXX",
        "329200": "TIGER 글로벌리튬&2차전지SOLACTIVE",
        "411060": "KODEX 미국나스닥100레버리지(합성)",
        "261220": "KODEX WTI원유선물(H)",
        "310970": "TIGER 미국필라델피아반도체나스닥",
        "396580": "TIGER 미국빅테크10",
        "409820": "KODEX 미국S&P500인버스(H)",
        "139230": "TIGER 200 IT",
        "157030": "TIGER 반도체",
        "091160": "KODEX 반도체",
    }


def get_stocks_master():
    """상위 주요 종목 마스터 딕셔너리를 구성하여 반환합니다.
    우선 오프라인 사전 데이터를 로드한 뒤, pykrx가 정상 작동하면 최신 종목들을 보충/합산하여 반환합니다.
    """
    # 1. 오프라인 마스터 선로드 (안정성 보장)
    integrated = get_offline_stocks()

    try:
        from pykrx import stock

        # 최신 영업일을 찾기 위해 오늘부터 역산
        current_date = datetime.now()
        for i in range(5):
            date_str = (current_date - timedelta(days=i)).strftime("%Y%m%d")
            try:
                # 일반 주식 (KOSPI/KOSDAQ) 티커 목록 로드
                kospi_tickers = stock.get_market_ticker_list(
                    date_str, market="KOSPI"
                )
                kosdaq_tickers = stock.get_market_ticker_list(
                    date_str, market="KOSDAQ"
                )
                etf_tickers = stock.get_etf_ticker_list(date_str)

                # pykrx의 경우 개별 루프 시 많은 요청(네트워크 지연/차단 위험)이 유발되므로,
                # 오프라인 백업이 부족한 부분 혹은 필수 종목 위주로 매핑을 시도하거나
                # KRX 스크래핑을 통한 업데이트를 제한적으로 시도합니다.
                if kospi_tickers or kosdaq_tickers or etf_tickers:
                    # KOSPI 종목 매핑 추가
                    for t in kospi_tickers[
                        :100
                    ]:  # 부하 방지를 위해 상위 100개 우선 매핑
                        if t not in integrated:
                            name = stock.get_market_ticker_name(t)
                            if name:
                                integrated[t] = name
                    # KOSDAQ 종목 매핑 추가
                    for t in kosdaq_tickers[:50]:
                        if t not in integrated:
                            name = stock.get_market_ticker_name(t)
                            if name:
                                integrated[t] = name
                    # ETF 종목 매핑 추가
                    for t in etf_tickers[:50]:
                        if t not in integrated:
                            name = stock.get_etf_ticker_name(t)
                            if name:
                                integrated[t] = name

                    print(
                        "Complemented stock master dynamically "
                        f"from pykrx for date {date_str}"
                    )
                    break
            except Exception as e:
                print(
                    f"Dynamic complementary fetch failed for {date_str}: {e}"
                )
                continue
    except Exception as e:
        print(f"Failed to load pykrx: {e}")

    return integrated


@router.get(
    "/search",
    summary="종목 검색 자동완성 API",
    description=(
        "입력된 키워드(종목명 또는 종목코드)를 기반으로 매칭되는 주식/ETF 목록을 반환합니다. "
        "Cache Aside 패턴에 따라 DB 캐시 조회를 우선 수행합니다."
    ),
)
def search_stocks(keyword: str = "", db: Session = Depends(get_db)):
    """종목명을 기반으로 종목코드를 자동 검색합니다 (부분 일치)."""
    if not keyword:
        return {"status": "success", "results": []}

    # [1단계] 로컬 DB 선검색 (Cache Hit 시도)
    keyword_lower = keyword.lower()
    db_results = (
        db.query(CacheStock)
        .filter(func.lower(CacheStock.stock_name).like(f"%{keyword_lower}%"))
        .all()
    )

    if db_results:
        results = [
            {"code": r.stock_code, "name": r.stock_name} for r in db_results
        ]
        # 부분매칭 정밀도 정렬 (검색어와 완전히 같거나 앞부분에 매칭되는 종목을 먼저 보여줌)
        results.sort(
            key=lambda x: (
                not x["name"].lower().startswith(keyword_lower),
                len(x["name"]),
            )
        )
        return {"status": "success", "results": results[:10]}

    # [2단계] 외부 데이터 로드 및 통합 (Cache Miss 대응)
    stocks_master = get_stocks_master()
    matched_stocks = []

    for code, name in stocks_master.items():
        if keyword_lower in name.lower() or keyword_lower in code:
            matched_stocks.append({"code": code, "name": name})

    # 부분매칭 정밀도 정렬
    matched_stocks.sort(
        key=lambda x: (
            not x["name"].lower().startswith(keyword_lower),
            len(x["name"]),
        )
    )

    # [3단계] 로컬 DB 적재 및 반환 (Cache Fill)
    if matched_stocks:
        for ms in matched_stocks:
            # 중복 방지를 위해 확인 후 INSERT
            existing = (
                db.query(CacheStock)
                .filter(CacheStock.stock_code == ms["code"])
                .first()
            )
            if not existing:
                cache_item = CacheStock(
                    stock_code=ms["code"], stock_name=ms["name"]
                )
                db.add(cache_item)
        try:
            db.commit()
        except Exception as e:
            db.rollback()
            print(f"Failed to commit cached stocks: {e}")

    return {"status": "success", "results": matched_stocks[:10]}

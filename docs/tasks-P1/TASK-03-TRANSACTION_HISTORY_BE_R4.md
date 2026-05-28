# TASK-03: 매매일시 커스텀 파싱 및 SQLite 데이터 적재 구현 (_BE_R4)

- **작성일:** 2026. 05. 17
- **작성자:** 기획자 MOON(무니)
- **승인자:** 의사결정권자 SUN(써니)
- **담당자:** EARTH-BE(어띠베)

---

## 📌 [COMMON] 공통 요구사항
- 프런트엔드에서 전송하는 커스텀 거래일시 문자열을 유연하게 받아, SQLite DB의 `transactions` 테이블 내부 `date` 컬럼에 정확한 시계열 데이터로 적재한다.
- 사용자가 거래일시를 비워서 보낸 경우(null 또는 빈 문자열), 백엔드 서버 시스템의 현재 시각(`datetime.now()`)을 기본값으로 강제 주입한다.

---

## 🌍 [BE_TASK] 백엔드 상세 구현 지침

### 1. 작업 디렉토리: `be/`

### 2. `POST /api/transactions/add` 수신 DTO 및 파싱 로직 개정
- 프런트엔드가 전송하는 JSON Request Body(Pydantic 스키마)에 `date` 필드를 선택적 항목(`Optional[str] = None`)으로 확장하라.
- **비즈니스 예외 처리 (시간 자동 할당):**
```python
# 어띠베 구현 가이드라인 코드
from datetime import datetime

@app.post("/api/transactions/add")
async def add_transaction(payload: TransactionSchema, db: Session = Depends(get_db)):
    # 1. 거래일시 파싱 및 디폴트값 제어
    if not payload.date:
        transaction_date = datetime.now() # 입력 안 하면 현재시각
    else:
        try:
            # 프런트엔드가 보낸 포맷에 맞춰 파싱 수행
            transaction_date = datetime.strptime(payload.date, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            transaction_date = datetime.now() # 포맷 오류 시 방어 코드로 현재시각 주입
```

### 3. SQLite DB 적재 및 정렬 검증
- 위에서 가공된 transaction_date 변수를 transactions 테이블의 date 컬럼에 바인딩하여 db.add() 처리를 완료하라.
- 이로 인해 과거 시점의 매매 내역 을 수동 입력하더라도, GET /api/transactions 호출 시 SQL의 ORDER BY date DESC 정렬 규칙에 의해 대시보드 타임라인에 실시간 순서대로 알맞게 정렬되는지 최종 데이터 흐름을 검증하라.

## 🏁 완료 조건
1. 런트엔드에서 date 필드를 생략하거나 빈 값으로 보냈을 때 백엔드가 오류 없이 현재 시간으로 저장하는가?
2. 과거 특정 날짜(예: 2026-05-01)를 지정해 날렸을 때 SQLite DB에 해당 시각으로 정상 인서트되는가?
3. 소스코드 정리를 위해 black 및 flake8 검사를 필히 수행했는가?

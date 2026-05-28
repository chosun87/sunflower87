# TASK-04: FastAPI 내장 Swagger UI 문서화 고도화 및 표준 확립 (_BE_R1)

- **작성일:** 2026. 05. 17
- **작성자:** 기획자 MOON(무니)
- **승인자:** 의사결정권자 SUN(써니)
- **담당자:** EARTH-BE(어띠베)

---

## 📌 [COMMON] 공통 요구사항
- **자동 문서화 극대화:** 주묵구구식 API 관리를 탈피하고, FastAPI가 내장한 `OpenAPI/Swagger UI` 기능(`http://localhost:8000/docs`)을 프로젝트 통합 명세서로 공식 채택한다.
- **가독성 통제:** 프런트엔드(어띠페)가 Swagger 화면만 보고도 각 API의 역할, 에러 코드, 데이터 포맷을 완벽히 이해할 수 있도록 코드 레벨의 메타데이터 입력을 의무화한다.

---

## 🌍 [BE_TASK] 백엔드 상세 구현 지침

### 1. 작업 디렉토리: `be/`

### 2. FastAPI 전용 API 태그(Tags) 및 메타데이터 정의
- `FastAPI()` 인스턴스 생성 시 메인 타이틀과 프로젝트 설명을 명시하라. (예: `title="sunflower87 API 코어"`, `description="미래에셋 멀티 계좌 및 AI 주식 추천 시스템"`)
- 각 APIRouter 등록 시 도메인별로 **`tags`**를 지정하여 Swagger 화면에서 API들이 예쁘게 그룹핑되도록 하라.
  - 계좌 관리: `tags=["Account"]`
  - 매매 원장: `tags=["Transaction"]`
  - 종목 캐시: `tags=["Market Stock"]`

### 3. 엔드포인트 데코레이터 및 Pydantic 필드 주석화 (★핵심)
- **함수형 주석 추가:** 모든 API 라우터 데코레이터에 `summary`와 `description`을 명시하여 무엇을 하는 API인지 서술하라.
- **Pydantic Field 활용:** Request Body 및 Response로 사용하는 모든 Pydantic 모델의 필드에 `Field(description="...")`와 `Field(examples=[...])`를 반드시 선언하라.

```python
# 어띠베 구현 참고용 파이썬 예시 가이드
from pydantic import BaseModel, Field

class TransactionCreateSchema(BaseModel):
    acc_code: str = Field(..., description="account 테이블의 acc_cd 참조 키", examples=["A001"])
    type: str = Field(..., description="매매 구분 (BUY: 매수, SELL: 매도)", examples=["BUY"])
    code: str = Field(..., description="종목/ETF 6자리 고유 코드", examples=["005930"])
    name: str = Field(..., description="종목/ETF 명칭", examples=["삼성전자"])
    quantity: int = Field(..., description="매매 수량", examples=[10])
    price: float = Field(..., description="매매 단가", examples=[71000.0])
```
### 4. HTTP 예외 처리(HTTPException) 명시화
- 400 Bad Request (예수금 부족, 과매도 에러) 또는 404 Not Found (존재하지 않는 매매 내역  삭제 시) 발생할 수 있는 에러 템플릿 응답 구조를 responses={400: {"model": ErrorResponse}} 형태로 라우터에 사전 선언하여 Swagger 문서상에 에러 규격이 자동으로 표기되도록 하라.

## 🏁 완료 조건
1. http://localhost:8000/docs 접속 시 모든 API가 Account, Transaction, Market Stock 그룹으로 깔끔하게 정렬되어 노출되는가?
2. 각 API를 펼쳤을 때 Request/Response 데이터 구조 옆에 한글 설명(description)과 예시 데이터(examples)가 친절하게 바인딩되어 있는가?
3. Python 소스코드에 black 포맷터 및 flake8 린트 규칙이 에러 없이 통과되는가?

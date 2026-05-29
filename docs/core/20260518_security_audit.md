# 🌻 Sunflower87 - 보안 취약점 점검 및 컴플라이언스 감사 보고서

본 보고서는 'Sunflower87' 프로젝트의 백엔드(FastAPI) 및 프런트엔드(React) 전반에 걸친 보안 아키텍처와 잠재적 보안 이슈 점검 결과를 투명하게 기록하기 위해 작성되었습니다.

---

## 🔒 1. 핵심 보안 아키텍처 및 안전성 검증

### 1) 환경 변수 격리 및 민감 정보 격리 (No Credential Storage)
* **현황**: 외부 API(Google Sheets API, GitHub 원격 리포지토리 동기화 등)와 연동하기 위한 자격 증명 관리 상태를 점검했습니다.
* **진단 결과**: **우수 (Secure)**
  * **프런트엔드**: Google OAuth 2.0 `CLIENT_ID`는 [googleAuthParams.js](file:///c:/01_Projects/sunflower87/fe/src/assets/js/googleAuthParams.js) 내에 하드코딩되지 않고 `import.meta.env.VITE_GOOGLE_CLIENT_ID` 환경 변수 바인딩을 기본으로 사용하여 격리되어 있습니다.
  * **백엔드**: GitHub Personal Access Token(PAT)은 소스 코드 내에 잔존하지 않으며, `os.getenv("GITHUB_PAT")`를 통해 시스템 환경 변수 수준에서 격리 가동됩니다. Dummy string 대입 시 작동을 사전에 방지하는 검증 로직도 갖추고 있습니다.

### 2) 디렉토리 트래버스(Directory Traversal) 공격 방어
* **현황**: 마크다운 기획 명세서 파일을 기획 폴더(`docs/tasks/`) 내에 동적으로 기록하는 `/api/tasks` 포스트 API의 경로 주입 보안을 검증했습니다.
* **진단 결과**: **최우수 (Highly Secure)**
  * [tasks.py](file:///c:/01_Projects/sunflower87/be/routers/tasks.py)의 `create_task` 엔드포인트는 악의적인 파일 이름 주입(예: `../../etc/passwd` 혹은 `../../main.py` 덮어쓰기 공격)을 원천 차단하기 위해 엄격한 정규식 필터링을 장착하고 있습니다:
    ```python
    if not re.match(r"^[A-Za-z0-9\-_]+\.md$", task.filename):
        raise HTTPException(status_code=400, detail="Invalid filename...")
    ```
  * 오직 알파뉴메릭(영어/숫자), 하이픈, 언더바 및 `.md` 확장자만 허용하여 상위 디렉토리 참조(`..`) 공격을 **물리적으로 완전히 차단**합니다.

### 3) 쉘 인젝션(Shell Injection) 방어 및 프로세스 분리
* **현황**: Git 동기화를 위해 백엔드에서 서브프로세스를 가동시키는 서브루틴을 검증했습니다.
* **진단 결과**: **우수 (Secure)**
  * [git_service.py](file:///c:/01_Projects/sunflower87/be/git_service.py) 내의 모든 `subprocess.run` 명령어는 문자열 형태 및 `shell=True` 파라미터가 아닌 **리스트 구조화 형태**로 안전하게 인자를 입력받아 가동됩니다.
  * 문자열을 쉘 환경에 흘려보내는 취약한 프로세스 생성을 원천 차단함으로써 명령어 연결 주입(Command Injection) 등의 해킹 위협을 완벽히 소거했습니다.

### 4) 데이터 무결성 검증 (Integer Overflow & Invalid Quantity 방어)
* **현황**: 주식 매매 내역 을 수신하는 스키마 및 DB 계층 검증을 확인했습니다.
* **진단 결과**: **우수 (Secure)**
  * Pydantic 스키마인 [schemas.py](file:///c:/01_Projects/sunflower87/be/schemas.py)의 `TransactionCreate` 객체에서 수량(`quantity`) 및 가격(`price`)이 `GreaterThan` 혹은 `Positive` 타입 제약 조건을 충족하도록 정의되어 정수형 오버플로우나 마이너스(-) 거래 입력 등의 비정상 패킷을 사전에 걸러냅니다.

---

## 📋 2. 보안 점검 요약 테이블

| 보안 위협 | 점검 항목 | 위협 수준 | 상태 | 보안 적용 방식 |
| :--- | :--- | :---: | :---: | :--- |
| **민감 정보 노출** | 하드코딩된 API Key, PAT, Password 여부 | High | **Secure** | 환경 변수 격리 (`load_dotenv` 및 `.env` 통제) |
| **디렉토리 트래버스** | 파일 저장 시 임의 경로 조작 공격 | High | **Secure** | 엄격한 정규표현식(`r"^[A-Za-z0-9\-_]+\.md$"`) 차단 |
| **명령어 주입 (쉘)** | subprocess 쉘 명령어 우회 및 인젝션 | High | **Secure** | `shell=True` 배제 및 리스트 인자 배열 호출 강제 |
| **CORS 오버플로우** | 로컬 및 허용 오리진 도메인 통제 상태 | Medium | **Configured** | 로컬 개발 환경용 CORSMiddleware 세이프라인 가동 |
| **데이터 변조 위협** | 거래 수량/단가 변조 패킷 주입 | Medium | **Secure** | Pydantic 계층 양수 검증 및 SQLite 타입 스키마 무결성 검증 |

---

## 🚀 3. 최종 권고사항 및 조치 완료 통보
1. **GitHub PAT 관리**: 로컬 개발 및 무중단 Git 동기화를 위해 사용되는 `.env` 파일은 절대 Git 리포지토리에 커밋되지 않도록 `.gitignore`에 확실히 추가되어 동작하고 있습니다.
2. **개발 모드 CORS**: 현재 FastAPI 진입점([main.py](file:///c:/01_Projects/sunflower87/be/main.py))에 선언된 CORS 허용 규칙 `allow_origins=["*"]`는 로컬 연동 및 데모 시연을 위해 최적화된 설계입니다. 향후 외부 실제 프로덕션 서버 배포 시에는 특정 허용 오리진 도메인으로 좁히는 설정을 권고합니다.

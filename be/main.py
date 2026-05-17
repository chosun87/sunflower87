import re
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

# 모듈화된 계층 임포트
from mock_data import ACCOUNTS_DATA, get_mock_recommendations
from git_service import commit_and_push_task

# 보안 지침: 환경변수 로드
load_dotenv()


# 기획자 MOON(무니)의 태스크 업로드 스펙 규격 정의
class TaskCreate(BaseModel):
    filename: str
    content: str


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
    """SUN님의 미래에셋 3개 계좌 예시 데이터 반환 (보안을 위해 계좌명만 노출)

    MOON 기획자님의 Mock 데이터 규격 준수
    """
    return ACCOUNTS_DATA


@app.get("/api/recommendations")
def get_ai_recommendations():
    """기획자 MOON(무니)의 R1 명세 데이터 규격 준수 (date 및 data 키 포맷)

    오늘 날짜에 맞춘 주식 가치주/성장주 목록 추천 데이터를 반환합니다.
    """
    return get_mock_recommendations()


@app.post("/api/tasks")
def create_task(task: TaskCreate):
    """지정된 이름과 내용을 기반으로 docs/tasks 디렉토리에 마크다운 형식 태스크 파일을 생성하고,

    Git에 자동으로 add, commit, push합니다. (보안 및 트래버스 방어 적용)
    """
    # 1. 파일 이름 유효성 검사 (디렉토리 트래버스 공격 차단 및 .md 확장자 확인)
    if not re.match(r"^[A-Za-z0-9\-_]+\.md$", task.filename):
        detail_msg = (
            "Invalid filename. Only alphanumeric, hyphens, "
            "underscores and .md extension are allowed."
        )
        raise HTTPException(
            status_code=400,
            detail=detail_msg,
        )

    # 2. 경로 설정 (프로젝트 루트의 docs/tasks)
    be_dir = Path(__file__).parent.resolve()
    project_root = be_dir.parent
    docs_tasks_dir = project_root / "docs" / "tasks"

    # docs/tasks 폴더가 없으면 자동 생성
    docs_tasks_dir.mkdir(parents=True, exist_ok=True)
    file_path = docs_tasks_dir / task.filename

    # 3. 파일 작성
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(task.content)
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to write file: {str(e)}",
        )

    # 4. Git 커밋 및 푸시 연동 처리 (GitService에 위임)
    git_result = commit_and_push_task(file_path, task.filename, project_root)

    msg = f"Task file '{task.filename}' successfully written."
    return {
        "status": "success",
        "message": msg,
        "path": str(file_path.relative_to(project_root)),
        "git": git_result,
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

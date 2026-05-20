import re
from pathlib import Path

from fastapi import APIRouter, HTTPException

from git_service import commit_and_push_task
from schemas import TaskCreate

router = APIRouter(prefix="/api/tasks", tags=["Task"])


@router.post(
    "",
    summary="기획 마크다운 태스크 생성 및 원격 Git 동기화 API",
    description=(
        "입력받은 파일명과 마크다운 내용을 기반으로 로컬 프로젝트 docs/tasks 폴더 내에 "
        "명세서를 물리 작성하고, Git 형상관리를 통해 원격 리포지토리에 자동 Push합니다."
    ),
)
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
    project_root = (
        be_dir.parent.parent
    )  # since routers/ is at be/routers/, we need be/routers/ -> be/ -> root
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

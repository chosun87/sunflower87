import os
import re
import subprocess
from pathlib import Path
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv

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
    # 기획자 MOON(무니)의 R1 명세 데이터 규격 준수 (date 및 data 키 포맷)
    return {
        "status": "success",
        "date": "20260517",
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


@app.post("/api/tasks")
def create_task(task: TaskCreate):
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

    # 4. Git 커밋 및 푸시 연동 처리
    try:
        # 현재 브랜치 이름 획득
        branch_res = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        )
        branch_name = branch_res.stdout.strip()

        # git add
        subprocess.run(
            ["git", "add", str(file_path)],
            cwd=project_root,
            check=True,
            capture_output=True,
        )

        # git commit
        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                f"docs: add {task.filename} task specification",
            ],
            cwd=project_root,
            capture_output=True,
            check=False,  # 변경 사항이 없을 수도 있으므로 예외 발생 금지
        )

        # push 리모트 설정 로드
        pat = os.getenv("GITHUB_PAT")
        username = os.getenv("GITHUB_USERNAME", "chosun87")
        repo = os.getenv("GITHUB_REPO", "sunflower87")

        # GITHUB_PAT가 실제 유효한 토큰 형식인지 검사 (URL 형식이나 단순 placeholder 배제)
        is_token_valid = (
            pat
            and pat != "YOUR_GITHUB_PAT"
            and not pat.startswith("http")
            and "github.com" not in pat
        )

        if is_token_valid:
            # PAT가 제공된 경우 인증 정보 포함 푸시
            push_url = f"https://{pat}@github.com/{username}/{repo}.git"
            push_res = subprocess.run(
                ["git", "push", push_url, branch_name],
                cwd=project_root,
                capture_output=True,
                text=True,
            )
        else:
            # PAT가 없거나 올바르지 않은 경우
            # 로컬 OS 자격 증명(SSH Key, Credential Manager 등) 자동 사용 푸시
            push_res = subprocess.run(
                ["git", "push", "origin", branch_name],
                cwd=project_root,
                capture_output=True,
                text=True,
            )

        push_output = push_res.stdout + "\n" + push_res.stderr
        push_status = "success" if push_res.returncode == 0 else "failed"

    except Exception as git_err:
        push_status = "error"
        push_output = str(git_err)

    msg = f"Task file '{task.filename}' successfully written."
    return {
        "status": "success",
        "message": msg,
        "path": str(file_path.relative_to(project_root)),
        "git": {
            "push_status": push_status,
            "output": push_output.strip(),
        },
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

import os
import subprocess
from pathlib import Path


def commit_and_push_task(file_path: Path, filename: str, project_root: Path) -> dict:
    """Git add, commit, push 작업을 순차적으로 실행하고 결과를 반환합니다.

    - 변경사항이 없어도 커밋 실패로 서버가 멈추지 않도록 예외 처리가 적용되어 있습니다.
    - GITHUB_PAT 환경변수가 유효하게 존재할 경우 인증된 URL을 사용해 푸시합니다.
    """
    try:
        # 1. 현재 브랜치 이름 획득
        branch_res = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=project_root,
            capture_output=True,
            text=True,
            check=True,
        )
        branch_name = branch_res.stdout.strip()

        # 2. git add
        subprocess.run(
            ["git", "add", str(file_path)],
            cwd=project_root,
            check=True,
            capture_output=True,
        )

        # 3. git commit
        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                f"docs: add {filename} task specification",
            ],
            cwd=project_root,
            capture_output=True,
            check=False,  # 변경 사항이 없을 수도 있으므로 예외 발생 금지
        )

        # 4. push 리모트 설정 로드 및 인증 확인
        pat = os.getenv("GITHUB_PAT")
        username = os.getenv("GITHUB_USERNAME", "chosun87")
        repo = os.getenv("GITHUB_REPO", "sunflower87")

        # GITHUB_PAT 유효성 검사 (URL 형식이나 단순 placeholder 배제)
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
            # PAT가 없거나 올바르지 않은 경우 로컬 자격 증명 사용
            push_res = subprocess.run(
                ["git", "push", "origin", branch_name],
                cwd=project_root,
                capture_output=True,
                text=True,
            )

        push_output = push_res.stdout + "\n" + push_res.stderr
        push_status = "success" if push_res.returncode == 0 else "failed"

        return {
            "push_status": push_status,
            "output": push_output.strip(),
        }

    except Exception as git_err:
        return {
            "push_status": "error",
            "output": str(git_err),
        }

from fastapi import APIRouter
from pathlib import Path
from pydantic import BaseModel
import schemas

router = APIRouter(prefix="/api/tasks", tags=["Task"])

DOCS_TASKS_DIR = Path("C:/01_Projects/sunflower87/docs/tasks-P3")

@router.post("", status_code=201)
def create_task(task: schemas.TaskCreate):
    DOCS_TASKS_DIR.mkdir(parents=True, exist_ok=True)
    file_path = DOCS_TASKS_DIR / task.filename
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(task.content)
        return {"status": "success", "message": f"Task created: {task.filename}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

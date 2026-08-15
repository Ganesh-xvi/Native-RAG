from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import verify_api_key
from src.schemas import TaskProgress, TaskResponse
from src.utils.tasks import get_task_manager

router = APIRouter(tags=["tasks"])


@router.get("/tasks/{task_id}", response_model=TaskResponse)
async def get_task_status(
    task_id: str,
    _: str = Depends(verify_api_key),
) -> TaskResponse:
    task_manager = get_task_manager()
    task = task_manager.get(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    progress = task["progress"]
    return TaskResponse(
        task_id=task["task_id"],
        type=task["type"],
        status=task["status"],
        progress=TaskProgress(**progress),
        source_file=task.get("source_file"),
        started_at=task["started_at"],
        completed_at=task.get("completed_at"),
        error=task.get("error"),
        result=task.get("result"),
    )

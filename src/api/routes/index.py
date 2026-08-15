from fastapi import APIRouter, Depends, status

from src.api.deps import verify_api_key
from src.rag.ingest import ingest_all_pdfs
from src.schemas import RebuildRequest, RebuildResponse
from src.utils.config import get_settings
from src.utils.tasks import get_task_manager

router = APIRouter(tags=["index"])


@router.post(
    "/index/rebuild",
    response_model=RebuildResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def rebuild_index(
    body: RebuildRequest | None = None,
    _: str = Depends(verify_api_key),
) -> RebuildResponse:
    settings = get_settings()
    body = body or RebuildRequest()
    settings.data_dir.mkdir(parents=True, exist_ok=True)
    pdf_files = sorted(settings.data_dir.glob("*.pdf"))

    task_manager = get_task_manager()
    task_id = task_manager.create_task("rebuild", files_found=len(pdf_files))

    def worker() -> dict:
        def progress(step: str, current: int, total: int) -> None:
            task_manager.update_progress(task_id, step, current, total)

        return ingest_all_pdfs(
            recreate=True,
            settings=settings,
            progress_callback=progress,
        )

    task_manager.run_in_background(task_id, worker)

    return RebuildResponse(
        task_id=task_id,
        status="pending",
        message="Rebuild started. Poll GET /tasks/{task_id} for progress.",
        files_found=len(pdf_files),
    )

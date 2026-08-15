import re
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from src.api.deps import verify_api_key
from src.rag.ingest import ingest_pdf
from src.schemas import IngestResponse
from src.utils.config import get_settings
from src.utils.logging import get_logger
from src.utils.tasks import get_task_manager

router = APIRouter(tags=["ingest"])
logger = get_logger("api.ingest")


def sanitize_filename(filename: str) -> str:
    name = Path(filename).name
    return re.sub(r"[^\w.\- ]", "_", name)


@router.post("/ingest", response_model=IngestResponse, status_code=status.HTTP_202_ACCEPTED)
async def ingest_document(
    file: UploadFile = File(...),
    recreate: bool = Form(default=False),
    _: str = Depends(verify_api_key),
) -> IngestResponse:
    settings = get_settings()

    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only PDF files are supported")

    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    if len(content) > settings.max_upload_size_bytes:
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum size of {settings.max_upload_size_mb} MB",
        )

    settings.data_dir.mkdir(parents=True, exist_ok=True)
    safe_name = sanitize_filename(file.filename)
    destination = settings.data_dir / safe_name
    destination.write_bytes(content)
    logger.info(
        "PDF uploaded | file=%s size_bytes=%s recreate=%s",
        safe_name,
        len(content),
        recreate,
    )

    task_manager = get_task_manager()
    task_id = task_manager.create_task("ingest", source_file=safe_name)

    def worker() -> dict:
        def progress(step: str, current: int, total: int) -> None:
            task_manager.update_progress(task_id, step, current, total)

        return ingest_pdf(
            destination,
            recreate=recreate,
            settings=settings,
            progress_callback=progress,
        )

    task_manager.run_in_background(task_id, worker)

    return IngestResponse(
        task_id=task_id,
        status="pending",
        message="Ingestion started. Poll GET /tasks/{task_id} for progress.",
    )

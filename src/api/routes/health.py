import httpx
from fastapi import APIRouter

from src.rag.ingest import get_document_count, index_is_loaded
from src.schemas import HealthResponse
from src.utils.config import get_settings

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    settings = get_settings()
    dependencies = {
        "groq": "configured" if settings.groq_api_key else "missing",
        "ollama": "unknown",
        "chroma": "loaded" if index_is_loaded() else "empty",
    }

    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(f"{settings.ollama_base_url}/api/tags")
            dependencies["ollama"] = (
                "reachable" if response.status_code == 200 else "unreachable"
            )
    except httpx.HTTPError:
        dependencies["ollama"] = "unreachable"

    return HealthResponse(
        status="ok",
        index_loaded=index_is_loaded(),
        document_count=get_document_count(),
        dependencies=dependencies,
    )

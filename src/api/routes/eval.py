from fastapi import APIRouter, Depends, HTTPException

from src.api.deps import verify_api_key
from src.rag.ingest import index_is_loaded
from src.schemas import EvalRequest, EvalResponse
from src.services.eval import run_evaluation

router = APIRouter(tags=["eval"])


@router.post("/eval", response_model=EvalResponse)
async def evaluate_rag(
    body: EvalRequest | None = None,
    _: str = Depends(verify_api_key),
) -> EvalResponse:
    if not index_is_loaded():
        raise HTTPException(
            status_code=503,
            detail="Index not loaded. Upload a PDF via POST /ingest first.",
        )

    body = body or EvalRequest()
    return run_evaluation(
        questions=body.questions,
        metrics=body.metrics,
    )

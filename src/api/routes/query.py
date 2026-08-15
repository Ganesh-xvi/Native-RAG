import json

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from src.api.deps import verify_api_key
from src.rag.chain import build_rag_chain, docs_to_sources, retrieve_context
from src.rag.ingest import index_is_loaded
from src.rag.prompts import RAG_PROMPT
from src.schemas import GuardrailInfo, QueryRequest, QueryResponse, SourceItem
from src.utils.config import get_settings
from src.utils.guardrails import GuardrailError, validate_input, validate_output
from src.utils.logging import get_logger

router = APIRouter(tags=["query"])
logger = get_logger("api.query")


def _ensure_index_loaded() -> None:
    if not index_is_loaded():
        raise HTTPException(
            status_code=503,
            detail="Index not loaded. Upload a PDF via POST /ingest first.",
        )


@router.post("/query", response_model=QueryResponse)
async def query_documents(
    body: QueryRequest,
    _: str = Depends(verify_api_key),
) -> QueryResponse:
    _ensure_index_loaded()
    settings = get_settings()

    try:
        question = validate_input(body.question, settings)
    except GuardrailError as exc:
        logger.warning("Query blocked by input guardrails | reason=%s", exc.reason)
        raise HTTPException(
            status_code=422,
            detail={"message": "Input blocked by guardrails", "reason": exc.reason},
        ) from exc

    chain, _, _ = build_rag_chain(settings, top_k=body.top_k)
    docs, _ = retrieve_context(question, top_k=body.top_k, settings=settings)
    logger.info("Query started | top_k=%s sources=%s", body.top_k or settings.retriever_top_k, len(docs))
    answer = chain.invoke(question)

    output_check = validate_output(
        answer,
        [doc.page_content for doc in docs],
        settings,
    )
    if not output_check["output_passed"]:
        logger.warning("Query blocked by output guardrails | reason=%s", output_check["reason"])
        raise HTTPException(
            status_code=422,
            detail={
                "message": "Output blocked by guardrails",
                "reason": output_check["reason"],
            },
        )

    sources = [SourceItem(**source) for source in docs_to_sources(docs)]
    logger.info("Query completed | answer_length=%s", len(output_check["answer"]))

    return QueryResponse(
        answer=output_check["answer"],
        sources=sources,
        question=question,
        guardrails=GuardrailInfo(
            input_passed=True,
            output_passed=True,
            output_reason=None,
        ),
    )


@router.post("/query/stream")
async def query_documents_stream(
    body: QueryRequest,
    _: str = Depends(verify_api_key),
) -> StreamingResponse:
    _ensure_index_loaded()
    settings = get_settings()

    try:
        question = validate_input(body.question, settings)
    except GuardrailError as exc:
        logger.warning("Stream query blocked by input guardrails | reason=%s", exc.reason)
        raise HTTPException(
            status_code=422,
            detail={"message": "Input blocked by guardrails", "reason": exc.reason},
        ) from exc

    docs, context = retrieve_context(question, top_k=body.top_k, settings=settings)
    logger.info("Stream query started | top_k=%s sources=%s", body.top_k or settings.retriever_top_k, len(docs))
    _, _, llm = build_rag_chain(settings, top_k=body.top_k)
    messages = RAG_PROMPT.format_messages(context=context, question=question)

    async def event_generator():
        collected: list[str] = []
        for chunk in llm.stream(messages):
            token = chunk.content
            if token:
                collected.append(token)
                yield f"data: {json.dumps({'token': token})}\n\n"

        full_answer = "".join(collected)
        output_check = validate_output(
            full_answer,
            [doc.page_content for doc in docs],
            settings,
        )
        payload = {
            "done": True,
            "answer": output_check["answer"],
            "output_passed": output_check["output_passed"],
            "output_reason": output_check["reason"],
            "sources": docs_to_sources(docs),
        }
        yield f"data: {json.dumps(payload)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")

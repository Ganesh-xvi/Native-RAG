from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.middleware.logging import RequestLoggingMiddleware
from src.api.routes import eval as eval_routes
from src.api.routes import health as health_routes
from src.api.routes import index as index_routes
from src.api.routes import ingest as ingest_routes
from src.api.routes import query as query_routes
from src.api.routes import tasks as tasks_routes
from src.rag.ingest import get_document_count, index_is_loaded
from src.utils.config import get_settings
from src.utils.logging import get_logger, setup_logging

logger = get_logger("api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    setup_logging(settings)

    settings.data_dir.mkdir(parents=True, exist_ok=True)
    settings.chroma_persist_dir.mkdir(parents=True, exist_ok=True)
    settings.task_store_dir.mkdir(parents=True, exist_ok=True)

    index_loaded = index_is_loaded()
    doc_count = get_document_count()

    app.state.settings = settings
    app.state.index_loaded = index_loaded
    app.state.document_count = doc_count

    logger.info(
        "Application startup | host=%s port=%s log_level=%s log_format=%s "
        "index_loaded=%s document_count=%s llm=%s embedding=%s",
        settings.api_host,
        settings.api_port,
        settings.log_level,
        settings.log_format,
        index_loaded,
        doc_count,
        settings.llm_model,
        settings.embedding_model,
    )

    yield

    logger.info("Application shutdown")


setup_logging()

app = FastAPI(
    title="4-RAG API",
    description="RAG pipeline with LangChain, Groq, Ollama, guardrails, and eval",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(RequestLoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health_routes.router)
app.include_router(ingest_routes.router)
app.include_router(tasks_routes.router)
app.include_router(index_routes.router)
app.include_router(query_routes.router)
app.include_router(eval_routes.router)

from langchain_core.vectorstores import VectorStoreRetriever

from src.rag.ingest import get_vectorstore
from src.utils.config import Settings, get_settings


def get_retriever(
    top_k: int | None = None, settings: Settings | None = None
) -> VectorStoreRetriever:
    settings = settings or get_settings()
    k = top_k or settings.retriever_top_k
    vectorstore = get_vectorstore(settings)
    return vectorstore.as_retriever(search_kwargs={"k": k})

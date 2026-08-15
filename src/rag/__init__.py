"""RAG pipeline: ingest, retrieve, chain, prompts."""

from src.rag.chain import (
    build_rag_chain,
    docs_to_sources,
    format_docs,
    query_rag,
    retrieve_context,
)
from src.rag.ingest import (
    get_document_count,
    index_is_loaded,
    ingest_all_pdfs,
    ingest_pdf,
    load_pdf,
    split_documents,
)
from src.rag.prompts import RAG_PROMPT
from src.rag.retriever import get_retriever

__all__ = [
    "RAG_PROMPT",
    "build_rag_chain",
    "docs_to_sources",
    "format_docs",
    "query_rag",
    "retrieve_context",
    "get_retriever",
    "get_document_count",
    "index_is_loaded",
    "ingest_all_pdfs",
    "ingest_pdf",
    "load_pdf",
    "split_documents",
]

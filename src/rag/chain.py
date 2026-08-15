from typing import Any

from langchain_core.documents import Document
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough

from src.rag.prompts import RAG_PROMPT
from src.rag.retriever import get_retriever
from src.utils.config import Settings, get_settings
from src.utils.llm import get_llm


def format_docs(docs: list[Document]) -> str:
    return "\n\n".join(doc.page_content for doc in docs)


def docs_to_sources(docs: list[Document]) -> list[dict[str, Any]]:
    sources: list[dict[str, Any]] = []
    for doc in docs:
        sources.append(
            {
                "content": doc.page_content,
                "metadata": dict(doc.metadata),
                "score": doc.metadata.get("score"),
            }
        )
    return sources


def build_rag_chain(settings: Settings | None = None, top_k: int | None = None):
    settings = settings or get_settings()
    retriever = get_retriever(top_k=top_k, settings=settings)
    llm = get_llm(settings)

    chain = (
        {
            "context": retriever | format_docs,
            "question": RunnablePassthrough(),
        }
        | RAG_PROMPT
        | llm
        | StrOutputParser()
    )
    return chain, retriever, llm


def query_rag(
    question: str,
    *,
    top_k: int | None = None,
    settings: Settings | None = None,
) -> dict[str, Any]:
    settings = settings or get_settings()
    chain, retriever, _ = build_rag_chain(settings, top_k=top_k)
    docs = retriever.invoke(question)
    answer = chain.invoke(question)
    return {
        "answer": answer,
        "sources": docs_to_sources(docs),
        "question": question,
    }


def retrieve_context(
    question: str,
    *,
    top_k: int | None = None,
    settings: Settings | None = None,
) -> tuple[list[Document], str]:
    settings = settings or get_settings()
    retriever = get_retriever(top_k=top_k, settings=settings)
    docs = retriever.invoke(question)
    return docs, format_docs(docs)

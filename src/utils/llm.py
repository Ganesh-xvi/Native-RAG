from langchain_groq import ChatGroq
from langchain_ollama import OllamaEmbeddings

from src.utils.config import Settings, get_settings


def get_llm(settings: Settings | None = None) -> ChatGroq:
    settings = settings or get_settings()
    return ChatGroq(
        model=settings.llm_model,
        groq_api_key=settings.groq_api_key,
        temperature=0,
    )


def get_embeddings(settings: Settings | None = None) -> OllamaEmbeddings:
    settings = settings or get_settings()
    return OllamaEmbeddings(
        model=settings.embedding_model,
        base_url=settings.ollama_base_url,
    )

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    groq_api_key: str
    llm_model: str = "openai/gpt-oss-120b"
    embedding_model: str = "snowflake-arctic-embed:137m"
    ollama_base_url: str = "http://localhost:11434"

    api_key: str = "dev-api-key"

    data_dir: Path = Field(default=Path("./data"), alias="DATA_DIR")
    chroma_persist_dir: Path = Field(
        default=Path("./storage/chroma"), alias="CHROMA_PERSIST_DIR"
    )
    task_store_dir: Path = Field(
        default=Path("./storage/tasks"), alias="TASK_STORE_DIR"
    )

    chunk_size: int = Field(default=1000, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, alias="CHUNK_OVERLAP")
    retriever_top_k: int = Field(default=4, alias="RETRIEVER_TOP_K")

    max_question_length: int = Field(default=2000, alias="MAX_QUESTION_LENGTH")
    blocked_topics: str = Field(default="", alias="BLOCKED_TOPICS")
    max_upload_size_mb: int = Field(default=50, alias="MAX_UPLOAD_SIZE_MB")

    api_host: str = Field(default="0.0.0.0", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")

    gunicorn_workers: int = Field(default=2, alias="GUNICORN_WORKERS")
    gunicorn_timeout: int = Field(default=120, alias="GUNICORN_TIMEOUT")
    gunicorn_graceful_timeout: int = Field(default=30, alias="GUNICORN_GRACEFUL_TIMEOUT")
    gunicorn_keepalive: int = Field(default=5, alias="GUNICORN_KEEPALIVE")

    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    log_format: str = Field(default="text", alias="LOG_FORMAT")
    log_file: Path | None = Field(default=None, alias="LOG_FILE")

    golden_set_path: Path = Field(default=Path("./eval/golden_set.json"))

    @property
    def blocked_topics_list(self) -> list[str]:
        if not self.blocked_topics.strip():
            return []
        return [t.strip().lower() for t in self.blocked_topics.split(",") if t.strip()]

    @property
    def max_upload_size_bytes(self) -> int:
        return self.max_upload_size_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    return Settings()

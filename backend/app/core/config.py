"""
DevDocsAI — Core Configuration
Pydantic BaseSettings — all config from environment variables
"""
from functools import lru_cache
from typing import List

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── App ──────────────────────────────────────────
    app_name: str = "DevDocsAI"
    app_version: str = "1.0.0"
    debug: bool = False
    environment: str = "development"

    # ── API ──────────────────────────────────────────
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_v1_prefix: str = "/api/v1"

    # ── Security ─────────────────────────────────────
    secret_key: str = Field(default="change-me-in-production-minimum-32-chars-long")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440

    # ── Database ─────────────────────────────────────
    database_url: str = "sqlite+aiosqlite:///./devdocsai.db"

    # ── Redis / Celery ───────────────────────────────
    redis_url: str = "redis://localhost:6379/0"
    celery_broker_url: str = "redis://localhost:6379/0"
    celery_result_backend: str = "redis://localhost:6379/1"

    # ── ChromaDB ─────────────────────────────────────
    chroma_persist_dir: str = "./chroma_data"
    chroma_collection_name: str = "devdocsai_embeddings"

    # ── Embedding Model ──────────────────────────────
    embedding_model: str = "BAAI/bge-large-en-v1.5"
    embedding_batch_size: int = 32
    embedding_device: str = "cpu"

    # ── LLM ──────────────────────────────────────────
    llm_api_key: str = Field(default="")
    llm_base_url: str = "https://api.deepseek.com/v1"
    llm_model: str = "deepseek-chat"
    llm_max_tokens: int = 4096
    llm_temperature: float = 0.1

    @field_validator("llm_base_url")
    @classmethod
    def normalize_llm_base_url(cls, value: str) -> str:
        """OpenAI SDK expects the /v1 prefix in base_url."""
        value = value.rstrip("/")
        if not value.endswith("/v1"):
            value = f"{value}/v1"
        return value

    # ── GitHub ───────────────────────────────────────
    github_token: str = Field(default="")
    repo_clone_dir: str = "/tmp/devdocsai_repos"
    max_repo_size_mb: int = 500
    repo_clone_timeout_seconds: int = 120

    # ── Retrieval ────────────────────────────────────
    retrieval_top_k: int = 50
    reranker_top_k: int = 10
    reranker_model: str = "BAAI/bge-reranker-base"

    # ── V2 Agent Settings ─────────────────────────────
    agent_mode: str = "auto"  # "auto" | "v2" | "v1" — auto selects based on query complexity
    llm_provider: str = "deepseek"  # deepseek | gemini | groq | openrouter
    agent_max_reflection_cycles: int = 2
    agent_confidence_threshold: float = 0.75
    agent_timeout_ms: int = 30000  # Per-agent timeout (30s)
    agent_max_concurrent_queries: int = 10

    # ── CORS ─────────────────────────────────────────
    allowed_origins: str = "http://localhost:3000,http://localhost:5173"

    @property
    def allowed_origins_list(self) -> List[str]:
        return [o.strip() for o in self.allowed_origins.split(",")]


@lru_cache()
def get_settings() -> Settings:
    return Settings()


settings = get_settings()

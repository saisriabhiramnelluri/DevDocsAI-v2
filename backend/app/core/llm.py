"""
DevDocsAI — Shared LLM client (DeepSeek / OpenAI-compatible)
"""
from typing import Optional

from openai import AsyncOpenAI

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

_client: Optional[AsyncOpenAI] = None

_PLACEHOLDER_PREFIXES = ("your-", "sk-your-", "change-me", "sk-test")


def is_llm_configured() -> bool:
    key = settings.llm_api_key.strip()
    return bool(key) and not any(key.lower().startswith(p) for p in _PLACEHOLDER_PREFIXES)


def get_llm_client() -> AsyncOpenAI:
    """Return a shared AsyncOpenAI client configured for DeepSeek."""
    global _client
    if not is_llm_configured():
        raise RuntimeError(
            "LLM_API_KEY is not configured. Set your DeepSeek API key in backend/.env "
            "(https://platform.deepseek.com), then restart uvicorn."
        )
    if _client is None:
        _client = AsyncOpenAI(
            api_key=settings.llm_api_key,
            base_url=settings.llm_base_url,
            timeout=120.0,
            max_retries=2,
        )
    return _client

"""
DevDocsAI V2 — Provider-Agnostic LLM Abstraction Layer
========================================================
Agents never communicate directly with any LLM provider. They use
BaseLLM, which resolves the configured provider at runtime via
LLMFactory.

This does NOT modify the existing V1 `app.core.llm` module.
The V1 `get_llm_client()` remains for V1 code paths.

Supported providers (all OpenAI-compatible):
    - deepseek (default, uses existing LLM_API_KEY)
    - gemini   (via Gemini's OpenAI-compatible endpoint)
    - groq     (via Groq's OpenAI-compatible endpoint)
    - openrouter (via OpenRouter)

References:
    docs/README_V2_ARCHITECTURE.md §14 (Provider-Agnostic LLM Architecture)
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, AsyncIterator, Dict, List, Optional, Type

from openai import AsyncOpenAI
from pydantic import BaseModel

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


# ── Abstract LLM Interface ──────────────────────────────────────────────────

class BaseLLM(ABC):
    """Abstract LLM interface used by every agent."""

    @abstractmethod
    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> str:
        """Generate a complete response."""
        ...

    @abstractmethod
    async def stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """Stream response tokens."""
        ...

    @abstractmethod
    async def structured_output(
        self,
        messages: List[Dict[str, str]],
        output_schema: Type[BaseModel],
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> BaseModel:
        """Generate a response conforming to a Pydantic schema."""
        ...


# ── OpenAI-Compatible Implementation ────────────────────────────────────────

class OpenAICompatibleLLM(BaseLLM):
    """
    Concrete LLM implementation using the AsyncOpenAI client.
    Works with any OpenAI-compatible API: DeepSeek, Groq, OpenRouter,
    Gemini (via OpenAI compat endpoint), etc.
    """

    def __init__(
        self,
        api_key: str,
        base_url: str,
        model: str,
        timeout: float = 120.0,
        max_retries: int = 2,
    ) -> None:
        self.model = model
        self._client = AsyncOpenAI(
            api_key=api_key,
            base_url=base_url,
            timeout=timeout,
            max_retries=max_retries,
        )
        logger.info(
            "LLM provider initialized",
            model=model,
            base_url=base_url[:50],
        )

    async def generate(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> str:
        """Generate a complete response."""
        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return response.choices[0].message.content or ""
        except Exception as e:
            logger.error("LLM generate failed", model=self.model, error=str(e))
            raise

    async def stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> AsyncIterator[str]:
        """Stream response tokens."""
        try:
            response = await self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
            )
            async for chunk in response:
                content = chunk.choices[0].delta.content
                if content:
                    yield content
        except Exception as e:
            logger.error("LLM stream failed", model=self.model, error=str(e))
            raise

    async def structured_output(
        self,
        messages: List[Dict[str, str]],
        output_schema: Type[BaseModel],
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> BaseModel:
        """
        Generate a response conforming to a Pydantic schema.

        Strategy:
        1. Try native JSON mode with schema instruction in the prompt.
        2. Parse the LLM output as JSON and validate against the schema.
        3. On parse failure, retry once with explicit error feedback.
        """
        schema_json = json.dumps(output_schema.model_json_schema(), indent=2)
        schema_instruction = (
            f"\n\nYou MUST respond with ONLY a valid JSON object matching this schema:\n"
            f"```json\n{schema_json}\n```\n"
            f"Do NOT include any text outside the JSON object. No markdown fences, "
            f"no explanations — only the raw JSON."
        )

        # Inject schema instruction into the last user message
        augmented_messages = list(messages)
        if augmented_messages and augmented_messages[-1]["role"] == "user":
            augmented_messages[-1] = {
                "role": "user",
                "content": augmented_messages[-1]["content"] + schema_instruction,
            }
        else:
            augmented_messages.append({"role": "user", "content": schema_instruction})

        # Attempt 1
        raw = await self.generate(
            augmented_messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )

        parsed = self._try_parse(raw, output_schema)
        if parsed is not None:
            return parsed

        # Attempt 2 — feedback on parse failure
        logger.warning(
            "Structured output parse failed, retrying",
            schema=output_schema.__name__,
            raw_preview=raw[:200],
        )
        retry_messages = augmented_messages + [
            {"role": "assistant", "content": raw},
            {
                "role": "user",
                "content": (
                    "Your previous response was not valid JSON. "
                    "Please respond ONLY with a valid JSON object matching the schema. "
                    "No markdown, no explanations."
                ),
            },
        ]
        raw2 = await self.generate(retry_messages, temperature=0.0, max_tokens=max_tokens)
        parsed2 = self._try_parse(raw2, output_schema)
        if parsed2 is not None:
            return parsed2

        # Final fallback — try to extract JSON from the response
        raise ValueError(
            f"Failed to parse structured output as {output_schema.__name__} "
            f"after 2 attempts. Last response: {raw2[:300]}"
        )

    @staticmethod
    def _try_parse(raw: str, schema: Type[BaseModel]) -> Optional[BaseModel]:
        """Try to parse a raw string as JSON and validate against schema."""
        # Strip markdown fences if present
        text = raw.strip()
        if text.startswith("```"):
            lines = text.split("\n")
            # Remove first and last lines (fences)
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            text = "\n".join(lines).strip()

        try:
            data = json.loads(text)
            return schema.model_validate(data)
        except (json.JSONDecodeError, Exception):
            return None


# ── LLM Factory ──────────────────────────────────────────────────────────────

# Provider → (base_url, default_model, api_key_setting)
_PROVIDER_CONFIGS: Dict[str, Dict[str, str]] = {
    "deepseek": {
        "base_url": "https://api.deepseek.com/v1",
        "default_model": "deepseek-chat",
    },
    "gemini": {
        "base_url": "https://generativelanguage.googleapis.com/v1beta/openai",
        "default_model": "gemini-2.5-flash",
    },
    "groq": {
        "base_url": "https://api.groq.com/openai/v1",
        "default_model": "llama-3.3-70b-versatile",
    },
    "openrouter": {
        "base_url": "https://openrouter.ai/api/v1",
        "default_model": "deepseek/deepseek-chat",
    },
}

# Singleton LLM instance
_llm_instance: Optional[BaseLLM] = None


class LLMFactory:
    """Returns the configured LLM provider based on application settings."""

    @staticmethod
    def create(provider: Optional[str] = None) -> BaseLLM:
        """
        Create or return a cached LLM instance.

        Uses the existing V1 LLM config by default (api_key, base_url, model)
        unless a V2-specific provider is configured.
        """
        global _llm_instance
        if _llm_instance is not None:
            return _llm_instance

        provider = provider or getattr(settings, "llm_provider", "deepseek")

        if provider in _PROVIDER_CONFIGS:
            config = _PROVIDER_CONFIGS[provider]
            base_url = config["base_url"]
            model = getattr(settings, "llm_model", config["default_model"])
        else:
            # Fallback: use existing V1 settings
            base_url = settings.llm_base_url
            model = settings.llm_model

        api_key = settings.llm_api_key

        _llm_instance = OpenAICompatibleLLM(
            api_key=api_key,
            base_url=base_url,
            model=model,
        )
        return _llm_instance

    @staticmethod
    def reset() -> None:
        """Reset the singleton (for testing)."""
        global _llm_instance
        _llm_instance = None


def get_agent_llm() -> BaseLLM:
    """Convenience function to get the agent LLM instance."""
    return LLMFactory.create()

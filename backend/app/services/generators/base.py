"""
DevDocsAI — Base Generator
All generators share this class for LLM access and logging.
"""
from openai import APIConnectionError, AuthenticationError

from app.core.config import settings
from app.core.llm import get_llm_client
from app.core.logging import get_logger

logger = get_logger(__name__)

DOCBLOCK_SYSTEM = """You are an expert software engineer.
Your ONLY job is to add appropriate documentation comments to the code provided.
- Do NOT change any logic, variable names, or structure.
- Add language-appropriate docstrings/comments (JSDoc, PyDoc, Javadoc, etc.)
- Return ONLY the commented code — no explanations, no markdown fences."""

GENERAL_SYSTEM = """You are an expert software engineer and technical writer.
You produce precise, professional, developer-focused output.
Follow the user's instructions exactly."""


class BaseGenerator:
    """Shared LLM client for all generator services."""

    async def _call(
        self,
        user_prompt: str,
        system_prompt: str = GENERAL_SYSTEM,
        temperature: float = 0.1,
        max_tokens: int = 4096,
    ) -> str:
        try:
            client = get_llm_client()
            resp = await client.chat.completions.create(
                model=settings.llm_model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=temperature,
                max_tokens=max_tokens,
            )
            return resp.choices[0].message.content or ""
        except AuthenticationError:
            logger.error("Generator LLM authentication failed — check LLM_API_KEY in backend/.env")
            raise RuntimeError(
                "DeepSeek authentication failed. Verify LLM_API_KEY in backend/.env and restart the server."
            )
        except APIConnectionError as e:
            logger.error("Generator LLM connection failed", error=str(e), base_url=settings.llm_base_url)
            raise RuntimeError(
                f"Cannot reach DeepSeek API at {settings.llm_base_url}. Check your internet connection and try again."
            ) from e
        except Exception as e:
            logger.error("Generator LLM call failed", error=str(e))
            raise RuntimeError(f"LLM error: {e}") from e

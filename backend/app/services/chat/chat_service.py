"""
DevDocsAI — Chat Service (Phase 1)
Orchestrates: Hybrid Retrieval → Context Assembly → LLM → Response
Phase 2 upgrade: LangGraph planner agent
"""
import json
from typing import Any, AsyncGenerator, Dict, List, Optional

from openai import APIConnectionError, AuthenticationError

from app.core.config import settings
from app.core.llm import get_llm_client
from app.core.logging import get_logger
from app.services.retrieval.context_builder import ContextBuilder
from app.services.retrieval.hybrid_retriever import HybridRetriever

logger = get_logger(__name__)

# ── System Prompt ─────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """You are DevDocsAI, an expert AI Software Intelligence Platform that deeply understands software repositories.

You have access to structured knowledge extracted from the repository including:
- Abstract Syntax Tree (AST) analysis of all source files
- Function and class definitions with their relationships
- Import and dependency graphs
- Architecture patterns

Your role is to provide accurate, detailed, and insightful answers about the repository's codebase.

Guidelines:
- Answer based ONLY on the provided code context
- Include specific file paths and line numbers when referencing code
- Use markdown formatting for readability
- For architecture questions, describe component relationships
- For code questions, reference actual function/class names
- If you cannot find specific information in the context, say so clearly
- Never hallucinate code or functionality that isn't in the context"""

INTENT_INSTRUCTIONS = {
    "architecture": "Focus on high-level architecture, components, and their relationships.",
    "documentation": "Generate clear, comprehensive documentation with examples.",
    "security": "Focus on security patterns, potential vulnerabilities, and authentication flows.",
    "debugging": "Analyze the code for potential issues and trace the execution flow.",
    "general": "Provide a thorough explanation based on the code context.",
}


class ChatService:
    """
    Main chat orchestrator: retrieves context and calls LLM.
    """

    def __init__(self) -> None:
        self.retriever = HybridRetriever()
        self.context_builder = ContextBuilder()

    def _get_llm_client(self):
        return get_llm_client()

    def detect_intent(self, question: str) -> str:
        """Simple keyword-based intent detection (Phase 1)."""
        q = question.lower()
        if any(w in q for w in ["architecture", "design", "structure", "overview", "diagram"]):
            return "architecture"
        if any(w in q for w in ["readme", "document", "api doc", "onboard", "guide"]):
            return "documentation"
        if any(w in q for w in ["security", "vulnerability", "auth", "jwt", "token", "secret"]):
            return "security"
        if any(w in q for w in ["bug", "error", "debug", "fix", "issue", "crash"]):
            return "debugging"
        return "general"

    async def chat(
        self,
        repo_id: str,
        question: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> Dict[str, Any]:
        """
        Main chat method.
        Returns: {answer, sources, graph_context, intent, model}
        """
        intent = self.detect_intent(question)
        logger.info("Chat query", repo_id=repo_id, intent=intent, question=question[:80])

        # 1. Hybrid Retrieval
        results = self.retriever.retrieve(
            repo_id=repo_id,
            query=question,
            top_k=settings.retrieval_top_k,
        )

        if not results:
            return {
                "answer": "I couldn't find relevant information in this repository. The repository may still be processing, or the topic may not be covered in the codebase.",
                "sources": [],
                "graph_context": [],
                "intent": intent,
                "model": settings.llm_model,
            }

        # 2. Build context
        context = self.context_builder.build_context(results, max_tokens=5000)
        sources = self.context_builder.build_source_references(results, top_n=settings.reranker_top_k)

        # 3. Build graph context
        graph_context = [
            r.metadata for r in results
            if r.metadata.get("type") == "graph_context"
        ][:5]

        # 4. Build messages
        intent_instruction = INTENT_INSTRUCTIONS.get(intent, INTENT_INSTRUCTIONS["general"])
        user_prompt = f"""Repository Code Context:
{context}

---
Question: {question}

{intent_instruction}

Please provide a comprehensive answer based on the code context above."""

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if conversation_history:
            # Include last 6 messages for context continuity
            messages.extend(conversation_history[-6:])
        messages.append({"role": "user", "content": user_prompt})

        # 5. Call LLM
        answer = await self._call_llm(messages)

        return {
            "answer": answer,
            "sources": sources,
            "graph_context": graph_context,
            "intent": intent,
            "model": settings.llm_model,
        }

    async def _call_llm(self, messages: List[Dict[str, str]]) -> str:
        """Call the LLM API (DeepSeek V3 via OpenAI-compatible API)."""
        try:
            client = self._get_llm_client()
            response = await client.chat.completions.create(
                model=settings.llm_model,
                messages=messages,
                max_tokens=settings.llm_max_tokens,
                temperature=settings.llm_temperature,
            )
            return response.choices[0].message.content or "No response generated."
        except Exception as e:
            logger.error("LLM call failed", error=str(e))
            return f"I encountered an error generating a response. Please check your LLM API configuration. Error: {str(e)}"

    async def generate_documentation(
        self,
        repo_id: str,
        doc_type: str,
        repo_summary: str,
        metadata: Optional[Dict] = None,
    ) -> str:
        """Generate documentation (README, API docs, onboarding)."""
        prompts = {
            "readme": f"""Based on this repository analysis, generate a comprehensive README.md:

Repository Summary:
{repo_summary}

Include: Project overview, features, installation, usage, API reference, contributing guidelines.
Use proper markdown formatting.""",

            "api": f"""Generate comprehensive API documentation for this repository:

Repository Summary:
{repo_summary}

Include: All endpoints, request/response formats, authentication, examples.
Use markdown with code blocks.""",

            "onboarding": f"""Generate a developer onboarding guide for this repository:

Repository Summary:
{repo_summary}

Include: Architecture overview, key components, development setup, code structure, common tasks.
Make it beginner-friendly.""",
        }

        prompt = prompts.get(doc_type, prompts["readme"])
        context_results = self.retriever.retrieve(repo_id=repo_id, query=f"generate {doc_type} documentation", top_k=30)
        context = self.context_builder.build_context(context_results, max_tokens=4000)

        full_prompt = f"{prompt}\n\nCode Context:\n{context}"
        messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": full_prompt},
        ]
        return await self._call_llm(messages)

    async def chat_stream(
        self,
        repo_id: str,
        question: str,
        conversation_history: Optional[List[Dict[str, str]]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Async generator that streams LLM response tokens as JSON events.
        Yields: {"type": "token", "content": "..."} or {"type": "done", ...} or {"type": "error", ...}
        """
        intent = self.detect_intent(question)
        logger.info("Chat stream query", repo_id=repo_id, intent=intent)

        # Retrieval
        results = self.retriever.retrieve(
            repo_id=repo_id,
            query=question,
            top_k=settings.retrieval_top_k,
        )

        if not results:
            yield json.dumps({
                "type": "error",
                "content": "I couldn't find relevant context in this repository. The repository may still be processing.",
            })
            return

        context = self.context_builder.build_context(results, max_tokens=5000)
        sources = self.context_builder.build_source_references(results, top_n=settings.reranker_top_k)

        intent_instruction = INTENT_INSTRUCTIONS.get(intent, INTENT_INSTRUCTIONS["general"])
        user_prompt = f"""Repository Code Context:
{context}

---
Question: {question}

{intent_instruction}

Please provide a comprehensive answer based on the code context above."""

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        if conversation_history:
            messages.extend(conversation_history[-6:])
        messages.append({"role": "user", "content": user_prompt})

        try:
            client = self._get_llm_client()
            stream = await client.chat.completions.create(
                model=settings.llm_model,
                messages=messages,
                max_tokens=settings.llm_max_tokens,
                temperature=settings.llm_temperature,
                stream=True,
            )

            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    yield json.dumps({"type": "token", "content": content})

            # Final event with metadata
            yield json.dumps({
                "type": "done",
                "sources": sources,
                "intent": intent,
                "model": settings.llm_model,
            })

        except Exception as e:
            logger.error("LLM stream failed", error=str(e))
            yield json.dumps({"type": "error", "content": f"Stream error: {str(e)}"})


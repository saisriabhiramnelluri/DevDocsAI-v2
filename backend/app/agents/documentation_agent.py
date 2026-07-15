"""
DevDocsAI V2 — Documentation Agent
=====================================
Wraps the existing ChatService.generate_documentation() for README,
API docs, and onboarding guide generation. V2 extensions include
context-enriched generation using retrieval results.

References:
    docs/README_V2_ARCHITECTURE.md §5.6 (Documentation Agent)
"""

from __future__ import annotations

from typing import List

from app.agents.base import BaseAgent
from app.agents.llm_provider import BaseLLM
from app.agents.schemas import AgentOutput, OrchestratorState
from app.agents.tools import repo_statistics, semantic_search
from app.core.logging import get_logger

logger = get_logger(__name__)


class DocumentationAgent(BaseAgent):
    """
    Handles documentation generation and documentation-related queries.
    Wraps existing ChatService.generate_documentation() for backward
    compatibility, with V2 enhancements for context-enriched generation.
    """

    def __init__(self, llm: BaseLLM) -> None:
        self.llm = llm

    @property
    def name(self) -> str:
        return "documentation"

    def get_tools(self) -> List:
        return [semantic_search, repo_statistics]

    async def execute(self, state: OrchestratorState) -> AgentOutput:
        repo_id = state.get("repo_id", "")
        query = state.get("query", "")
        retrieval_results = state.get("retrieval_results", [])
        repo_context = state.get("repo_context")

        # Determine doc type from query
        doc_type = self._detect_doc_type(query)

        # Check if we already have cached documentation
        cached = self._check_cached_docs(repo_id, doc_type)
        if cached:
            return AgentOutput(
                agent_name=self.name,
                result=cached,
                confidence=0.85,
                tools_used=["repo_statistics"],
                reasoning_summary=f"Returned cached {doc_type} documentation",
            )

        # Build context for generation
        context_parts = []

        # Repo metadata
        if repo_context and isinstance(repo_context, dict):
            context_parts.append(
                f"Repository: {repo_context.get('primary_language', 'unknown')} project, "
                f"framework: {repo_context.get('framework', 'unknown')}, "
                f"{repo_context.get('total_files', 0)} files, "
                f"{repo_context.get('total_functions', 0)} functions.\n"
                f"Summary: {repo_context.get('summary', 'No summary available')[:500]}"
            )

        # Retrieval results
        if retrieval_results:
            code_context = []
            for r in retrieval_results[:10]:
                if isinstance(r, dict):
                    meta = r.get("metadata", {})
                    name = meta.get("name", "")
                    file_path = meta.get("file", "")
                    content = r.get("content", "")[:400]
                    if content:
                        header = f"[{name}]" if name else "[chunk]"
                        if file_path:
                            header += f" ({file_path})"
                        code_context.append(f"{header}\n{content}")
            if code_context:
                context_parts.append("Code Context:\n" + "\n---\n".join(code_context))

        full_context = "\n\n".join(context_parts) if context_parts else "No context available."

        # Generate documentation
        system_prompt = (
            "You are DevDocsAI, an expert technical documentation writer.\n"
            "Generate clear, comprehensive, professional documentation based on "
            "the provided code context and repository analysis.\n"
            "Use proper markdown formatting with headers, code blocks, and lists."
        )

        doc_prompts = {
            "readme": (
                f"Generate a comprehensive README.md for this repository.\n"
                f"Include: Project overview, features, installation, usage, "
                f"API reference, configuration, contributing guidelines.\n\n"
                f"Context:\n{full_context}"
            ),
            "api": (
                f"Generate comprehensive API documentation.\n"
                f"Include: All endpoints, request/response formats, "
                f"authentication, error codes, examples.\n\n"
                f"Context:\n{full_context}"
            ),
            "onboarding": (
                f"Generate a developer onboarding guide.\n"
                f"Include: Architecture overview, key components, "
                f"development setup, code structure, common tasks.\n"
                f"Make it beginner-friendly.\n\n"
                f"Context:\n{full_context}"
            ),
            "general": (
                f"Answer the following documentation question:\n{query}\n\n"
                f"Context:\n{full_context}"
            ),
        }

        prompt = doc_prompts.get(doc_type, doc_prompts["general"])
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt},
        ]

        try:
            result = await self.llm.generate(messages, temperature=0.2, max_tokens=4096)
            confidence = 0.8 if len(result) > 200 else 0.5
        except Exception as e:
            logger.error("Documentation generation failed", error=str(e))
            result = f"Documentation generation failed: {str(e)}"
            confidence = 0.2

        tools = ["repo_statistics"]
        if retrieval_results:
            tools.append("semantic_search")

        return AgentOutput(
            agent_name=self.name,
            result=result,
            confidence=confidence,
            tools_used=tools,
            reasoning_summary=f"Generated {doc_type} documentation ({len(result)} chars)",
        )

    def _detect_doc_type(self, query: str) -> str:
        """Detect what type of documentation is requested."""
        q = query.lower()
        if any(kw in q for kw in ["readme", "readme.md"]):
            return "readme"
        if any(kw in q for kw in ["api doc", "endpoint", "swagger", "openapi"]):
            return "api"
        if any(kw in q for kw in ["onboard", "getting started", "setup guide", "developer guide"]):
            return "onboarding"
        return "general"

    def _check_cached_docs(self, repo_id: str, doc_type: str) -> str | None:
        """Check if documentation is already cached in the database."""
        try:
            stats = repo_statistics.invoke({"repo_id": repo_id})
            if not isinstance(stats, dict) or stats.get("error"):
                return None

            cache_map = {
                "readme": stats.get("readme_content"),
                "api": stats.get("api_doc_content"),
                "onboarding": stats.get("onboarding_content"),
            }

            cached = cache_map.get(doc_type)
            if cached and len(cached) > 100:
                return cached

        except Exception:
            pass
        return None

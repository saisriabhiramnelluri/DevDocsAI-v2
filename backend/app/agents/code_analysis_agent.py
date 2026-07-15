"""
DevDocsAI V2 — Code Analysis Agent
=====================================
Performs code review, security analysis, performance optimization,
and refactoring suggestions. Wraps existing generator services as
tools and synthesizes findings into structured reports.

References:
    docs/README_V2_ARCHITECTURE.md §5.7 (Code Analysis Agent)
"""

from __future__ import annotations

from typing import Any, Dict, List

from app.agents.base import BaseAgent
from app.agents.llm_provider import BaseLLM
from app.agents.schemas import AgentOutput, OrchestratorState
from app.agents.tools import semantic_search
from app.core.logging import get_logger

logger = get_logger(__name__)


class CodeAnalysisAgent(BaseAgent):
    """
    Performs code analysis: review, security, performance, refactoring.
    Uses retrieval to find relevant code, then applies LLM analysis
    with specialized prompts for each analysis type.
    """

    def __init__(self, llm: BaseLLM) -> None:
        self.llm = llm

    @property
    def name(self) -> str:
        return "code_analysis"

    def get_tools(self) -> List:
        return [semantic_search]

    async def execute(self, state: OrchestratorState) -> AgentOutput:
        query = state.get("query", "")
        retrieval_results = state.get("retrieval_results", [])

        # Determine analysis type
        analysis_type = self._detect_analysis_type(query)

        # Build code context from retrieval results
        code_context = self._build_code_context(retrieval_results)

        if not code_context:
            return AgentOutput(
                agent_name=self.name,
                result="No code context available for analysis.",
                confidence=0.2,
                tools_used=[],
                reasoning_summary="No code context available",
            )

        # Generate analysis
        system_prompt = self._get_system_prompt(analysis_type)
        user_prompt = (
            f"Analyze the following code based on the user's request.\n\n"
            f"User request: {query}\n\n"
            f"Code context:\n{code_context}"
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ]

        try:
            analysis = await self.llm.generate(
                messages, temperature=0.2, max_tokens=4096
            )
            confidence = 0.75 if len(analysis) > 200 else 0.5
        except Exception as e:
            logger.error("Code analysis failed", error=str(e))
            analysis = f"Code analysis failed: {str(e)}"
            confidence = 0.2

        return AgentOutput(
            agent_name=self.name,
            result=analysis,
            confidence=confidence,
            tools_used=["semantic_search"],
            reasoning_summary=(
                f"{analysis_type.replace('_', ' ').title()} analysis completed "
                f"({len(analysis)} chars)"
            ),
        )

    def _detect_analysis_type(self, query: str) -> str:
        """Detect what type of code analysis is requested."""
        q = query.lower()
        if any(kw in q for kw in ["security", "vulnerability", "injection", "xss", "csrf", "auth"]):
            return "security"
        if any(kw in q for kw in ["performance", "optimize", "slow", "bottleneck", "memory", "cpu"]):
            return "performance"
        if any(kw in q for kw in ["refactor", "clean", "restructure", "improve", "simplify"]):
            return "refactoring"
        if any(kw in q for kw in ["test", "testing", "coverage", "unit test"]):
            return "testing"
        return "code_review"

    def _get_system_prompt(self, analysis_type: str) -> str:
        """Get specialized system prompt for the analysis type."""
        prompts = {
            "security": (
                "You are an expert security engineer performing a code security review.\n"
                "Focus on:\n"
                "- Authentication and authorization vulnerabilities\n"
                "- Input validation and sanitization\n"
                "- SQL injection, XSS, CSRF risks\n"
                "- Secrets and credential management\n"
                "- Dependency vulnerabilities\n"
                "Rate each finding as: 🔴 Critical, 🟠 High, 🟡 Medium, 🟢 Low\n"
                "Provide specific remediation steps for each issue."
            ),
            "performance": (
                "You are an expert performance engineer analyzing code for optimization.\n"
                "Focus on:\n"
                "- Algorithm complexity (time and space)\n"
                "- Database query optimization (N+1, missing indexes)\n"
                "- Memory leaks and resource management\n"
                "- Caching opportunities\n"
                "- Async/concurrency improvements\n"
                "Provide specific, actionable optimization suggestions with expected impact."
            ),
            "refactoring": (
                "You are an expert software architect reviewing code for refactoring.\n"
                "Focus on:\n"
                "- SOLID principle violations\n"
                "- Code duplication and DRY violations\n"
                "- Function/class complexity (too large, too many responsibilities)\n"
                "- Design pattern opportunities\n"
                "- Naming and readability improvements\n"
                "Provide before/after examples where helpful."
            ),
            "testing": (
                "You are an expert test engineer analyzing code for test coverage.\n"
                "Focus on:\n"
                "- Missing test coverage\n"
                "- Edge cases not covered\n"
                "- Testability improvements (dependency injection, mocking)\n"
                "- Test quality and assertion completeness\n"
                "Suggest specific test cases with expected behavior."
            ),
            "code_review": (
                "You are an expert software engineer performing a thorough code review.\n"
                "Cover:\n"
                "- Code quality and readability\n"
                "- Potential bugs and edge cases\n"
                "- Error handling completeness\n"
                "- API design and interface quality\n"
                "- Documentation gaps\n"
                "- Security considerations\n"
                "Provide specific, constructive feedback with code references."
            ),
        }
        return prompts.get(analysis_type, prompts["code_review"])

    def _build_code_context(self, results: List[Dict[str, Any]]) -> str:
        """Build code context string from retrieval results."""
        if not results:
            return ""

        parts = []
        for i, r in enumerate(results[:12]):
            if not isinstance(r, dict):
                continue
            meta = r.get("metadata", {})
            name = meta.get("name", "")
            file_path = meta.get("file", "")
            content = r.get("content", "")

            if not content:
                continue

            header = f"[{i+1}]"
            if name:
                header += f" {name}"
            if file_path:
                header += f" ({file_path})"

            parts.append(f"{header}\n{content[:800]}")

        return "\n\n---\n\n".join(parts)

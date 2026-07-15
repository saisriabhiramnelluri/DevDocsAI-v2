"""
DevDocsAI V2 — Repository Understanding Agent
================================================
Loads and interprets repository metadata to provide project context
to other agents. This is mostly deterministic (reads from DB), so
confidence is typically high (0.95+).

References:
    docs/README_V2_ARCHITECTURE.md §5.3 (Repository Agent)
"""

from __future__ import annotations

import json
from typing import List

from app.agents.base import BaseAgent
from app.agents.schemas import AgentOutput, OrchestratorState, RepoContext
from app.agents.tools import repo_statistics
from app.core.logging import get_logger

logger = get_logger(__name__)


class RepositoryAgent(BaseAgent):
    """
    Loads repository metadata from the database and interprets it
    to produce a RepoContext for downstream agents.
    """

    @property
    def name(self) -> str:
        return "repository"

    def get_tools(self) -> List:
        return [repo_statistics]

    async def execute(self, state: OrchestratorState) -> AgentOutput:
        repo_id = state.get("repo_id", "")

        try:
            stats = repo_statistics.invoke({"repo_id": repo_id})
        except Exception as e:
            logger.error("Repository agent failed to fetch stats", error=str(e))
            return AgentOutput(
                agent_name=self.name,
                result=RepoContext(),
                confidence=0.2,
                tools_used=["repo_statistics"],
                reasoning_summary=f"Failed to fetch repository metadata: {str(e)[:100]}",
                error=str(e)[:200],
            )

        if not isinstance(stats, dict) or stats.get("error"):
            error_msg = stats.get("error", "Unknown error") if isinstance(stats, dict) else "Invalid response"
            return AgentOutput(
                agent_name=self.name,
                result=RepoContext(),
                confidence=0.2,
                tools_used=["repo_statistics"],
                reasoning_summary=f"Repository metadata unavailable: {error_msg}",
                error=error_msg,
            )

        # Parse languages
        languages = {}
        lang_str = stats.get("languages_detected", "")
        if lang_str:
            try:
                languages = json.loads(lang_str) if isinstance(lang_str, str) else lang_str
            except (json.JSONDecodeError, TypeError):
                pass

        # Determine project type
        project_type = self._infer_project_type(stats)

        # Build context
        context = RepoContext(
            primary_language=stats.get("primary_language") or "",
            languages=languages if isinstance(languages, dict) else {},
            framework=stats.get("framework"),
            architecture_type=stats.get("architecture_type"),
            project_type=project_type,
            total_files=stats.get("total_files", 0),
            total_functions=stats.get("total_functions", 0),
            total_classes=stats.get("total_classes", 0),
            total_lines=stats.get("total_lines", 0),
            summary=stats.get("summary") or stats.get("architecture_summary") or "",
            key_directories=[],
            entry_points=[],
        )

        # Calculate confidence based on data completeness
        confidence = self._score_confidence(context, stats)

        summary_parts = [f"{context.primary_language}"]
        if context.framework:
            summary_parts.append(f"framework: {context.framework}")
        if context.architecture_type:
            summary_parts.append(f"arch: {context.architecture_type}")
        summary_parts.append(f"type: {project_type}")
        summary_parts.append(f"{context.total_files} files, {context.total_functions} functions")

        return AgentOutput(
            agent_name=self.name,
            result=context,
            confidence=confidence,
            tools_used=["repo_statistics"],
            reasoning_summary=f"Repository context: {', '.join(summary_parts)}",
        )

    def _infer_project_type(self, stats: dict) -> str:
        """Infer project type from framework and metadata."""
        framework = (stats.get("framework") or "").lower()
        arch_type = (stats.get("architecture_type") or "").lower()
        summary = (stats.get("summary") or "").lower()

        if any(kw in framework for kw in ["fastapi", "flask", "django", "express", "spring"]):
            return "api_server"
        if any(kw in framework for kw in ["react", "vue", "angular", "next", "svelte"]):
            return "web_app"
        if any(kw in arch_type for kw in ["cli", "command"]):
            return "cli"
        if any(kw in summary for kw in ["library", "package", "sdk"]):
            return "library"
        if any(kw in summary for kw in ["api", "server", "backend"]):
            return "api_server"
        if any(kw in summary for kw in ["frontend", "web app", "dashboard"]):
            return "web_app"
        return "unknown"

    def _score_confidence(self, context: RepoContext, stats: dict) -> float:
        """Score confidence based on metadata completeness."""
        score = 0.5

        if context.primary_language:
            score += 0.1
        if context.framework:
            score += 0.1
        if context.architecture_type:
            score += 0.05
        if context.summary:
            score += 0.1
        if context.total_files > 0:
            score += 0.05
        if context.total_functions > 0:
            score += 0.05
        if stats.get("mermaid_diagram"):
            score += 0.05

        return self.clamp_confidence(score)

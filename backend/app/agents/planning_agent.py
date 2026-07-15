"""
DevDocsAI V2 — Planning Agent
===============================
Decomposes complex user queries into structured execution plans.
Each plan step contains a targeted retrieval query, priority level,
and expected entities — enabling the Retrieval Agent to perform
multi-step, focused retrieval instead of a single broad query.

References:
    docs/README_V2_ARCHITECTURE.md §5.2 (Planning Agent)
"""

from __future__ import annotations

from typing import List

from app.agents.base import BaseAgent
from app.agents.llm_provider import BaseLLM
from app.agents.schemas import (
    AgentOutput,
    ExecutionPlan,
    OrchestratorState,
    PlanStep,
)
from app.agents.tools import repo_statistics
from app.core.logging import get_logger

logger = get_logger(__name__)

# ── Planning Prompt ──────────────────────────────────────────────────────────

PLANNING_SYSTEM_PROMPT = """You are a Planning Agent for DevDocsAI, an AI Software Intelligence Platform.

Your job is to decompose a user's question about a software repository into a structured execution plan.
Each step in the plan should have a targeted search query optimized for semantic retrieval.

Think step-by-step:
1. What is the user really asking?
2. What information do we need to find?
3. What code entities (functions, classes, files) are likely relevant?
4. In what order should we search?
5. Do we need architecture analysis (dependency graphs, component diagrams)?
6. Do we need code analysis (review, security, performance)?

Guidelines:
- Create 2-5 focused retrieval steps (not too many, not too few)
- Each step should have a specific, targeted search query
- Prioritize steps as "critical", "important", or "supplementary"
- Set requires_architecture=true if the question is about system design, dependencies, or component relationships
- Set requires_code_analysis=true if the question is about code quality, security, or performance
"""


class PlanningAgent(BaseAgent):
    """
    Decomposes complex queries into structured execution plans.
    Uses LLM structured_output() to generate ExecutionPlan.
    """

    def __init__(self, llm: BaseLLM) -> None:
        self.llm = llm

    @property
    def name(self) -> str:
        return "planning"

    def get_tools(self) -> List:
        return [repo_statistics]

    async def execute(self, state: OrchestratorState) -> AgentOutput:
        query = state.get("query", "")
        repo_id = state.get("repo_id", "")
        query_type = state.get("query_type", "general_code")

        # Get repo context hint for better planning
        repo_hint = ""
        try:
            stats = repo_statistics.invoke({"repo_id": repo_id})
            if isinstance(stats, dict) and not stats.get("error"):
                repo_hint = (
                    f"\nRepository info: {stats.get('repo_name', 'unknown')} "
                    f"({stats.get('primary_language', 'unknown')}, "
                    f"framework: {stats.get('framework', 'unknown')}, "
                    f"files: {stats.get('total_files', 0)}, "
                    f"functions: {stats.get('total_functions', 0)})"
                )
        except Exception:
            pass

        user_prompt = (
            f"User query: \"{query}\"\n"
            f"Query type: {query_type}\n"
            f"{repo_hint}\n\n"
            f"Generate a structured execution plan to answer this query. "
            f"Decompose it into 2-5 focused retrieval steps."
        )

        messages = [
            {"role": "system", "content": PLANNING_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        try:
            plan = await self.llm.structured_output(
                messages=messages,
                output_schema=ExecutionPlan,
                temperature=0.1,
                max_tokens=2048,
            )

            # Validate plan has at least one step
            if not plan.steps:
                plan = self._fallback_plan(query, query_type)

            step_count = len(plan.steps)
            return AgentOutput(
                agent_name=self.name,
                result=plan,
                confidence=self._score_confidence(plan),
                tools_used=["repo_statistics"] if repo_hint else [],
                reasoning_summary=(
                    f"Decomposed query into {step_count} steps "
                    f"(complexity: {plan.estimated_complexity})"
                ),
            )

        except Exception as e:
            logger.warning("Planning failed, using fallback plan", error=str(e))
            plan = self._fallback_plan(query, query_type)
            return AgentOutput(
                agent_name=self.name,
                result=plan,
                confidence=0.4,
                tools_used=[],
                reasoning_summary=f"Used fallback plan (planning failed: {str(e)[:100]})",
                error=str(e)[:200],
            )

    def _fallback_plan(self, query: str, query_type: str) -> ExecutionPlan:
        """Generate a simple fallback plan when LLM planning fails."""
        requires_arch = query_type in ("architecture", "complex_multi_hop")
        requires_code = query_type in ("code_review", "complex_multi_hop")

        return ExecutionPlan(
            goal=f"Answer: {query[:100]}",
            sub_goals=[query],
            steps=[
                PlanStep(
                    step_id=1,
                    description="Direct retrieval with original query",
                    retrieval_query=query,
                    target_entities=[],
                    priority="critical",
                    required_tools=["semantic_search"],
                ),
            ],
            estimated_complexity="simple",
            estimated_retrieval_cost=1,
            requires_architecture=requires_arch,
            requires_code_analysis=requires_code,
            required_agents=["retrieval"],
        )

    def _score_confidence(self, plan: ExecutionPlan) -> float:
        """Score confidence based on plan quality indicators."""
        score = 0.5

        # More steps → higher confidence (up to a point)
        if 2 <= len(plan.steps) <= 5:
            score += 0.2
        elif len(plan.steps) == 1:
            score += 0.05

        # Has sub-goals → structured thinking
        if plan.sub_goals:
            score += 0.1

        # Has critical steps → good prioritization
        critical_steps = [s for s in plan.steps if s.priority == "critical"]
        if critical_steps:
            score += 0.1

        # Has target entities → specific retrieval
        steps_with_entities = [s for s in plan.steps if s.target_entities]
        if steps_with_entities:
            score += 0.1

        return self.clamp_confidence(score)

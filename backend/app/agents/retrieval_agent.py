"""
DevDocsAI V2 — Retrieval Agent
================================
Wraps the existing HybridRetriever for plan-driven multi-step retrieval.
Instead of a single broad query, executes each PlanStep as a separate
targeted retrieval and aggregates with deduplication.

V1 HybridRetriever code is NOT modified — this agent wraps it.

References:
    docs/README_V2_ARCHITECTURE.md §5.4 (Retrieval Agent)
"""

from __future__ import annotations

from typing import Any, Dict, List, Set

from app.agents.base import BaseAgent
from app.agents.schemas import AgentOutput, OrchestratorState
from app.agents.tools import semantic_search
from app.core.logging import get_logger

logger = get_logger(__name__)


class RetrievalAgent(BaseAgent):
    """
    Multi-step retrieval agent that executes each plan step as a
    separate semantic_search call and aggregates results.
    """

    @property
    def name(self) -> str:
        return "retrieval"

    def get_tools(self) -> List:
        return [semantic_search]

    async def execute(self, state: OrchestratorState) -> AgentOutput:
        repo_id = state.get("repo_id", "")
        plan = state.get("execution_plan")

        # Extract retrieval queries from the plan
        queries = self._extract_queries(plan, state.get("query", ""))

        # Execute each query
        all_results: List[Dict[str, Any]] = []
        seen_chunks: Set[str] = set()
        tools_used = []

        for i, query_info in enumerate(queries):
            query_text = query_info["query"]
            top_k = query_info.get("top_k", 30)

            try:
                results = semantic_search.invoke({
                    "repo_id": repo_id,
                    "query": query_text,
                    "top_k": top_k,
                })

                if isinstance(results, list):
                    for r in results:
                        if isinstance(r, dict):
                            chunk_id = r.get("chunk_id", "")
                            if chunk_id and chunk_id not in seen_chunks:
                                seen_chunks.add(chunk_id)
                                # Tag with the retrieval step
                                r["retrieval_step"] = i + 1
                                r["retrieval_query"] = query_text
                                all_results.append(r)

                tools_used.append(f"semantic_search(step_{i+1})")
                logger.info(
                    "Retrieval step completed",
                    step=i + 1,
                    query_preview=query_text[:60],
                    results=len(results) if isinstance(results, list) else 0,
                )

            except Exception as e:
                logger.warning(
                    "Retrieval step failed",
                    step=i + 1,
                    error=str(e),
                )

        # Sort by score (highest first)
        all_results.sort(key=lambda r: r.get("score", 0), reverse=True)

        # Cap at reasonable limit
        all_results = all_results[:50]

        # Calculate confidence from scores
        confidence = self._score_confidence(all_results)

        return AgentOutput(
            agent_name=self.name,
            result=all_results,
            confidence=confidence,
            tools_used=tools_used,
            reasoning_summary=(
                f"Executed {len(queries)} retrieval steps, "
                f"found {len(all_results)} unique results"
            ),
        )

    def _extract_queries(self, plan: Any, fallback_query: str) -> List[Dict[str, Any]]:
        """
        Extract retrieval queries from the execution plan.
        Falls back to the original query if no plan is available.
        """
        queries = []

        if isinstance(plan, dict) and plan.get("steps"):
            for step in plan["steps"]:
                if isinstance(step, dict):
                    retrieval_query = step.get("retrieval_query", "")
                    if retrieval_query:
                        priority = step.get("priority", "important")
                        # Critical steps get more results
                        top_k = 30 if priority == "critical" else 20
                        queries.append({
                            "query": retrieval_query,
                            "top_k": top_k,
                            "step_id": step.get("step_id", 0),
                        })

        # Always include the original query as fallback
        if not queries:
            queries.append({
                "query": fallback_query,
                "top_k": 50,
                "step_id": 0,
            })

        return queries

    def _score_confidence(self, results: List[Dict[str, Any]]) -> float:
        """Score confidence based on retrieval quality."""
        if not results:
            return 0.1

        # Average score of top-10 results
        top_scores = [r.get("score", 0) for r in results[:10]]
        if not top_scores:
            return 0.2

        avg_score = sum(top_scores) / len(top_scores)

        # Scale: high-quality retrieval has scores > 0.5
        if avg_score > 0.5:
            confidence = 0.85 + (avg_score - 0.5) * 0.3  # 0.85–1.0
        elif avg_score > 0.3:
            confidence = 0.6 + (avg_score - 0.3) * 1.25  # 0.6–0.85
        else:
            confidence = 0.2 + avg_score * 1.33  # 0.2–0.6

        # Bonus for having many results
        if len(results) >= 15:
            confidence += 0.05
        elif len(results) < 5:
            confidence -= 0.1

        return self.clamp_confidence(confidence)

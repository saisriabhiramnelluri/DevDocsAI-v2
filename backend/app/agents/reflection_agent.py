"""
DevDocsAI V2 — Reflection Agent
==================================
Validates agent responses before returning to the user. Checks:
1. Answer completeness — does it address the full question?
2. Evidence coverage — are claims backed by retrieved code?
3. Citation accuracy — do file references exist in results?
4. Contradiction detection — conflicting statements?
5. Missing coverage — important files/entities missing?
6. Loop decision — trigger re-retrieval if confidence < threshold

Can trigger up to 2 additional retrieval cycles when quality is insufficient.

References:
    docs/README_V2_ARCHITECTURE.md §5.8 (Reflection Agent)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.agents.base import BaseAgent
from app.agents.llm_provider import BaseLLM
from app.agents.schemas import (
    AgentOutput,
    OrchestratorState,
    ReflectionResult,
)
from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

REFLECTION_SYSTEM_PROMPT = """You are a Reflection Agent for DevDocsAI, an AI Software Intelligence Platform.

Your job is to validate the quality of a generated answer before it is returned to the user.

Evaluate the answer on these criteria and respond with ONLY a valid JSON object:

1. **Answer Completeness** (0.0-1.0): Does the answer fully address the question? Are all aspects covered?
2. **Evidence Coverage** (0.0-1.0): What percentage of claims in the answer are backed by the retrieved code context?
3. **Citation Accuracy** (true/false): Do file paths mentioned in the answer exist in the retrieved results?
4. **Contradiction Detection** (true/false): Are there any conflicting statements in the answer?
5. **Overall Confidence** (0.0-1.0): Your overall assessment of answer quality.

Also identify:
- Any specific issues with the answer
- Files that should have been retrieved but weren't
- Refined search queries that could improve the answer (if confidence < 0.75)

Respond with this exact JSON structure:
{
    "passed": true/false,
    "confidence": 0.0-1.0,
    "answer_completeness": 0.0-1.0,
    "evidence_coverage_ratio": 0.0-1.0,
    "citation_accurate": true/false,
    "contradiction_detected": true/false,
    "issues": ["issue1", "issue2"],
    "missing_files": ["file1.py"],
    "missing_agents": [],
    "suggested_refinements": ["refined query 1"]
}
"""


class ReflectionAgent(BaseAgent):
    """
    Validates the final answer against the retrieved context.
    Can trigger re-retrieval cycles when quality is insufficient.
    """

    def __init__(self, llm: BaseLLM) -> None:
        self.llm = llm

    @property
    def name(self) -> str:
        return "reflection"

    async def execute(self, state: OrchestratorState) -> AgentOutput:
        query = state.get("query", "")
        answer = state.get("final_answer", "")
        retrieval_results = state.get("retrieval_results", [])
        plan = state.get("execution_plan")
        reflection_count = state.get("reflection_count", 0)

        if not answer:
            return AgentOutput(
                agent_name=self.name,
                result=ReflectionResult(
                    passed=False,
                    confidence=0.0,
                    issues=["No answer generated"],
                ),
                confidence=0.0,
                tools_used=[],
                reasoning_summary="No answer to validate",
            )

        # Build validation context
        retrieved_files = set()
        retrieved_entities = set()
        for r in retrieval_results[:20]:
            if isinstance(r, dict):
                meta = r.get("metadata", {})
                file_path = meta.get("file", "")
                if file_path:
                    retrieved_files.add(file_path)
                name = meta.get("name", "")
                if name:
                    retrieved_entities.add(name)

        # Build the LLM prompt
        context_summary = (
            f"Retrieved {len(retrieval_results)} code chunks from "
            f"{len(retrieved_files)} unique files.\n"
            f"Files: {', '.join(list(retrieved_files)[:15])}\n"
            f"Entities: {', '.join(list(retrieved_entities)[:15])}"
        )

        plan_summary = ""
        if plan and isinstance(plan, dict):
            goals = plan.get("sub_goals", [])
            if goals:
                plan_summary = f"\nPlan sub-goals: {', '.join(goals[:5])}"

        user_prompt = (
            f"**User Question:** {query}\n\n"
            f"**Generated Answer (to validate):**\n{answer[:3000]}\n\n"
            f"**Retrieved Context Summary:**\n{context_summary}\n"
            f"{plan_summary}\n\n"
            f"**Reflection cycle:** {reflection_count + 1} of "
            f"{settings.agent_max_reflection_cycles + 1}\n\n"
            f"Validate this answer and respond with the JSON structure described."
        )

        messages = [
            {"role": "system", "content": REFLECTION_SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ]

        try:
            reflection = await self.llm.structured_output(
                messages=messages,
                output_schema=ReflectionResult,
                temperature=0.1,
                max_tokens=1024,
            )
        except Exception as e:
            logger.warning("Reflection LLM call failed", error=str(e))
            # Fallback: basic heuristic validation
            reflection = self._heuristic_validation(answer, retrieval_results, query)

        # Apply confidence threshold
        threshold = settings.agent_confidence_threshold
        if reflection.confidence >= threshold:
            reflection.passed = True

        logger.info(
            "Reflection completed",
            passed=reflection.passed,
            confidence=reflection.confidence,
            issues=len(reflection.issues),
            cycle=reflection_count + 1,
        )

        return AgentOutput(
            agent_name=self.name,
            result=reflection,
            confidence=reflection.confidence,
            tools_used=[],
            reasoning_summary=(
                f"Reflection {'PASSED' if reflection.passed else 'FAILED'} "
                f"(confidence: {reflection.confidence:.2f}, "
                f"issues: {len(reflection.issues)}, "
                f"evidence: {reflection.evidence_coverage_ratio:.0%})"
            ),
        )

    def _heuristic_validation(
        self,
        answer: str,
        retrieval_results: List[Dict[str, Any]],
        query: str,
    ) -> ReflectionResult:
        """
        Fallback heuristic validation when LLM reflection fails.
        Uses simple checks to estimate quality.
        """
        issues = []
        confidence = 0.5

        # Check answer length
        if len(answer) < 100:
            issues.append("Answer is very short — may be incomplete")
            confidence -= 0.15
        elif len(answer) > 500:
            confidence += 0.1

        # Check if answer contains file references
        retrieved_files = set()
        for r in retrieval_results[:20]:
            if isinstance(r, dict):
                meta = r.get("metadata", {})
                f = meta.get("file", "")
                if f:
                    retrieved_files.add(f)

        file_refs_in_answer = sum(1 for f in retrieved_files if f in answer)
        if file_refs_in_answer > 0:
            confidence += 0.1
            evidence_ratio = min(file_refs_in_answer / max(len(retrieved_files), 1), 1.0)
        else:
            issues.append("Answer does not reference specific files from retrieved context")
            evidence_ratio = 0.0

        # Check if answer contains code blocks
        if "```" in answer:
            confidence += 0.05

        # Check if answer addresses key terms from query
        query_words = set(query.lower().split())
        answer_words = set(answer.lower().split())
        overlap = query_words & answer_words
        if len(overlap) < len(query_words) * 0.3:
            issues.append("Answer may not fully address the question")
            confidence -= 0.1

        # Check retrieval quality
        if not retrieval_results:
            issues.append("No retrieval results available")
            confidence -= 0.2
        elif len(retrieval_results) < 5:
            issues.append("Limited retrieval results")
            confidence -= 0.1

        # Check for common error patterns
        error_phrases = [
            "i couldn't find", "i don't have", "no information",
            "not available", "error:", "failed",
        ]
        if any(phrase in answer.lower() for phrase in error_phrases):
            issues.append("Answer indicates potential retrieval failure")
            confidence -= 0.15

        confidence = max(0.1, min(1.0, confidence))
        passed = confidence >= settings.agent_confidence_threshold

        return ReflectionResult(
            passed=passed,
            confidence=confidence,
            issues=issues,
            missing_files=[],
            missing_agents=[],
            suggested_refinements=None if passed else [query],
            contradiction_detected=False,
            evidence_coverage_ratio=evidence_ratio,
        )

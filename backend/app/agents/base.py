"""
DevDocsAI V2 — Base Agent Abstract Class
==========================================
Every agent in the system extends BaseAgent and implements the
`execute()` method. This class provides:
  - Standardized timing & error handling
  - Automatic AgentOutput envelope wrapping
  - Tool registration interface
  - Confidence scoring helpers

References:
    docs/README_V2_ARCHITECTURE.md §4 (Standardized Agent Contract)
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

from langchain_core.tools import BaseTool

from app.agents.schemas import AgentOutput, OrchestratorState
from app.core.logging import get_logger

logger = get_logger(__name__)


class BaseAgent(ABC):
    """
    Abstract base class for all V2 agents.

    Subclasses must implement:
        - `execute(state)` → produces an AgentOutput
        - `get_tools()` → returns list of LangChain tools this agent can use

    The `run()` method wraps `execute()` with timing and error handling.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Unique identifier for this agent (e.g. 'planning', 'retrieval')."""
        ...

    @abstractmethod
    async def execute(self, state: OrchestratorState) -> AgentOutput:
        """
        Core agent logic. Reads from shared state, invokes tools,
        produces a typed AgentOutput with confidence scoring.
        """
        ...

    def get_tools(self) -> List[BaseTool]:
        """Return the LangChain tools this agent can invoke. Override in subclasses."""
        return []

    # ── Public runner with timing + error handling ───────────────────────────

    async def run(self, state: OrchestratorState) -> AgentOutput:
        """
        Execute the agent with automatic timing and error recovery.

        Returns:
            AgentOutput with duration_ms populated and error field
            set on failure (graceful degradation).
        """
        start = time.perf_counter()
        try:
            logger.info(
                "Agent started",
                agent=self.name,
                repo_id=state.get("repo_id", ""),
            )
            output = await self.execute(state)
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            output.duration_ms = elapsed_ms
            output.agent_name = self.name
            logger.info(
                "Agent completed",
                agent=self.name,
                confidence=output.confidence,
                duration_ms=elapsed_ms,
                tools_used=output.tools_used,
            )
            return output

        except Exception as exc:
            elapsed_ms = int((time.perf_counter() - start) * 1000)
            logger.error(
                "Agent failed",
                agent=self.name,
                error=str(exc),
                duration_ms=elapsed_ms,
                exc_info=True,
            )
            return AgentOutput(
                agent_name=self.name,
                result=None,
                confidence=0.0,
                tools_used=[],
                duration_ms=elapsed_ms,
                reasoning_summary=f"Agent {self.name} failed: {str(exc)[:200]}",
                error=str(exc)[:500],
            )

    # ── Helpers ──────────────────────────────────────────────────────────────

    @staticmethod
    def clamp_confidence(value: float) -> float:
        """Clamp a confidence score to [0.0, 1.0]."""
        return max(0.0, min(1.0, value))

    @staticmethod
    def calculate_final_confidence(agent_confidences: Dict[str, float]) -> float:
        """
        Weighted average confidence across all invoked agents.
        Reflection Agent has the highest individual weight.

        Weights:
            planning=0.10, repository=0.10, retrieval=0.30,
            architecture=0.15, code_analysis=0.10, reflection=0.25
        """
        weights = {
            "planning": 0.10,
            "repository": 0.10,
            "retrieval": 0.30,
            "architecture": 0.15,
            "code_analysis": 0.10,
            "documentation": 0.10,
            "reflection": 0.25,
        }
        active = {k: v for k, v in agent_confidences.items() if k in weights}
        if not active:
            return 0.5

        total_weight = sum(weights[k] for k in active)
        if total_weight == 0:
            return 0.5
        return sum(weights[k] * v for k, v in active.items()) / total_weight

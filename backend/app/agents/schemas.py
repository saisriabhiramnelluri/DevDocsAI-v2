"""
DevDocsAI V2 — Agent Schemas & Contracts
==========================================
Pydantic models defining the standardized contract every agent follows.
These schemas ensure agents are independently testable, observable,
and produce typed outputs with confidence scoring.

References:
    docs/README_V2_ARCHITECTURE.md §4 (Standardized Agent Contract)
    docs/README_V2_ARCHITECTURE.md §5 (Agent Specifications)
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, TypedDict

from pydantic import BaseModel, Field


# ── Agent Output Envelope ────────────────────────────────────────────────────

class AgentOutput(BaseModel):
    """Standard envelope returned by every agent execution."""

    agent_name: str = Field(..., description="Identifier of the agent that produced this output")
    result: Any = Field(default=None, description="Agent-specific typed output")
    confidence: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Confidence score (0.0 = no confidence, 1.0 = fully confident)",
    )
    tools_used: List[str] = Field(default_factory=list, description="Names of tools invoked")
    duration_ms: int = Field(default=0, description="Execution time in milliseconds")
    reasoning_summary: str = Field(
        default="", description="One-line summary of what the agent did"
    )
    error: Optional[str] = Field(default=None, description="Non-fatal error description")


# ── Reasoning Trace ──────────────────────────────────────────────────────────

class AgentStep(BaseModel):
    """One step in the reasoning trace returned to the frontend."""

    agent_name: str
    action: str = Field(..., description='e.g. "decomposed query into 4 steps"')
    tools_invoked: List[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    duration_ms: int = 0
    output_summary: str = ""


class ReasoningTrace(BaseModel):
    """Full execution trace attached to every V2 response."""

    steps: List[AgentStep] = Field(default_factory=list)
    total_duration_ms: int = 0
    total_tokens_used: int = 0
    agents_invoked: List[str] = Field(default_factory=list)
    reflection_cycles: int = 0
    final_confidence: float = Field(default=0.5, ge=0.0, le=1.0)


# ── Planning Agent Models ────────────────────────────────────────────────────

class PlanStep(BaseModel):
    """One step in an execution plan produced by the Planning Agent."""

    step_id: int
    description: str = Field(..., description="Human-readable step description")
    retrieval_query: str = Field(..., description="Optimized search query for this step")
    target_entities: List[str] = Field(
        default_factory=list, description='e.g. ["auth routes", "JWT middleware"]'
    )
    expected_files: Optional[List[str]] = Field(
        default=None, description="Hints for targeted retrieval"
    )
    priority: str = Field(
        default="important",
        description='"critical" | "important" | "supplementary"',
    )
    required_tools: List[str] = Field(
        default_factory=lambda: ["semantic_search"],
        description="Tools needed for this step",
    )


class ExecutionPlan(BaseModel):
    """Full execution plan produced by the Planning Agent."""

    goal: str = Field(..., description="High-level objective")
    sub_goals: List[str] = Field(default_factory=list, description="Decomposed sub-objectives")
    steps: List[PlanStep] = Field(default_factory=list, description="Ordered execution steps")
    estimated_complexity: str = Field(
        default="moderate",
        description='"simple" | "moderate" | "complex"',
    )
    estimated_retrieval_cost: int = Field(
        default=1, description="Estimated number of retrieval calls"
    )
    estimated_token_usage: int = Field(default=0, description="Rough token budget estimate")
    requires_architecture: bool = Field(
        default=False, description="Should Architecture Agent be invoked?"
    )
    requires_code_analysis: bool = Field(
        default=False, description="Should Code Analysis Agent be invoked?"
    )
    required_agents: List[str] = Field(
        default_factory=list, description="Explicit list of agents needed"
    )


# ── Repository Agent Models ──────────────────────────────────────────────────

class RepoContext(BaseModel):
    """Repository metadata context produced by the Repository Agent."""

    primary_language: str = ""
    languages: Dict[str, int] = Field(default_factory=dict)
    framework: Optional[str] = None
    architecture_type: Optional[str] = None
    project_type: str = Field(
        default="unknown",
        description='"api_server" | "web_app" | "library" | "cli" | "unknown"',
    )
    total_files: int = 0
    total_functions: int = 0
    total_classes: int = 0
    total_lines: int = 0
    summary: str = ""
    key_directories: List[str] = Field(default_factory=list)
    entry_points: List[str] = Field(default_factory=list)


# ── Reflection Agent Models ──────────────────────────────────────────────────

class ReflectionResult(BaseModel):
    """Result of the Reflection Agent validation pipeline."""

    passed: bool = Field(default=False, description="Overall pass/fail")
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)
    issues: List[str] = Field(default_factory=list, description="Specific problems found")
    missing_files: List[str] = Field(
        default_factory=list, description="Files that should have been retrieved"
    )
    missing_agents: List[str] = Field(
        default_factory=list, description="Agents that should have been invoked"
    )
    suggested_refinements: Optional[List[str]] = Field(
        default=None, description="Refined queries for re-retrieval"
    )
    contradiction_detected: bool = Field(
        default=False, description="Whether conflicting info was found"
    )
    evidence_coverage_ratio: float = Field(
        default=0.0, ge=0.0, le=1.0, description="% of claims backed by evidence"
    )


# ── Source Reference ─────────────────────────────────────────────────────────

class SourceRef(BaseModel):
    """File/line source reference attached to agent responses."""

    file: str
    function: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    content_preview: Optional[str] = None
    score: float = 0.0


# ── Orchestrator State (LangGraph TypedDict) ─────────────────────────────────

class OrchestratorState(TypedDict, total=False):
    """
    LangGraph state passed between orchestrator nodes.
    TypedDict is required by LangGraph's StateGraph.
    """

    # ── Inputs ──
    query: str
    repo_id: str
    conversation_history: List[Dict[str, str]]
    mode: str  # "auto" | "v2" | "v1"

    # ── Query classification ──
    query_type: str  # "simple" | "general_code" | "architecture" | "documentation" | "code_review" | "complex_multi_hop"

    # ── Agent outputs ──
    repo_context: Optional[Dict[str, Any]]
    execution_plan: Optional[Dict[str, Any]]
    retrieval_results: List[Dict[str, Any]]
    architecture_context: Optional[str]
    documentation_output: Optional[str]
    code_analysis_output: Optional[str]

    # ── Confidence tracking ──
    agent_confidences: Dict[str, float]

    # ── Reflection ──
    reflection_result: Optional[Dict[str, Any]]
    reflection_count: int

    # ── Output ──
    final_answer: str
    sources: List[Dict[str, Any]]
    reasoning_trace: Dict[str, Any]

    # ── Error tracking ──
    error: Optional[str]

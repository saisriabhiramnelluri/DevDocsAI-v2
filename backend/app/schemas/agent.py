"""
DevDocsAI V2 — Agent API Schemas
===================================
Request/response models for the V2 agent chat API.
These are separate from the V1 chat schemas to avoid breaking changes.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Request Schemas ──────────────────────────────────────────────────────────

class AgentChatRequest(BaseModel):
    """Request body for agent-powered chat queries."""

    repo_id: str = Field(..., description="Repository identifier")
    session_id: str = Field(..., description="Chat session identifier")
    question: str = Field(..., description="User's question about the repository")
    mode: str = Field(
        default="auto",
        description='Agent mode: "auto" (select based on complexity), "v2" (force multi-agent), "v1" (force V1 fast path)',
    )


# ── Response Schemas ─────────────────────────────────────────────────────────

class AgentStepOut(BaseModel):
    """One step in the reasoning trace displayed to the user."""

    agent_name: str
    action: str
    tools_invoked: List[str] = []
    confidence: float = 0.5
    duration_ms: int = 0
    output_summary: str = ""


class ReasoningTraceOut(BaseModel):
    """Full reasoning trace returned with every V2 response."""

    steps: List[AgentStepOut] = []
    total_duration_ms: int = 0
    total_tokens_used: int = 0
    agents_invoked: List[str] = []
    reflection_cycles: int = 0
    final_confidence: float = 0.5


class AgentSourceReference(BaseModel):
    """Source file reference from agent retrieval."""

    file: str
    function: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    content_preview: Optional[str] = None
    score: float = 0.0


class AgentChatResponse(BaseModel):
    """Response from the agent-powered chat pipeline."""

    answer: str = Field(..., description="AI-generated answer")
    session_id: str
    message_id: str
    sources: List[AgentSourceReference] = Field(
        default_factory=list, description="Source file references"
    )
    reasoning_trace: ReasoningTraceOut = Field(
        default_factory=ReasoningTraceOut,
        description="Full agent reasoning trace",
    )
    confidence: float = Field(
        default=0.5, ge=0.0, le=1.0, description="Final confidence score"
    )
    agents_invoked: List[str] = Field(
        default_factory=list, description="Names of agents that were invoked"
    )
    query_type: str = Field(
        default="unknown", description="Classified query type"
    )
    model: str = Field(default="", description="LLM model used")
    mode: str = Field(default="auto", description="Agent mode that was used")
    error: Optional[str] = Field(
        default=None, description="Error message if pipeline partially failed"
    )


# ── SSE Event Schemas ────────────────────────────────────────────────────────

class AgentStatusEvent(BaseModel):
    """Server-Sent Event for real-time agent status updates."""

    type: str = Field(
        ...,
        description=(
            'Event type: "agent_start", "agent_complete", "token", "done", "error"'
        ),
    )
    agent_name: Optional[str] = None
    content: Optional[str] = None
    confidence: Optional[float] = None
    duration_ms: Optional[int] = None
    step_index: Optional[int] = None
    total_steps: Optional[int] = None
    # Full response data (only in "done" events)
    sources: Optional[List[Dict[str, Any]]] = None
    reasoning_trace: Optional[Dict[str, Any]] = None

"""
DevDocsAI — Pydantic Schemas (Chat + Documentation + Architecture)
"""
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel


# ── Chat ─────────────────────────────────────────────────────────────────────

class ChatSessionCreateRequest(BaseModel):
    repo_id: str


class ChatSessionOut(BaseModel):
    id: str
    repo_id: str
    title: Optional[str] = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatQueryRequest(BaseModel):
    repo_id: str
    session_id: str
    question: str


class SourceReference(BaseModel):
    file: str
    function: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None
    content_preview: Optional[str] = None
    score: float = 0.0


class ChatQueryResponse(BaseModel):
    answer: str
    session_id: str
    message_id: str
    sources: List[SourceReference] = []
    graph_context: List[Dict[str, Any]] = []
    intent: Optional[str] = None
    model: str = "deepseek-chat"


class MessageOut(BaseModel):
    id: str
    session_id: str
    role: str
    content: str
    sources: Optional[str] = None
    timestamp: datetime

    model_config = {"from_attributes": True}


class ChatHistoryOut(BaseModel):
    session_id: str
    messages: List[MessageOut]


# ── Documentation ─────────────────────────────────────────────────────────────

class DocumentationOut(BaseModel):
    repo_id: str
    doc_type: str  # readme | api | onboarding
    content: str
    generated_at: Optional[datetime] = None


# ── Architecture ──────────────────────────────────────────────────────────────

class ArchitectureComponentOut(BaseModel):
    name: str
    type: str  # service | module | database | api
    description: Optional[str] = None
    dependencies: List[str] = []


class ArchitectureSummaryOut(BaseModel):
    repo_id: str
    summary: str
    components: List[ArchitectureComponentOut] = []
    framework: Optional[str] = None
    architecture_type: Optional[str] = None


class DependencyGraphOut(BaseModel):
    repo_id: str
    mermaid: str
    nodes: List[Dict[str, Any]] = []
    edges: List[Dict[str, Any]] = []

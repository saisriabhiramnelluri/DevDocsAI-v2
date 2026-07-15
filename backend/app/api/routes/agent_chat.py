"""
DevDocsAI V2 — Agent Chat Routes
===================================
New API endpoints for the V2 multi-agent chat pipeline.
These run alongside the existing V1 /chat routes — no breaking changes.

Endpoints:
    POST /agent/chat/query   — Full agent pipeline query
    POST /agent/chat/stream  — SSE streaming with agent status events
    GET  /agent/chat/modes   — Available agent modes info
"""

import json
import time
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Header, status
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.db import get_db
from app.core.config import settings
from app.core.logging import get_logger
from app.repositories.chat_repository import ChatRepository
from app.repositories.repo_repository import RepositoryRepository
from app.schemas.agent import (
    AgentChatRequest,
    AgentChatResponse,
    AgentSourceReference,
    AgentStepOut,
    ReasoningTraceOut,
)

router = APIRouter()
logger = get_logger(__name__)


@router.post(
    "/chat/query",
    response_model=AgentChatResponse,
    summary="Ask a question using the V2 multi-agent pipeline",
)
async def agent_chat_query(
    request: AgentChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Run the V2 multi-agent pipeline against a repository.

    The orchestrator classifies the query and dynamically selects
    which agents to invoke:
    - **simple** → V1 fast path (zero overhead)
    - **general_code** → Planning → Retrieval → Reflection
    - **architecture** → Planning → Repo + Retrieval + Architecture → Reflection
    - **documentation** → Planning → Repo + Retrieval → Documentation → Reflection
    - **code_review** → Planning → Retrieval → Code Analysis → Reflection
    - **complex_multi_hop** → All agents

    Returns the answer with full reasoning trace and confidence score.
    """
    # Validate session
    chat_repo = ChatRepository(db)
    session = await chat_repo.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    if session.repo_id != request.repo_id:
        raise HTTPException(
            status_code=400, detail="Session does not belong to this repository"
        )

    # Validate repository is ready
    repo_repo = RepositoryRepository(db)
    repo = await repo_repo.get_by_id(request.repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    if repo.status != "ready":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Repository is not ready. Current status: {repo.status}",
        )

    # Save user message
    await chat_repo.add_message(
        session_id=request.session_id,
        role="user",
        content=request.question,
    )

    # Get conversation history
    history = await chat_repo.get_history_for_llm(request.session_id, limit=8)
    history = history[:-1]  # Exclude the message we just added

    # Run agent pipeline
    from app.agents.orchestrator import run_agent_pipeline

    result = await run_agent_pipeline(
        repo_id=request.repo_id,
        query=request.question,
        conversation_history=history,
        mode=request.mode,
    )

    answer = result.get("answer", "")
    sources_raw = result.get("sources", [])
    trace_raw = result.get("reasoning_trace", {})

    # Save assistant message
    assistant_msg = await chat_repo.add_message(
        session_id=request.session_id,
        role="assistant",
        content=answer,
        sources=sources_raw,
    )

    # Build typed response
    sources = [
        AgentSourceReference(
            file=s.get("file", ""),
            function=s.get("function"),
            line_start=s.get("line_start"),
            line_end=s.get("line_end"),
            content_preview=s.get("content_preview"),
            score=s.get("score", 0.0),
        )
        for s in sources_raw
        if isinstance(s, dict)
    ]

    # Parse reasoning trace
    steps = []
    if isinstance(trace_raw, dict):
        for step_data in trace_raw.get("steps", []):
            if isinstance(step_data, dict):
                steps.append(
                    AgentStepOut(
                        agent_name=step_data.get("agent_name", "unknown"),
                        action=step_data.get("action", ""),
                        tools_invoked=step_data.get("tools_invoked", []),
                        confidence=step_data.get("confidence", 0.5),
                        duration_ms=step_data.get("duration_ms", 0),
                        output_summary=step_data.get("output_summary", ""),
                    )
                )

    reasoning_trace = ReasoningTraceOut(
        steps=steps,
        total_duration_ms=trace_raw.get("total_duration_ms", 0) if isinstance(trace_raw, dict) else 0,
        total_tokens_used=trace_raw.get("total_tokens_used", 0) if isinstance(trace_raw, dict) else 0,
        agents_invoked=trace_raw.get("agents_invoked", []) if isinstance(trace_raw, dict) else [],
        reflection_cycles=trace_raw.get("reflection_cycles", 0) if isinstance(trace_raw, dict) else 0,
        final_confidence=trace_raw.get("final_confidence", 0.5) if isinstance(trace_raw, dict) else 0.5,
    )

    logger.info(
        "Agent chat query completed",
        session_id=request.session_id,
        query_type=result.get("query_type", "unknown"),
        agents=result.get("agents_invoked", []),
        confidence=result.get("confidence", 0),
    )

    return AgentChatResponse(
        answer=answer,
        session_id=request.session_id,
        message_id=assistant_msg.id,
        sources=sources,
        reasoning_trace=reasoning_trace,
        confidence=result.get("confidence", 0.5),
        agents_invoked=result.get("agents_invoked", []),
        query_type=result.get("query_type", "unknown"),
        model=settings.llm_model,
        mode=request.mode,
        error=result.get("error"),
    )


@router.post(
    "/chat/stream",
    summary="Stream an agent chat response via Server-Sent Events",
)
async def agent_chat_stream(
    request: AgentChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Streams the V2 agent pipeline response as SSE events.

    Events emitted:
    - `{"type": "agent_start", "agent_name": "planning", ...}` — Agent begins
    - `{"type": "agent_complete", "agent_name": "planning", "confidence": 0.9, ...}` — Agent done
    - `{"type": "token", "content": "..."}` — Answer token
    - `{"type": "done", "sources": [...], "reasoning_trace": {...}}` — Final metadata
    - `{"type": "error", "content": "..."}` — Error
    """
    # Validate session
    chat_repo = ChatRepository(db)
    session = await chat_repo.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    if session.repo_id != request.repo_id:
        raise HTTPException(
            status_code=400, detail="Session does not belong to this repository"
        )

    # Validate repository
    repo_repo = RepositoryRepository(db)
    repo = await repo_repo.get_by_id(request.repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    if repo.status != "ready":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Repository is not ready. Current status: {repo.status}",
        )

    # Save user message
    await chat_repo.add_message(
        session_id=request.session_id,
        role="user",
        content=request.question,
    )

    # Get conversation history
    history = await chat_repo.get_history_for_llm(request.session_id, limit=8)
    history = history[:-1]

    async def generate():
        """SSE generator — runs the pipeline and streams events."""
        start_time = time.perf_counter()

        # Emit pipeline start
        yield _sse({"type": "agent_start", "agent_name": "orchestrator", "content": "Starting agent pipeline..."})

        try:
            from app.agents.orchestrator import run_agent_pipeline

            result = await run_agent_pipeline(
                repo_id=request.repo_id,
                query=request.question,
                conversation_history=history,
                mode=request.mode,
            )

            answer = result.get("answer", "")
            sources = result.get("sources", [])
            trace = result.get("reasoning_trace", {})

            # Emit agent steps as status events
            if isinstance(trace, dict):
                for i, step in enumerate(trace.get("steps", [])):
                    if isinstance(step, dict):
                        yield _sse({
                            "type": "agent_complete",
                            "agent_name": step.get("agent_name", ""),
                            "confidence": step.get("confidence", 0.5),
                            "duration_ms": step.get("duration_ms", 0),
                            "content": step.get("output_summary", ""),
                            "step_index": i + 1,
                        })

            # Stream the answer token-by-token (simulate chunking for smooth UX)
            chunk_size = 12  # characters per chunk
            for i in range(0, len(answer), chunk_size):
                chunk = answer[i : i + chunk_size]
                yield _sse({"type": "token", "content": chunk})

            # Emit final done event
            total_ms = int((time.perf_counter() - start_time) * 1000)
            yield _sse({
                "type": "done",
                "sources": sources,
                "reasoning_trace": trace,
                "confidence": result.get("confidence", 0.5),
                "agents_invoked": result.get("agents_invoked", []),
                "query_type": result.get("query_type", "unknown"),
                "duration_ms": total_ms,
            })

            # Persist assistant message
            from app.database.session import AsyncSessionLocal
            from app.repositories.chat_repository import ChatRepository as CR

            async with AsyncSessionLocal() as save_db:
                save_repo = CR(save_db)
                if answer:
                    await save_repo.add_message(
                        session_id=request.session_id,
                        role="assistant",
                        content=answer,
                        sources=sources,
                    )

        except Exception as e:
            logger.error("Agent stream failed", error=str(e), exc_info=True)
            yield _sse({"type": "error", "content": f"Agent pipeline error: {str(e)}"})

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.get(
    "/chat/modes",
    summary="Get available agent modes and their descriptions",
)
async def get_agent_modes():
    """Return info about the available agent modes."""
    return {
        "modes": [
            {
                "id": "auto",
                "name": "Auto",
                "description": (
                    "Automatically selects V1 fast path for simple queries "
                    "and V2 multi-agent pipeline for complex queries."
                ),
                "default": True,
            },
            {
                "id": "v2",
                "name": "Multi-Agent (V2)",
                "description": (
                    "Forces the full multi-agent pipeline with planning, "
                    "retrieval, and reflection — even for simple queries."
                ),
                "default": False,
            },
            {
                "id": "v1",
                "name": "Fast (V1)",
                "description": (
                    "Forces the V1 Hybrid RAG pipeline. Fastest response time, "
                    "no agent overhead."
                ),
                "default": False,
            },
        ],
        "current_mode": settings.agent_mode,
        "confidence_threshold": settings.agent_confidence_threshold,
        "max_reflection_cycles": settings.agent_max_reflection_cycles,
    }


def _sse(data: dict) -> str:
    """Format a dict as an SSE event string."""
    return f"data: {json.dumps(data)}\n\n"

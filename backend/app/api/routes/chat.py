"""
DevDocsAI — Chat Routes
POST /chat/sessions
POST /chat/query
POST /chat/stream
GET  /chat/history/{session_id}
GET  /chat/sessions/repo/{repo_id}
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.db import get_db
from app.core.logging import get_logger
from app.repositories.chat_repository import ChatRepository
from app.repositories.repo_repository import RepositoryRepository
from app.schemas.chat import (
    ChatHistoryOut,
    ChatQueryRequest,
    ChatQueryResponse,
    ChatSessionCreateRequest,
    ChatSessionOut,
    MessageOut,
    SourceReference,
)
from app.services.chat.chat_service import ChatService

router = APIRouter()
logger = get_logger(__name__)
chat_service = ChatService()


@router.post(
    "/sessions",
    response_model=ChatSessionOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new chat session for a repository",
)
async def create_chat_session(
    request: ChatSessionCreateRequest,
    db: AsyncSession = Depends(get_db),
    x_client_id: str | None = Header(None, alias="X-Client-Id"),
):
    """Create a new chat session tied to a repository."""
    repo_repo = RepositoryRepository(db)
    repo = await repo_repo.get_by_id(request.repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    if repo.status != "ready":
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Repository is not ready. Current status: {repo.status}",
        )

    chat_repo = ChatRepository(db)
    session = await chat_repo.create_session(repo_id=request.repo_id, user_id=x_client_id)
    return ChatSessionOut(
        id=session.id,
        repo_id=session.repo_id,
        title=session.title,
        created_at=session.created_at,
    )


@router.post(
    "/query",
    response_model=ChatQueryResponse,
    summary="Ask a question about the repository",
)
async def chat_query(
    request: ChatQueryRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Run a RAG query against the repository knowledge base.
    Returns an AI-generated answer with source references.
    """
    # Validate session exists
    chat_repo = ChatRepository(db)
    session = await chat_repo.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    if session.repo_id != request.repo_id:
        raise HTTPException(status_code=400, detail="Session does not belong to this repository")

    # Save user message
    user_msg = await chat_repo.add_message(
        session_id=request.session_id,
        role="user",
        content=request.question,
    )

    # Get conversation history for context continuity
    history = await chat_repo.get_history_for_llm(request.session_id, limit=8)
    # Remove the last user message (we'll add it in the prompt)
    history = history[:-1]

    # Run chat
    result = await chat_service.chat(
        repo_id=request.repo_id,
        question=request.question,
        conversation_history=history,
    )

    # Save assistant message
    assistant_msg = await chat_repo.add_message(
        session_id=request.session_id,
        role="assistant",
        content=result["answer"],
        sources=result.get("sources", []),
    )

    sources = [
        SourceReference(
            file=s.get("file", ""),
            function=s.get("function"),
            line_start=s.get("line_start"),
            line_end=s.get("line_end"),
            content_preview=s.get("content_preview"),
            score=s.get("score", 0.0),
        )
        for s in result.get("sources", [])
    ]

    logger.info("Chat query completed", session_id=request.session_id)
    return ChatQueryResponse(
        answer=result["answer"],
        session_id=request.session_id,
        message_id=assistant_msg.id,
        sources=sources,
        graph_context=result.get("graph_context", []),
        intent=result.get("intent"),
        model=result.get("model", "deepseek-chat"),
    )


@router.post(
    "/stream",
    summary="Stream a chat response via Server-Sent Events",
)
async def chat_stream_endpoint(
    request: ChatQueryRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Streams LLM response tokens as SSE events.
    Events: {"type":"token","content":"..."} | {"type":"done",...} | {"type":"error",...}
    """
    chat_repo = ChatRepository(db)
    session = await chat_repo.get_session(request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")
    if session.repo_id != request.repo_id:
        raise HTTPException(status_code=400, detail="Session does not belong to this repository")

    # Save user message immediately
    await chat_repo.add_message(
        session_id=request.session_id,
        role="user",
        content=request.question,
    )

    # Get conversation history (exclude the message we just added)
    history = await chat_repo.get_history_for_llm(request.session_id, limit=8)
    history = history[:-1]

    # Collect full response for persistence after streaming
    collected_tokens: list[str] = []
    collected_sources: list = []

    async def generate():
        nonlocal collected_sources
        async for event_json in chat_service.chat_stream(
            repo_id=request.repo_id,
            question=request.question,
            conversation_history=history,
        ):
            import json as _json
            try:
                data = _json.loads(event_json)
                if data.get("type") == "token":
                    collected_tokens.append(data.get("content", ""))
                elif data.get("type") == "done":
                    collected_sources = data.get("sources", [])
            except Exception:
                pass
            yield f"data: {event_json}\n\n"

        # After streaming finishes, persist the assistant message in a new session
        from app.database.session import AsyncSessionLocal
        from app.repositories.chat_repository import ChatRepository as CR
        async with AsyncSessionLocal() as save_db:
            save_repo = CR(save_db)
            full_answer = "".join(collected_tokens)
            if full_answer:
                await save_repo.add_message(
                    session_id=request.session_id,
                    role="assistant",
                    content=full_answer,
                    sources=collected_sources,
                )

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
    "/history/{session_id}",
    response_model=ChatHistoryOut,
    summary="Get chat history for a session",
)
async def get_chat_history(
    session_id: str,
    db: AsyncSession = Depends(get_db),
):
    chat_repo = ChatRepository(db)
    session = await chat_repo.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Chat session not found")

    messages = await chat_repo.get_history(session_id)
    return ChatHistoryOut(
        session_id=session_id,
        messages=[
            MessageOut(
                id=m.id,
                session_id=m.session_id,
                role=m.role,
                content=m.content,
                sources=m.sources,
                timestamp=m.timestamp,
            )
            for m in messages
        ],
    )


@router.get(
    "/sessions/repo/{repo_id}",
    response_model=list[ChatSessionOut],
    summary="List chat sessions for a repository",
)
async def list_sessions_by_repo(
    repo_id: str,
    db: AsyncSession = Depends(get_db),
    limit: int = 10,
    x_client_id: str | None = Header(None, alias="X-Client-Id"),
):
    """Return recent chat sessions for a given repository, newest first."""
    chat_repo = ChatRepository(db)
    sessions = await chat_repo.list_sessions_by_repo(repo_id=repo_id, limit=limit, user_id=x_client_id)
    return [
        ChatSessionOut(id=s.id, repo_id=s.repo_id, title=s.title, created_at=s.created_at)
        for s in sessions
    ]


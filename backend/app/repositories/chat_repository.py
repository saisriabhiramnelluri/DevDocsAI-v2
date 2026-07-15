"""
DevDocsAI — Chat Data Access Layer
"""
import json
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import ChatSession, Message


class ChatRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_session(self, repo_id: str, user_id: Optional[str] = None) -> ChatSession:
        session = ChatSession(repo_id=repo_id, user_id=user_id)
        self.db.add(session)
        await self.db.commit()
        await self.db.refresh(session)
        return session

    async def get_session(self, session_id: str) -> Optional[ChatSession]:
        result = await self.db.execute(
            select(ChatSession).where(ChatSession.id == session_id)
        )
        return result.scalar_one_or_none()

    async def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        sources: Optional[List] = None,
    ) -> Message:
        msg = Message(
            session_id=session_id,
            role=role,
            content=content,
            sources=json.dumps(sources) if sources else None,
        )
        self.db.add(msg)
        await self.db.commit()
        await self.db.refresh(msg)
        return msg

    async def get_history(self, session_id: str) -> List[Message]:
        result = await self.db.execute(
            select(Message)
            .where(Message.session_id == session_id)
            .order_by(Message.timestamp.asc())
        )
        return list(result.scalars().all())

    async def get_history_for_llm(self, session_id: str, limit: int = 10) -> List[dict]:
        """Return last N messages as LLM-compatible dicts."""
        messages = await self.get_history(session_id)
        recent = messages[-limit:]
        return [{"role": m.role, "content": m.content} for m in recent]

    async def list_sessions_by_repo(self, repo_id: str, limit: int = 10, user_id: Optional[str] = None) -> List[ChatSession]:
        """List recent chat sessions for a repository."""
        stmt = select(ChatSession).where(ChatSession.repo_id == repo_id)
        if user_id:
            stmt = stmt.where(ChatSession.user_id == user_id)
            
        result = await self.db.execute(
            stmt.order_by(ChatSession.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())


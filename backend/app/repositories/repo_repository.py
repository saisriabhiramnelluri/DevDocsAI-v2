"""
DevDocsAI — Repository Data Access Layer
"""
from typing import List, Optional

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Repository, RepositoryMetadata


class RepositoryRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create(self, repo_url: str, repo_name: str, owner: str, user_id: Optional[str] = None) -> Repository:
        repo = Repository(
            repo_url=repo_url,
            repo_name=repo_name,
            owner=owner,
            user_id=user_id,
            status="pending",
            progress=0,
        )
        self.db.add(repo)
        await self.db.commit()
        await self.db.refresh(repo)
        return repo

    async def get_by_id(self, repo_id: str) -> Optional[Repository]:
        result = await self.db.execute(
            select(Repository)
            .options(selectinload(Repository.metadata_))
            .where(Repository.id == repo_id)
        )
        return result.scalar_one_or_none()

    async def get_by_url(self, repo_url: str) -> Optional[Repository]:
        result = await self.db.execute(
            select(Repository).where(Repository.repo_url == repo_url)
        )
        return result.scalar_one_or_none()

    async def list_all(self, limit: int = 50, offset: int = 0) -> List[Repository]:
        result = await self.db.execute(
            select(Repository)
            .options(selectinload(Repository.metadata_))
            .order_by(Repository.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())

    async def update_status(
        self,
        repo_id: str,
        status: str,
        progress: int,
        current_stage: Optional[str] = None,
        error_message: Optional[str] = None,
    ) -> None:
        values = {"status": status, "progress": progress}
        if current_stage is not None:
            values["current_stage"] = current_stage
        if error_message is not None:
            values["error_message"] = error_message
        await self.db.execute(
            update(Repository).where(Repository.id == repo_id).values(**values)
        )
        await self.db.commit()

    async def delete(self, repo_id: str) -> bool:
        repo = await self.get_by_id(repo_id)
        if not repo:
            return False
        await self.db.delete(repo)
        await self.db.commit()
        return True

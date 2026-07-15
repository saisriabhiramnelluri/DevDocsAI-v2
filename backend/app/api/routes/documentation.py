"""
DevDocsAI — Documentation Routes
GET /docs/{repo_id}/readme
GET /docs/{repo_id}/api
GET /docs/{repo_id}/onboarding
"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.db import get_db
from app.core.logging import get_logger
from app.repositories.repo_repository import RepositoryRepository
from app.schemas.chat import DocumentationOut
from app.services.chat.chat_service import ChatService

router = APIRouter()
logger = get_logger(__name__)
chat_service = ChatService()


async def _get_ready_repo(repo_id: str, db: AsyncSession):
    repo_repo = RepositoryRepository(db)
    repo = await repo_repo.get_by_id(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    if repo.status != "ready":
        raise HTTPException(status_code=409, detail=f"Repository not ready: {repo.status}")
    return repo


@router.get("/{repo_id}/readme", response_model=DocumentationOut)
async def get_readme(repo_id: str, db: AsyncSession = Depends(get_db)):
    """Generate a README for the repository."""
    repo = await _get_ready_repo(repo_id, db)

    # Use cached version if available
    if repo.metadata_ and repo.metadata_.readme_content:
        return DocumentationOut(repo_id=repo_id, doc_type="readme", content=repo.metadata_.readme_content)

    summary = repo.metadata_.summary if repo.metadata_ else ""
    content = await chat_service.generate_documentation(
        repo_id=repo_id, doc_type="readme", repo_summary=summary
    )

    # Cache it
    if repo.metadata_:
        from sqlalchemy import update
        from app.models import RepositoryMetadata
        from datetime import datetime, timezone
        await db.execute(
            update(RepositoryMetadata)
            .where(RepositoryMetadata.repo_id == repo_id)
            .values(readme_content=content)
        )
        await db.commit()

    return DocumentationOut(repo_id=repo_id, doc_type="readme", content=content)


@router.get("/{repo_id}/api", response_model=DocumentationOut)
async def get_api_docs(repo_id: str, db: AsyncSession = Depends(get_db)):
    """Generate API documentation for the repository."""
    repo = await _get_ready_repo(repo_id, db)
    if repo.metadata_ and repo.metadata_.api_doc_content:
        return DocumentationOut(repo_id=repo_id, doc_type="api", content=repo.metadata_.api_doc_content)

    summary = repo.metadata_.summary if repo.metadata_ else ""
    content = await chat_service.generate_documentation(
        repo_id=repo_id, doc_type="api", repo_summary=summary
    )
    return DocumentationOut(repo_id=repo_id, doc_type="api", content=content)


@router.get("/{repo_id}/onboarding", response_model=DocumentationOut)
async def get_onboarding(repo_id: str, db: AsyncSession = Depends(get_db)):
    """Generate developer onboarding documentation."""
    repo = await _get_ready_repo(repo_id, db)
    if repo.metadata_ and repo.metadata_.onboarding_content:
        return DocumentationOut(repo_id=repo_id, doc_type="onboarding", content=repo.metadata_.onboarding_content)

    summary = repo.metadata_.summary if repo.metadata_ else ""
    content = await chat_service.generate_documentation(
        repo_id=repo_id, doc_type="onboarding", repo_summary=summary
    )
    return DocumentationOut(repo_id=repo_id, doc_type="onboarding", content=content)

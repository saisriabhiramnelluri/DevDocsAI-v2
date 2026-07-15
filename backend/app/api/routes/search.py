"""
DevDocsAI — Search Routes
POST /search/query  — semantic code search across a repository
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.db import get_db
from app.core.logging import get_logger
from app.repositories.repo_repository import RepositoryRepository
from app.services.retrieval.hybrid_retriever import HybridRetriever

router = APIRouter()
logger = get_logger(__name__)
retriever = HybridRetriever()


class SearchRequest(BaseModel):
    repo_id: str
    query: str
    top_k: int = 10
    level_filter: Optional[str] = None  # function | class | file | repo


class SearchResultOut(BaseModel):
    chunk_id: str
    content: str
    file: str
    type: str
    name: Optional[str] = None
    score: float
    line_start: Optional[int] = None
    line_end: Optional[int] = None


class SearchResponse(BaseModel):
    results: list[SearchResultOut]
    total: int


@router.post("/query", response_model=SearchResponse, summary="Semantic code search")
async def search_query(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Run a semantic + keyword hybrid search over the repository's indexed codebase.
    Returns ranked results with file paths, types, and content previews.
    """
    repo_repo = RepositoryRepository(db)
    repo = await repo_repo.get_by_id(request.repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    if repo.status != "ready":
        raise HTTPException(status_code=409, detail=f"Repository not ready: {repo.status}")

    results = retriever.retrieve(
        repo_id=request.repo_id,
        query=request.query,
        top_k=request.top_k,
        level_filter=request.level_filter,
    )

    logger.info("Search query", repo_id=request.repo_id, query=request.query[:60], results=len(results))

    return SearchResponse(
        results=[
            SearchResultOut(
                chunk_id=r.chunk_id,
                content=r.content[:400],  # truncate for search results display
                file=r.metadata.get("file", ""),
                type=r.metadata.get("level", r.metadata.get("type", "unknown")),
                name=r.metadata.get("name"),
                score=round(r.score, 4),
                line_start=r.metadata.get("line_start"),
                line_end=r.metadata.get("line_end"),
            )
            for r in results
        ],
        total=len(results),
    )

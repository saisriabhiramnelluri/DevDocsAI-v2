"""
DevDocsAI — Repository Routes
POST /repositories/analyze
GET  /repositories/{id}
GET  /repositories/{id}/status
GET  /repositories/
DELETE /repositories/{id}
"""
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.db import get_db
from app.core.logging import get_logger
from app.repositories.repo_repository import RepositoryRepository
from app.schemas.repository import (
    RepositoryAnalyzeRequest,
    RepositoryAnalyzeResponse,
    RepositoryListOut,
    RepositoryOut,
    RepositoryStatusOut,
)
from app.services.github.validator import GitHubValidator

router = APIRouter()
logger = get_logger(__name__)
validator = GitHubValidator()


@router.post(
    "/analyze",
    response_model=RepositoryAnalyzeResponse,
    status_code=status.HTTP_202_ACCEPTED,
    summary="Submit a GitHub repository for analysis",
)
async def analyze_repository(
    request: RepositoryAnalyzeRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Accepts a GitHub URL, validates it, creates a DB record,
    and dispatches the analysis to Celery.
    Returns immediately with the repo_id and status: pending.
    """
    repo_url = request.repo_url
    repo_repo = RepositoryRepository(db)

    # Check if already analyzed
    existing = await repo_repo.get_by_url(repo_url)
    if existing and existing.status == "ready":
        logger.info("Repository already analyzed", repo_id=existing.id)
        return RepositoryAnalyzeResponse(
            repo_id=existing.id,
            status="ready",
            message="Repository already analyzed. You can start chatting.",
        )

    # Validate GitHub URL
    repo_info, error = await validator.validate_and_fetch_info(repo_url)
    if error:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=error)

    # Create DB record
    repo = await repo_repo.create(
        repo_url=repo_url,
        repo_name=repo_info.repo_name,
        owner=repo_info.owner,
    )

    # Dispatch to Celery
    try:
        from app.workers.analysis_tasks import analyze_repository as celery_task
        celery_task.apply_async(
            kwargs={
                "repo_id": repo.id,
                "repo_url": repo_url,
                "clone_url": repo_info.clone_url,
                "branch": repo_info.default_branch,
            },
            queue="analysis",
        )
    except Exception as e:
        logger.error("Failed to dispatch Celery task", error=str(e))
        # Fall back: start analysis in background thread (for environments without Redis)
        background_tasks.add_task(
            _run_analysis_sync,
            repo.id, repo_url, repo_info.clone_url, repo_info.default_branch
        )

    logger.info("Repository analysis queued", repo_id=repo.id, url=repo_url)
    return RepositoryAnalyzeResponse(
        repo_id=repo.id,
        status="pending",
        message="Repository analysis started. Poll /status for progress.",
    )


@router.get(
    "/",
    response_model=RepositoryListOut,
    summary="List all analyzed repositories",
)
async def list_repositories(
    db: AsyncSession = Depends(get_db),
    limit: int = 20,
    offset: int = 0,
):
    repo_repo = RepositoryRepository(db)
    repos = await repo_repo.list_all(limit=limit, offset=offset)
    return RepositoryListOut(repositories=repos, total=len(repos))


@router.get(
    "/{repo_id}",
    response_model=RepositoryOut,
    summary="Get repository details",
)
async def get_repository(
    repo_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo_repo = RepositoryRepository(db)
    repo = await repo_repo.get_by_id(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@router.get(
    "/{repo_id}/status",
    response_model=RepositoryStatusOut,
    summary="Get repository analysis status",
)
async def get_repository_status(
    repo_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo_repo = RepositoryRepository(db)
    repo = await repo_repo.get_by_id(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return RepositoryStatusOut(
        repo_id=repo.id,
        status=repo.status,
        progress=repo.progress,
        current_stage=repo.current_stage,
        error_message=repo.error_message,
    )


@router.delete(
    "/{repo_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a repository and its data",
)
async def delete_repository(
    repo_id: str,
    db: AsyncSession = Depends(get_db),
):
    repo_repo = RepositoryRepository(db)
    deleted = await repo_repo.delete(repo_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Repository not found")

    # Clean up ChromaDB and Graph
    try:
        from app.database.vector_store import delete_repo_collection
        from app.database.graph_store import delete_graph
        delete_repo_collection(repo_id)
        delete_graph(repo_id)
    except Exception as e:
        logger.warning("Cleanup error", repo_id=repo_id, error=str(e))


async def _run_analysis_sync(repo_id: str, repo_url: str, clone_url: str, branch: str) -> None:
    """Fallback: run analysis in background task (no Redis/Celery)."""
    import asyncio
    from app.workers.analysis_tasks import _run_analysis

    class FakeTask:
        pass

    try:
        await _run_analysis(FakeTask(), repo_id, repo_url, clone_url, branch)
    except Exception as e:
        logger.error("Background analysis failed", repo_id=repo_id, error=str(e))

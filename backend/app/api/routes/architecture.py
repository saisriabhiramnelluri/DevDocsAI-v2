"""
DevDocsAI — Architecture Routes
GET /architecture/{repo_id}/summary
GET /architecture/{repo_id}/graph
GET /architecture/{repo_id}/dependencies
"""
import json

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.db import get_db
from app.core.logging import get_logger
from app.repositories.repo_repository import RepositoryRepository
from app.schemas.chat import ArchitectureSummaryOut, DependencyGraphOut
from app.database.graph_store import load_graph, graph_to_dict, graph_to_mermaid

router = APIRouter()
logger = get_logger(__name__)


async def _get_ready_repo(repo_id: str, db: AsyncSession):
    repo_repo = RepositoryRepository(db)
    repo = await repo_repo.get_by_id(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    if repo.status != "ready":
        raise HTTPException(status_code=409, detail=f"Repository not ready: {repo.status}")
    return repo


@router.get("/{repo_id}/summary", response_model=ArchitectureSummaryOut)
async def get_architecture_summary(repo_id: str, db: AsyncSession = Depends(get_db)):
    """Get high-level architecture summary."""
    repo = await _get_ready_repo(repo_id, db)
    meta = repo.metadata_

    summary = meta.summary if meta else "No summary available."
    components = []

    if meta and meta.languages_detected:
        try:
            lang_counts = json.loads(meta.languages_detected)
            for lang, count in lang_counts.items():
                components.append({
                    "name": lang,
                    "type": "language",
                    "description": f"{count} files",
                    "dependencies": [],
                })
        except Exception:
            pass

    return ArchitectureSummaryOut(
        repo_id=repo_id,
        summary=summary,
        components=components,
        framework=meta.framework if meta else None,
        architecture_type=meta.architecture_type if meta else None,
    )


@router.get("/{repo_id}/graph", response_model=DependencyGraphOut)
async def get_architecture_graph(repo_id: str, db: AsyncSession = Depends(get_db)):
    """Get the Mermaid diagram and graph data."""
    repo = await _get_ready_repo(repo_id, db)
    meta = repo.metadata_

    # Use cached Mermaid diagram if available
    mermaid = meta.mermaid_diagram if meta and meta.mermaid_diagram else ""

    # Load full graph for nodes/edges
    graph = load_graph(repo_id)
    graph_data = graph_to_dict(graph) if graph else {"nodes": [], "edges": []}

    if not mermaid and graph:
        mermaid = graph_to_mermaid(graph, max_nodes=50)

    return DependencyGraphOut(
        repo_id=repo_id,
        mermaid=mermaid or "graph TD\n    A[No graph data available]",
        nodes=graph_data.get("nodes", [])[:100],
        edges=graph_data.get("edges", [])[:200],
    )


@router.get("/{repo_id}/dependencies")
async def get_dependencies(repo_id: str, db: AsyncSession = Depends(get_db)):
    """Get file-level dependency information."""
    repo = await _get_ready_repo(repo_id, db)
    graph = load_graph(repo_id)
    if not graph:
        return {"repo_id": repo_id, "dependencies": []}

    import networkx as nx
    deps = []
    for source, target, data in graph.edges(data=True):
        if data.get("relation") == "IMPORTS":
            src_data = graph.nodes.get(source, {})
            tgt_data = graph.nodes.get(target, {})
            deps.append({
                "source": src_data.get("path", source),
                "target": tgt_data.get("path", target),
                "relation": "IMPORTS",
            })

    return {"repo_id": repo_id, "dependencies": deps[:200]}

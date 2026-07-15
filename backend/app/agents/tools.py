"""
DevDocsAI V2 — Tool Registry
==============================
Standardized LangChain tools wrapping all existing V1 services.
Each tool has typed input/output, descriptive docstrings (used by
agents for tool selection), and error handling with graceful fallback.

Agents invoke these tools rather than calling V1 services directly.
This provides modularity, reuse, observability, and future MCP compatibility.

References:
    docs/README_V2_ARCHITECTURE.md §9 (Tool Registry)
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from langchain_core.tools import tool

from app.core.logging import get_logger

logger = get_logger(__name__)


# ── Retrieval Tools ──────────────────────────────────────────────────────────

@tool
def semantic_search(repo_id: str, query: str, top_k: int = 50) -> List[Dict[str, Any]]:
    """
    Run hybrid retrieval: Vector Search + BM25 Keyword Search + Reciprocal Rank Fusion + Graph Enrichment.

    This is the primary search tool for finding relevant code chunks in a repository.
    Returns ranked search results with content, metadata, and relevance scores.

    Args:
        repo_id: Repository identifier
        query: Natural language search query
        top_k: Maximum number of results to return (default: 50)

    Returns:
        List of search result dicts with keys: chunk_id, content, metadata, score
    """
    try:
        from app.services.retrieval.hybrid_retriever import HybridRetriever

        retriever = HybridRetriever()
        results = retriever.retrieve(repo_id=repo_id, query=query, top_k=top_k)
        return [r.to_dict() for r in results]
    except Exception as e:
        logger.error("semantic_search tool failed", repo_id=repo_id, error=str(e))
        return []


@tool
def ast_search(repo_id: str, query: str, level: str = "function", top_k: int = 20) -> List[Dict[str, Any]]:
    """
    Search for code at a specific AST level (function, class, or file).

    Uses the vector store with level filtering to find specific code constructs.

    Args:
        repo_id: Repository identifier
        query: Search query targeting specific code elements
        level: AST level filter — "function", "class", or "file"
        top_k: Maximum number of results

    Returns:
        List of search result dicts filtered to the requested AST level
    """
    try:
        from app.services.retrieval.hybrid_retriever import HybridRetriever

        retriever = HybridRetriever()
        results = retriever.retrieve(
            repo_id=repo_id, query=query, top_k=top_k, level_filter=level
        )
        return [r.to_dict() for r in results]
    except Exception as e:
        logger.error("ast_search tool failed", repo_id=repo_id, error=str(e))
        return []


# ── Graph Tools ──────────────────────────────────────────────────────────────

@tool
def graph_query(repo_id: str, entity_name: str) -> Dict[str, Any]:
    """
    Get full context for a named entity from the knowledge graph.

    Returns the entity's type, file location, outgoing dependencies (calls),
    and incoming dependencies (called_by).

    Args:
        repo_id: Repository identifier
        entity_name: Name of the function, class, or module to look up

    Returns:
        Dict with node_id, name, type, file, calls, called_by. Empty dict if not found.
    """
    try:
        from app.services.graph.graph_query import GraphQueryService

        service = GraphQueryService()
        return service.get_node_context(repo_id, entity_name)
    except Exception as e:
        logger.error("graph_query tool failed", repo_id=repo_id, error=str(e))
        return {}


@tool
def graph_dependencies(repo_id: str, entity_name: str, max_depth: int = 3) -> List[Dict[str, Any]]:
    """
    Get all entities that the given entity depends on (outgoing edges).

    Performs BFS traversal up to max_depth in the dependency graph.

    Args:
        repo_id: Repository identifier
        entity_name: Name of the entity to trace dependencies from
        max_depth: Maximum traversal depth (default: 3)

    Returns:
        List of dependent entity dicts with node_id, name, type, file
    """
    try:
        from app.services.graph.graph_query import GraphQueryService

        service = GraphQueryService()
        return service.get_dependencies_of(repo_id, entity_name, max_depth)
    except Exception as e:
        logger.error("graph_dependencies tool failed", repo_id=repo_id, error=str(e))
        return []


@tool
def graph_dependents(repo_id: str, entity_name: str) -> List[Dict[str, Any]]:
    """
    Get all entities that depend ON the given entity (reverse traversal — who calls/imports this?).

    Args:
        repo_id: Repository identifier
        entity_name: Name of the entity to find dependents of

    Returns:
        List of dependent entity dicts with node_id, name, type, file
    """
    try:
        from app.services.graph.graph_query import GraphQueryService

        service = GraphQueryService()
        return service.get_dependents_of(repo_id, entity_name)
    except Exception as e:
        logger.error("graph_dependents tool failed", repo_id=repo_id, error=str(e))
        return []


@tool
def graph_shortest_path(repo_id: str, source_name: str, target_name: str) -> Optional[List[Dict[str, Any]]]:
    """
    Find the shortest dependency path between two entities in the knowledge graph.

    Useful for tracing how two components are connected (e.g., how a route handler
    connects to a database model).

    Args:
        repo_id: Repository identifier
        source_name: Starting entity name
        target_name: Target entity name

    Returns:
        List of entities forming the path, or None if no path exists
    """
    try:
        from app.services.graph.graph_query import GraphQueryService

        service = GraphQueryService()
        return service.find_shortest_path(repo_id, source_name, target_name)
    except Exception as e:
        logger.error("graph_shortest_path tool failed", repo_id=repo_id, error=str(e))
        return None


# ── Diagram Tools ────────────────────────────────────────────────────────────

@tool
def mermaid_generator(repo_id: str, max_nodes: int = 50) -> str:
    """
    Generate a Mermaid flowchart diagram from the repository's knowledge graph.

    Returns a Mermaid syntax string that can be rendered as an interactive diagram.

    Args:
        repo_id: Repository identifier
        max_nodes: Maximum number of nodes to include (default: 50)

    Returns:
        Mermaid diagram string, or "Graph unavailable" on failure
    """
    try:
        from app.database.graph_store import graph_to_mermaid, load_graph

        graph = load_graph(repo_id)
        if graph is None:
            return "Graph unavailable — repository has not been analyzed yet."
        return graph_to_mermaid(graph, max_nodes=max_nodes)
    except Exception as e:
        logger.error("mermaid_generator tool failed", repo_id=repo_id, error=str(e))
        return "Graph unavailable due to an error."


# ── Repository Metadata Tools ───────────────────────────────────────────────

@tool
def repo_statistics(repo_id: str) -> Dict[str, Any]:
    """
    Get repository metadata and statistics from the database.

    Returns framework, architecture type, language breakdown, file/function/class counts,
    summary, and cached documentation (README, API docs, onboarding).

    Args:
        repo_id: Repository identifier

    Returns:
        Dict with all repository metadata. Returns minimal dict on failure.
    """
    try:
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import Session as SyncSession
        from app.core.config import settings
        from app.models import Repository, RepositoryMetadata

        # Build a sync engine URL from the async one
        sync_url = settings.database_url
        if "aiosqlite" in sync_url:
            sync_url = sync_url.replace("+aiosqlite", "")
        elif "asyncpg" in sync_url:
            sync_url = sync_url.replace("+asyncpg", "+psycopg2")

        engine = create_engine(sync_url)

        with SyncSession(engine) as session:
            repo = session.query(Repository).filter(Repository.id == repo_id).first()
            if not repo:
                return {"error": "Repository not found", "repo_id": repo_id}

            result: Dict[str, Any] = {
                "repo_id": repo.id,
                "repo_url": repo.repo_url,
                "repo_name": repo.repo_name,
                "owner": repo.owner,
                "status": repo.status,
                "primary_language": repo.primary_language,
            }

            meta = (
                session.query(RepositoryMetadata)
                .filter(RepositoryMetadata.repo_id == repo_id)
                .first()
            )
            if meta:
                result.update({
                    "summary": meta.summary or "",
                    "framework": meta.framework,
                    "architecture_type": meta.architecture_type,
                    "total_files": meta.total_files,
                    "total_functions": meta.total_functions,
                    "total_classes": meta.total_classes,
                    "total_lines": meta.total_lines,
                    "languages_detected": meta.languages_detected,
                    "mermaid_diagram": meta.mermaid_diagram,
                    "readme_content": meta.readme_content,
                    "api_doc_content": meta.api_doc_content,
                    "onboarding_content": meta.onboarding_content,
                    "architecture_summary": meta.architecture_summary,
                })
            return result

    except Exception as e:
        logger.error("repo_statistics tool failed", repo_id=repo_id, error=str(e))
        return {"repo_id": repo_id, "error": str(e)}


@tool
def graph_search_by_type(repo_id: str, node_type: str, limit: int = 20) -> List[Dict[str, Any]]:
    """
    Get all nodes of a given type from the knowledge graph.

    Useful for listing all classes, functions, or files in a repository.

    Args:
        repo_id: Repository identifier
        node_type: Type of node — "class", "function", "method", "file"
        limit: Maximum number of results (default: 20)

    Returns:
        List of node dicts with node_id, name, file, line_start
    """
    try:
        from app.services.graph.graph_query import GraphQueryService

        service = GraphQueryService()
        return service.search_by_type(repo_id, node_type, limit)
    except Exception as e:
        logger.error("graph_search_by_type tool failed", repo_id=repo_id, error=str(e))
        return []


# ── Tool Registry ────────────────────────────────────────────────────────────

def get_all_tools() -> List:
    """Return all registered tools for agent use."""
    return [
        semantic_search,
        ast_search,
        graph_query,
        graph_dependencies,
        graph_dependents,
        graph_shortest_path,
        mermaid_generator,
        repo_statistics,
        graph_search_by_type,
    ]


def get_retrieval_tools() -> List:
    """Return only retrieval-related tools."""
    return [semantic_search, ast_search]


def get_graph_tools() -> List:
    """Return only graph-related tools."""
    return [
        graph_query,
        graph_dependencies,
        graph_dependents,
        graph_shortest_path,
        graph_search_by_type,
        mermaid_generator,
    ]


def get_metadata_tools() -> List:
    """Return only metadata/statistics tools."""
    return [repo_statistics]

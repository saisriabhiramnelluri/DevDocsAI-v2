"""
DevDocsAI — NetworkX Graph Store (Phase 1)
In-memory graph storage per repository.
Phase 2 upgrade: Neo4j.
"""
import json
import pickle
from pathlib import Path
from typing import Any, Dict, List, Optional

import networkx as nx

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)

GRAPH_STORE_DIR = Path(settings.chroma_persist_dir) / "graphs"
GRAPH_STORE_DIR.mkdir(parents=True, exist_ok=True)


def _graph_path(repo_id: str) -> Path:
    return GRAPH_STORE_DIR / f"{repo_id}.gpickle"


def save_graph(repo_id: str, graph: nx.DiGraph) -> None:
    path = _graph_path(repo_id)
    with open(path, "wb") as f:
        pickle.dump(graph, f)
    logger.info("Graph saved", repo_id=repo_id, nodes=graph.number_of_nodes(), edges=graph.number_of_edges())


def load_graph(repo_id: str) -> Optional[nx.DiGraph]:
    path = _graph_path(repo_id)
    if not path.exists():
        return None
    with open(path, "rb") as f:
        graph = pickle.load(f)
    logger.info("Graph loaded", repo_id=repo_id, nodes=graph.number_of_nodes())
    return graph


def delete_graph(repo_id: str) -> None:
    path = _graph_path(repo_id)
    if path.exists():
        path.unlink()
        logger.info("Graph deleted", repo_id=repo_id)


def graph_to_dict(graph: nx.DiGraph) -> Dict[str, Any]:
    """Convert graph to JSON-serializable dict for API responses."""
    nodes = []
    for node_id, data in graph.nodes(data=True):
        nodes.append({"id": node_id, **data})

    edges = []
    for source, target, data in graph.edges(data=True):
        edges.append({"source": source, "target": target, **data})

    return {"nodes": nodes, "edges": edges}


def graph_to_mermaid(graph: nx.DiGraph, max_nodes: int = 50) -> str:
    """Convert graph to Mermaid flowchart syntax."""
    lines = ["graph TD"]
    node_ids = list(graph.nodes())[:max_nodes]
    visited_nodes = set(node_ids)

    for node_id in node_ids:
        data = graph.nodes[node_id]
        label = data.get("name", node_id)
        node_type = data.get("type", "unknown")
        safe_id = node_id.replace("-", "_").replace(".", "_").replace("/", "_")
        if node_type == "class":
            lines.append(f'    {safe_id}["{label}"]')
        elif node_type == "function":
            lines.append(f'    {safe_id}("{label}")')
        else:
            lines.append(f'    {safe_id}["{label}"]')

    for source, target, data in graph.edges(data=True):
        if source in visited_nodes and target in visited_nodes:
            safe_src = source.replace("-", "_").replace(".", "_").replace("/", "_")
            safe_tgt = target.replace("-", "_").replace(".", "_").replace("/", "_")
            relation = data.get("relation", "")
            if relation:
                lines.append(f"    {safe_src} -->|{relation}| {safe_tgt}")
            else:
                lines.append(f"    {safe_src} --> {safe_tgt}")

    return "\n".join(lines)

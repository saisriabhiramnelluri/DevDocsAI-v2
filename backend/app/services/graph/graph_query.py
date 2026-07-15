"""
DevDocsAI — Graph Query Service
Traversal queries on the NetworkX knowledge graph
"""
from typing import Any, Dict, List, Optional

import networkx as nx

from app.core.logging import get_logger
from app.database.graph_store import load_graph

logger = get_logger(__name__)


class GraphQueryService:
    """Performs graph traversal queries for retrieval augmentation."""

    def get_dependencies_of(
        self,
        repo_id: str,
        entity_name: str,
        max_depth: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Returns all entities that the given entity depends on.
        (Outgoing edges from entity_name)
        """
        G = load_graph(repo_id)
        if G is None:
            return []

        # Find node(s) matching entity_name
        target_nodes = [
            n for n, d in G.nodes(data=True)
            if d.get("name", "").lower() == entity_name.lower()
        ]

        results = []
        for node_id in target_nodes:
            try:
                # BFS up to max_depth
                descendants = nx.descendants(G, node_id)
                for desc in list(descendants)[:50]:
                    data = G.nodes[desc]
                    results.append({
                        "node_id": desc,
                        "name": data.get("name", desc),
                        "type": data.get("type", "unknown"),
                        "file": data.get("file", ""),
                    })
            except Exception as e:
                logger.warning("Graph traversal failed", error=str(e))

        return results

    def get_dependents_of(
        self,
        repo_id: str,
        entity_name: str,
    ) -> List[Dict[str, Any]]:
        """
        Returns all entities that depend ON the given entity.
        (Reverse traversal — who calls/imports this?)
        """
        G = load_graph(repo_id)
        if G is None:
            return []

        reversed_G = G.reverse()
        target_nodes = [
            n for n, d in G.nodes(data=True)
            if d.get("name", "").lower() == entity_name.lower()
        ]

        results = []
        for node_id in target_nodes:
            try:
                ancestors = nx.descendants(reversed_G, node_id)
                for anc in list(ancestors)[:50]:
                    data = G.nodes[anc]
                    results.append({
                        "node_id": anc,
                        "name": data.get("name", anc),
                        "type": data.get("type", "unknown"),
                        "file": data.get("file", ""),
                    })
            except Exception:
                pass

        return results

    def find_shortest_path(
        self,
        repo_id: str,
        source_name: str,
        target_name: str,
    ) -> Optional[List[Dict[str, Any]]]:
        """Find shortest path between two entities in the graph."""
        G = load_graph(repo_id)
        if G is None:
            return None

        source_nodes = [n for n, d in G.nodes(data=True) if d.get("name", "").lower() == source_name.lower()]
        target_nodes = [n for n, d in G.nodes(data=True) if d.get("name", "").lower() == target_name.lower()]

        if not source_nodes or not target_nodes:
            return None

        try:
            path = nx.shortest_path(G, source_nodes[0], target_nodes[0])
            result = []
            for node_id in path:
                data = G.nodes[node_id]
                result.append({
                    "node_id": node_id,
                    "name": data.get("name", node_id),
                    "type": data.get("type", "unknown"),
                    "file": data.get("file", ""),
                })
            return result
        except nx.NetworkXNoPath:
            return None
        except Exception as e:
            logger.warning("Path finding failed", error=str(e))
            return None

    def get_node_context(
        self,
        repo_id: str,
        entity_name: str,
    ) -> Dict[str, Any]:
        """Get full context for a named entity (neighbors, type, file)."""
        G = load_graph(repo_id)
        if G is None:
            return {}

        for node_id, data in G.nodes(data=True):
            if data.get("name", "").lower() == entity_name.lower():
                neighbors_out = list(G.successors(node_id))[:10]
                neighbors_in = list(G.predecessors(node_id))[:10]

                return {
                    "node_id": node_id,
                    "name": data.get("name"),
                    "type": data.get("type"),
                    "file": data.get("file", ""),
                    "line_start": data.get("line_start"),
                    "calls": [
                        {"id": n, "name": G.nodes[n].get("name"), "type": G.nodes[n].get("type")}
                        for n in neighbors_out
                    ],
                    "called_by": [
                        {"id": n, "name": G.nodes[n].get("name"), "type": G.nodes[n].get("type")}
                        for n in neighbors_in
                    ],
                }
        return {}

    def get_file_neighbors(self, repo_id: str, file_path: str) -> List[Dict[str, Any]]:
        """Get files that import/are imported by the given file."""
        G = load_graph(repo_id)
        if G is None:
            return []

        file_node_id = f"file:{file_path}"
        if not G.has_node(file_node_id):
            return []

        neighbors = list(G.successors(file_node_id)) + list(G.predecessors(file_node_id))
        results = []
        for n in set(neighbors):
            data = G.nodes[n]
            if data.get("type") == "file":
                results.append({
                    "node_id": n,
                    "name": data.get("name"),
                    "path": data.get("path", ""),
                })
        return results

    def search_by_type(
        self,
        repo_id: str,
        node_type: str,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        """Get all nodes of a given type (e.g., all classes, all functions)."""
        G = load_graph(repo_id)
        if G is None:
            return []

        results = []
        for node_id, data in G.nodes(data=True):
            if data.get("type") == node_type:
                results.append({
                    "node_id": node_id,
                    "name": data.get("name", ""),
                    "file": data.get("file", ""),
                    "line_start": data.get("line_start"),
                })
                if len(results) >= limit:
                    break
        return results

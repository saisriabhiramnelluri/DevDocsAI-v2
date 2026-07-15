"""
DevDocsAI — Knowledge Graph Builder
Constructs a NetworkX DiGraph from AST parse results and dependency map.
Nodes: Repository, Module, File, Class, Function
Edges: CALLS, IMPORTS, CONTAINS, EXTENDS, DEPENDS_ON
"""
from pathlib import Path
from typing import Dict, List

import networkx as nx

from app.core.logging import get_logger
from app.database.graph_store import save_graph
from app.services.parser.ast_parser import FileParseResult

logger = get_logger(__name__)


class GraphBuilder:
    """Builds a knowledge graph from parsed code entities."""

    def build(
        self,
        repo_id: str,
        repo_name: str,
        parse_results: List[FileParseResult],
        dependencies: Dict[str, List[str]],
    ) -> nx.DiGraph:
        """
        Build the full knowledge graph and persist it.
        Returns the constructed DiGraph.
        """
        G = nx.DiGraph()

        # ── Repository Node ───────────────────────────────────────────────────
        G.add_node(
            f"repo:{repo_id}",
            type="repository",
            name=repo_name,
            label=repo_name,
        )

        # ── Module Nodes (top-level directories) ─────────────────────────────
        modules_seen = set()
        for result in parse_results:
            module = Path(result.file_path).parts[0] if Path(result.file_path).parts else "root"
            if module not in modules_seen:
                modules_seen.add(module)
                G.add_node(
                    f"module:{module}",
                    type="module",
                    name=module,
                    label=module,
                )
                G.add_edge(f"repo:{repo_id}", f"module:{module}", relation="CONTAINS")

        # ── File Nodes ────────────────────────────────────────────────────────
        for result in parse_results:
            file_node_id = f"file:{result.file_path}"
            module = Path(result.file_path).parts[0] if Path(result.file_path).parts else "root"
            G.add_node(
                file_node_id,
                type="file",
                name=Path(result.file_path).name,
                path=result.file_path,
                language=result.language,
                label=Path(result.file_path).name,
                total_lines=result.total_lines,
            )
            G.add_edge(f"module:{module}", file_node_id, relation="CONTAINS")

            # ── Class Nodes ───────────────────────────────────────────────────
            for cls in result.classes:
                class_node_id = f"class:{result.file_path}:{cls.name}"
                G.add_node(
                    class_node_id,
                    type="class",
                    name=cls.name,
                    file=result.file_path,
                    label=cls.name,
                    line_start=cls.line_start,
                )
                G.add_edge(file_node_id, class_node_id, relation="CONTAINS")

                # Inheritance edges
                for base in cls.base_classes:
                    # Try to find matching class node
                    for n, d in G.nodes(data=True):
                        if d.get("type") == "class" and d.get("name") == base:
                            G.add_edge(class_node_id, n, relation="EXTENDS")
                            break

            # ── Function Nodes ────────────────────────────────────────────────
            for func in result.functions:
                func_node_id = f"func:{result.file_path}:{func.name}:{func.line_start}"
                G.add_node(
                    func_node_id,
                    type="function",
                    name=func.name,
                    file=result.file_path,
                    label=func.name,
                    line_start=func.line_start,
                    is_async=func.is_async,
                    entity_type=func.entity_type,
                )
                if func.parent_class:
                    parent_id = f"class:{result.file_path}:{func.parent_class}"
                    if G.has_node(parent_id):
                        G.add_edge(parent_id, func_node_id, relation="CONTAINS")
                    else:
                        G.add_edge(file_node_id, func_node_id, relation="CONTAINS")
                else:
                    G.add_edge(file_node_id, func_node_id, relation="CONTAINS")

        # ── Dependency Edges (IMPORTS) ────────────────────────────────────────
        for source_file, dep_files in dependencies.items():
            source_node = f"file:{source_file}"
            if not G.has_node(source_node):
                continue
            for dep_file in dep_files:
                dep_node = f"file:{dep_file}"
                if G.has_node(dep_node) and source_node != dep_node:
                    G.add_edge(source_node, dep_node, relation="IMPORTS")

        logger.info(
            "Knowledge graph built",
            repo_id=repo_id,
            nodes=G.number_of_nodes(),
            edges=G.number_of_edges(),
        )

        save_graph(repo_id, G)
        return G

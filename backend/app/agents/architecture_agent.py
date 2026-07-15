"""
DevDocsAI V2 — Architecture Agent
====================================
Specialized for structural and architectural questions. Uses knowledge
graph tools to trace dependency chains, generate Mermaid diagrams,
and analyze component relationships.

References:
    docs/README_V2_ARCHITECTURE.md §5.5 (Architecture Agent)
"""

from __future__ import annotations

from typing import Any, Dict, List

from app.agents.base import BaseAgent
from app.agents.schemas import AgentOutput, OrchestratorState
from app.agents.tools import (
    graph_dependencies,
    graph_dependents,
    graph_query,
    graph_search_by_type,
    graph_shortest_path,
    mermaid_generator,
)
from app.core.logging import get_logger

logger = get_logger(__name__)


class ArchitectureAgent(BaseAgent):
    """
    Analyzes repository architecture using the knowledge graph.
    Traces dependency chains, identifies component relationships,
    and generates Mermaid diagrams for visualization.
    """

    @property
    def name(self) -> str:
        return "architecture"

    def get_tools(self) -> List:
        return [
            graph_query,
            graph_dependencies,
            graph_dependents,
            graph_shortest_path,
            graph_search_by_type,
            mermaid_generator,
        ]

    async def execute(self, state: OrchestratorState) -> AgentOutput:
        repo_id = state.get("repo_id", "")
        query = state.get("query", "")
        retrieval_results = state.get("retrieval_results", [])

        tools_used = []
        analysis_parts = []
        total_graph_hits = 0

        # 1. Generate Mermaid diagram
        try:
            diagram = mermaid_generator.invoke({"repo_id": repo_id})
            tools_used.append("mermaid_generator")
            if diagram and "unavailable" not in diagram.lower():
                analysis_parts.append(f"**Dependency Diagram:**\n```mermaid\n{diagram}\n```")
        except Exception as e:
            logger.warning("Mermaid generation failed", error=str(e))

        # 2. Extract entity names from retrieval results for graph queries
        entities = self._extract_entities(query, retrieval_results)

        # 3. Query knowledge graph for each entity
        for entity in entities[:5]:
            try:
                context = graph_query.invoke({
                    "repo_id": repo_id,
                    "entity_name": entity,
                })
                tools_used.append("graph_query")

                if context and isinstance(context, dict) and context.get("name"):
                    total_graph_hits += 1
                    calls = context.get("calls", [])
                    called_by = context.get("called_by", [])

                    entity_info = (
                        f"**{context.get('name')}** ({context.get('type', 'unknown')}) "
                        f"in `{context.get('file', 'unknown')}`\n"
                    )
                    if calls:
                        call_names = [c.get("name", "?") for c in calls[:8]]
                        entity_info += f"  - Calls: {', '.join(call_names)}\n"
                    if called_by:
                        caller_names = [c.get("name", "?") for c in called_by[:8]]
                        entity_info += f"  - Called by: {', '.join(caller_names)}\n"

                    analysis_parts.append(entity_info)

            except Exception as e:
                logger.warning("Graph query failed for entity", entity=entity, error=str(e))

        # 4. Get class list if architecture question
        if any(kw in query.lower() for kw in ["class", "component", "module", "structure"]):
            try:
                classes = graph_search_by_type.invoke({
                    "repo_id": repo_id,
                    "node_type": "class",
                    "limit": 15,
                })
                tools_used.append("graph_search_by_type")
                if classes and isinstance(classes, list):
                    total_graph_hits += len(classes)
                    class_names = [c.get("name", "?") for c in classes]
                    analysis_parts.append(
                        f"**Key Classes ({len(classes)}):** {', '.join(class_names)}"
                    )
            except Exception:
                pass

        # 5. Try to find dependency paths between mentioned entities
        if len(entities) >= 2:
            try:
                path = graph_shortest_path.invoke({
                    "repo_id": repo_id,
                    "source_name": entities[0],
                    "target_name": entities[1],
                })
                tools_used.append("graph_shortest_path")
                if path and isinstance(path, list):
                    total_graph_hits += len(path)
                    path_str = " → ".join(
                        f"{n.get('name', '?')} ({n.get('type', '')})"
                        for n in path
                    )
                    analysis_parts.append(
                        f"**Dependency Path ({entities[0]} → {entities[1]}):**\n{path_str}"
                    )
            except Exception:
                pass

        # Compile analysis
        if analysis_parts:
            full_analysis = "\n\n".join(analysis_parts)
        else:
            full_analysis = "Architecture analysis: No graph data available for this repository."

        confidence = self._score_confidence(total_graph_hits, len(entities))

        return AgentOutput(
            agent_name=self.name,
            result=full_analysis,
            confidence=confidence,
            tools_used=list(set(tools_used)),
            reasoning_summary=(
                f"Architecture analysis: {total_graph_hits} graph hits "
                f"across {len(entities)} entities"
            ),
        )

    def _extract_entities(
        self, query: str, retrieval_results: List[Dict[str, Any]]
    ) -> List[str]:
        """Extract entity names from query and retrieval results."""
        import re

        entities = set()

        # From query: capitalized words that look like code entities
        query_entities = re.findall(
            r"\b[A-Z][a-zA-Z]+(?:Service|Controller|Manager|Handler|Client|"
            r"Repository|Store|Agent|Router|Model|Schema|Factory|Builder|"
            r"Provider|Middleware|Module|Class)?\b",
            query,
        )
        entities.update(query_entities)

        # From retrieval results: function/class names
        for r in retrieval_results[:15]:
            if isinstance(r, dict):
                meta = r.get("metadata", {})
                name = meta.get("name", "")
                if name and len(name) > 2 and not name.startswith("_"):
                    entities.add(name)

        return list(entities)[:10]

    def _score_confidence(self, graph_hits: int, entity_count: int) -> float:
        """Score confidence based on graph coverage."""
        if entity_count == 0:
            return 0.3

        coverage = min(graph_hits / max(entity_count, 1), 2.0)

        if coverage >= 1.0:
            return self.clamp_confidence(0.85 + coverage * 0.05)
        elif coverage >= 0.5:
            return self.clamp_confidence(0.6 + coverage * 0.3)
        else:
            return self.clamp_confidence(0.3 + coverage * 0.4)

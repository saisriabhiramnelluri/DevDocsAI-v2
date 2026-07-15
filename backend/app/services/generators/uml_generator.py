"""
DevDocsAI — UML Class Diagram Generator
Generates Mermaid classDiagram syntax from:
  a) An already-analyzed repository (reads AST data from graph store)
  b) Raw code snippets (LLM-based extraction)
"""
from typing import Optional, List
from .base import BaseGenerator


class UMLGenerator(BaseGenerator):
    """Generates UML class diagrams as Mermaid syntax."""

    def _build_from_graph(
        self,
        repo_id: str,
        class_filter: Optional[List[str]] = None,
        max_classes: int = 20,
    ) -> Optional[str]:
        """
        Build a Mermaid classDiagram from the existing NetworkX knowledge graph.
        Returns None if no graph is found.
        """
        try:
            from app.database.graph_store import load_graph
            graph = load_graph(repo_id)
            if not graph:
                return None

            import networkx as nx
            lines = ["classDiagram"]
            classes_seen = set()
            relations = []

            for node_id, data in graph.nodes(data=True):
                if data.get("type") != "class":
                    continue

                name = data.get("name", node_id)
                if class_filter and name not in class_filter:
                    continue
                if len(classes_seen) >= max_classes:
                    break

                classes_seen.add(name)
                methods = data.get("methods", [])
                attrs = data.get("attributes", [])

                lines.append(f"    class {name} {{")
                for attr in attrs[:6]:
                    attr_name = attr if isinstance(attr, str) else attr.get("name", str(attr))
                    lines.append(f"        +{attr_name}")
                for m in methods[:8]:
                    m_name = m if isinstance(m, str) else m.get("name", str(m))
                    lines.append(f"        +{m_name}()")
                lines.append("    }")

            # Add INHERITS edges between class nodes
            for src, tgt, edata in graph.edges(data=True):
                if edata.get("relation") == "INHERITS":
                    src_data = graph.nodes.get(src, {})
                    tgt_data = graph.nodes.get(tgt, {})
                    sn, tn = src_data.get("name", ""), tgt_data.get("name", "")
                    if sn in classes_seen and tn in classes_seen:
                        relations.append(f"    {sn} --|> {tn} : inherits")
                elif edata.get("relation") == "IMPORTS":
                    src_data = graph.nodes.get(src, {})
                    tgt_data = graph.nodes.get(tgt, {})
                    if src_data.get("type") == "class" and tgt_data.get("type") == "class":
                        sn, tn = src_data.get("name", ""), tgt_data.get("name", "")
                        if sn in classes_seen and tn in classes_seen:
                            relations.append(f"    {sn} --> {tn} : uses")

            lines.extend(relations)

            if len(classes_seen) == 0:
                return None

            return "\n".join(lines)

        except Exception:
            return None

    async def generate_from_repo(
        self,
        repo_id: str,
        class_filter: Optional[List[str]] = None,
        max_classes: int = 20,
    ) -> dict:
        """Generate UML from existing repo knowledge graph."""
        mermaid = self._build_from_graph(repo_id, class_filter, max_classes)

        if not mermaid:
            return {
                "mermaid": "classDiagram\n    note \"No class data found in graph\"",
                "source": "graph",
                "classes_count": 0,
            }

        classes_count = mermaid.count("class ") - mermaid.count("classDiagram")
        return {
            "mermaid": mermaid,
            "source": "graph",
            "classes_count": max(0, classes_count),
        }

    async def generate_from_code(
        self,
        code: str,
        language: str,
        diagram_type: str = "class",
    ) -> dict:
        """Generate UML from raw code using LLM."""
        if diagram_type == "class":
            prompt = f"""Analyze this {language} code and generate a Mermaid classDiagram.

Include:
- All classes with their attributes and methods (use + for public, - for private, # for protected)
- Inheritance relationships (--|>)
- Composition/aggregation (*--, o--)
- Dependency/usage (-->)

CODE:
```{language}
{code}
```

Return ONLY valid Mermaid classDiagram syntax. Start with: classDiagram
No explanations. No markdown fences."""

        elif diagram_type == "sequence":
            prompt = f"""Analyze this {language} code and generate a Mermaid sequenceDiagram showing the main execution flow.

Show:
- The key function/method calls between objects
- Return values where important
- Conditions (alt/else) for branching logic

CODE:
```{language}
{code}
```

Return ONLY valid Mermaid sequenceDiagram syntax. Start with: sequenceDiagram
No explanations. No markdown fences."""
        else:
            prompt = f"""Analyze this {language} code and generate a Mermaid flowchart showing the component dependencies.

CODE:
```{language}
{code}
```

Return ONLY valid Mermaid graph TD syntax. Start with: graph TD
No explanations. No markdown fences."""

        result = await self._call(user_prompt=prompt, temperature=0.1, max_tokens=2048)
        result = result.strip()
        if result.startswith("```"):
            lines = result.split("\n")
            result = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        return {
            "mermaid": result,
            "source": "llm",
            "diagram_type": diagram_type,
            "language": language,
        }

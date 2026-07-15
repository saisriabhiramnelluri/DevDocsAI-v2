"""
DevDocsAI — Tree Documentation Generator
Generates a visual directory tree with per-folder/file descriptions.
Uses existing graph data when a repo_id is provided, or walks a code string.
"""
from typing import Optional
from pathlib import PurePosixPath
from .base import BaseGenerator


class TreeGenerator(BaseGenerator):
    """Generates annotated directory tree documentation."""

    def _build_tree_from_graph(self, repo_id: str, depth: int = 4) -> Optional[dict]:
        """Extract file paths from knowledge graph."""
        try:
            from app.database.graph_store import load_graph
            graph = load_graph(repo_id)
            if not graph:
                return None

            paths = []
            for _, data in graph.nodes(data=True):
                if data.get("type") == "file":
                    p = data.get("path") or data.get("name", "")
                    if p:
                        paths.append(p.replace("\\", "/"))

            return {"paths": sorted(set(paths)), "repo_id": repo_id}
        except Exception:
            return None

    def _paths_to_tree_text(self, paths: list[str], max_depth: int = 4) -> str:
        """Convert a flat file list into ASCII tree text."""
        tree: dict = {}
        for path in paths:
            parts = PurePosixPath(path).parts
            if len(parts) > max_depth:
                parts = parts[:max_depth] + ("...",)
            node = tree
            for part in parts:
                node = node.setdefault(part, {})

        lines: list[str] = []

        def walk(node: dict, prefix: str = "") -> None:
            items = sorted(node.keys())
            for i, key in enumerate(items):
                is_last = i == len(items) - 1
                connector = "└── " if is_last else "├── "
                lines.append(f"{prefix}{connector}{key}")
                if node[key]:
                    extension = "    " if is_last else "│   "
                    walk(node[key], prefix + extension)

        walk(tree)
        return "\n".join(lines)

    async def generate_from_repo(
        self,
        repo_id: str,
        depth: int = 4,
        include_descriptions: bool = True,
    ) -> dict:
        """Generate tree doc from existing repo graph."""
        graph_data = self._build_tree_from_graph(repo_id, depth)

        if not graph_data:
            return {
                "tree_text": "(No file data found for this repository)",
                "markdown": "```\n(No file data found)\n```",
                "file_count": 0,
            }

        paths = graph_data["paths"]
        tree_text = self._paths_to_tree_text(paths, depth)

        # Generate descriptions via LLM if requested
        if include_descriptions and len(paths) > 0:
            # Pick representative dirs for LLM description
            dirs = sorted(set(
                str(PurePosixPath(p).parent)
                for p in paths
                if str(PurePosixPath(p).parent) not in (".", "")
            ))[:20]

            dir_list = "\n".join(dirs)
            prompt = f"""Given these directory paths from a software project, write a one-line description for each directory explaining its purpose.

Directories:
{dir_list}

Return ONLY the directory descriptions in this format, one per line:
path/to/dir: Short description of what this directory contains
No extra text."""

            try:
                desc_raw = await self._call(user_prompt=prompt, temperature=0.1, max_tokens=1024)
                descriptions: dict = {}
                for line in desc_raw.strip().splitlines():
                    if ":" in line:
                        parts = line.split(":", 1)
                        descriptions[parts[0].strip()] = parts[1].strip()
            except Exception:
                descriptions = {}
        else:
            descriptions = {}

        # Build markdown with inline descriptions
        md_lines = ["```", tree_text, "```", ""]
        if descriptions:
            md_lines.append("## Directory Guide\n")
            for path, desc in descriptions.items():
                md_lines.append(f"- **`{path}/`** — {desc}")

        return {
            "tree_text": tree_text,
            "markdown": "\n".join(md_lines),
            "file_count": len(paths),
            "directory_descriptions": descriptions,
        }

    async def generate_from_structure(
        self,
        structure: str,
        project_name: str = "Project",
    ) -> dict:
        """Generate enhanced tree doc from a manually provided structure string."""
        prompt = f"""Enhance this directory structure with documentation.

Project: {project_name}

Structure:
{structure}

Return a Markdown document with:
1. The tree structure in a code block
2. A "## Directory Guide" section describing each folder's purpose

No extra preamble."""

        result = await self._call(user_prompt=prompt, temperature=0.15, max_tokens=2048)
        return {
            "tree_text": structure,
            "markdown": result.strip(),
            "file_count": structure.count("\n"),
            "directory_descriptions": {},
        }

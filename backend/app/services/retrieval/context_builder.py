"""
DevDocsAI — Context Builder
Assembles retrieved chunks into an LLM-ready context string
"""
from typing import Any, Dict, List

from app.services.retrieval.hybrid_retriever import SearchResult


class ContextBuilder:
    """
    Assembles the top-K retrieved chunks into a structured context
    block for the LLM prompt.
    """

    def build_context(
        self,
        results: List[SearchResult],
        max_tokens: int = 6000,
        include_metadata: bool = True,
    ) -> str:
        """
        Build context string from search results.
        Respects approximate token budget (1 token ≈ 4 chars).
        """
        max_chars = max_tokens * 4
        context_parts = []
        used_chars = 0

        for i, result in enumerate(results):
            if used_chars >= max_chars:
                break

            meta = result.metadata
            level = meta.get("level", "unknown")
            file_path = meta.get("file", meta.get("path", ""))
            name = meta.get("name", "")

            header = f"[Source {i+1}]"
            if name:
                header += f" {name}"
            if file_path:
                header += f" ({file_path})"
            header += f" [relevance: {result.score:.2f}]"

            chunk_text = f"{header}\n{result.content}\n"
            chunk_chars = len(chunk_text)

            if used_chars + chunk_chars > max_chars:
                # Truncate this chunk
                remaining = max_chars - used_chars
                if remaining > 200:
                    chunk_text = chunk_text[:remaining] + "\n[... truncated]\n"
                    context_parts.append(chunk_text)
                break

            context_parts.append(chunk_text)
            used_chars += chunk_chars

        return "\n---\n".join(context_parts)

    def build_source_references(
        self,
        results: List[SearchResult],
        top_n: int = 10,
    ) -> List[Dict[str, Any]]:
        """Build source reference list for API response."""
        sources = []
        seen_files = set()

        for result in results[:top_n]:
            meta = result.metadata
            file_path = meta.get("file", "")
            name = meta.get("name", "")

            if file_path and (file_path, name) not in seen_files:
                seen_files.add((file_path, name))
                sources.append({
                    "file": file_path,
                    "function": name if meta.get("type") in ("function", "method") else None,
                    "line_start": meta.get("line_start"),
                    "line_end": meta.get("line_end"),
                    "content_preview": result.content[:150] + "..." if len(result.content) > 150 else result.content,
                    "score": round(result.score, 3),
                })

        return sources

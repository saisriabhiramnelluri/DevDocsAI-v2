"""
DevDocsAI — Multi-Granularity Chunker
Creates text chunks at function, class, file, module, and repository levels
"""
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.services.parser.ast_parser import FileParseResult

logger = get_logger(__name__)

CHUNK_LEVEL_FUNCTION = "function"
CHUNK_LEVEL_CLASS = "class"
CHUNK_LEVEL_FILE = "file"
CHUNK_LEVEL_MODULE = "module"
CHUNK_LEVEL_REPOSITORY = "repository"


@dataclass
class CodeChunk:
    """A single chunk ready for embedding."""
    chunk_id: str
    repo_id: str
    level: str              # function | class | file | module | repository
    content: str            # The text to embed
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_chroma_doc(self) -> Dict[str, Any]:
        return {
            "id": self.chunk_id,
            "document": self.content,
            "metadata": {
                "repo_id": self.repo_id,
                "level": self.level,
                **self.metadata,
            },
        }


class MultiGranularityChunker:
    """
    Creates chunks at 5 granularity levels from parsed file results.
    Each level has a different content format optimized for embedding.
    """

    def __init__(self, repo_id: str, max_chunk_chars: int = 4000) -> None:
        self.repo_id = repo_id
        self.max_chunk_chars = max_chunk_chars

    def create_chunks(
        self,
        parse_results: List[FileParseResult],
        source_files: Optional[Dict[str, str]] = None,  # file_path → source_content
    ) -> List[CodeChunk]:
        """Generate all chunks from parsed results."""
        chunks: List[CodeChunk] = []

        # Group by module (top-level directory)
        module_groups: Dict[str, List[FileParseResult]] = {}

        for result in parse_results:
            # Function-level chunks
            chunks.extend(self._function_chunks(result))
            # Class-level chunks
            chunks.extend(self._class_chunks(result))
            # File-level chunk
            file_chunk = self._file_chunk(result, source_files)
            if file_chunk:
                chunks.append(file_chunk)

            # Group for module-level
            module = Path(result.file_path).parts[0] if Path(result.file_path).parts else "root"
            module_groups.setdefault(module, []).append(result)

        # Module-level chunks
        for module_name, module_results in module_groups.items():
            chunk = self._module_chunk(module_name, module_results)
            if chunk:
                chunks.append(chunk)

        logger.info("Chunks created", repo_id=self.repo_id, total=len(chunks))
        return chunks

    def create_repo_summary_chunk(self, repo_summary: str) -> CodeChunk:
        """Create a single repository-level summary chunk."""
        return CodeChunk(
            chunk_id=f"{self.repo_id}_repo_summary",
            repo_id=self.repo_id,
            level=CHUNK_LEVEL_REPOSITORY,
            content=f"Repository Summary:\n{repo_summary}",
            metadata={"type": "repository_summary"},
        )

    # ── Level Generators ──────────────────────────────────────────────────────

    def _function_chunks(self, result: FileParseResult) -> List[CodeChunk]:
        chunks = []
        for func in result.functions:
            parts = []
            if func.parent_class:
                parts.append(f"Class: {func.parent_class}")
            parts.append(f"Function: {func.name} ({result.language})")
            parts.append(f"File: {func.file} (lines {func.line_start}–{func.line_end})")
            if func.parameters:
                parts.append(f"Parameters: {', '.join(func.parameters)}")
            if func.return_type:
                parts.append(f"Returns: {func.return_type}")
            if func.docstring:
                parts.append(f"Description: {func.docstring}")
            if func.decorators:
                parts.append(f"Decorators: {', '.join(func.decorators)}")
            if func.body_preview:
                parts.append(f"Code Preview:\n{func.body_preview}")

            content = "\n".join(parts)
            if len(content) > self.max_chunk_chars:
                content = content[:self.max_chunk_chars]

            safe_name = func.name.replace("/", "_").replace("\\", "_")
            safe_file = result.file_path.replace("/", "_").replace("\\", "_").replace(".", "_")

            chunks.append(CodeChunk(
                chunk_id=f"{self.repo_id}_func_{safe_file}_{safe_name}_{func.line_start}",
                repo_id=self.repo_id,
                level=CHUNK_LEVEL_FUNCTION,
                content=content,
                metadata={
                    "name": func.name,
                    "type": func.entity_type,
                    "file": func.file,
                    "line_start": func.line_start,
                    "line_end": func.line_end,
                    "language": result.language,
                    "parent_class": func.parent_class or "",
                    "is_async": str(func.is_async),
                },
            ))
        return chunks

    def _class_chunks(self, result: FileParseResult) -> List[CodeChunk]:
        chunks = []
        for cls in result.classes:
            parts = [
                f"Class: {cls.name} ({result.language})",
                f"File: {cls.file} (lines {cls.line_start}–{cls.line_end})",
            ]
            if cls.base_classes:
                parts.append(f"Inherits from: {', '.join(cls.base_classes)}")
            if cls.docstring:
                parts.append(f"Description: {cls.docstring}")

            # Find methods belonging to this class
            methods = [f.name for f in result.functions if f.parent_class == cls.name]
            if methods:
                parts.append(f"Methods: {', '.join(methods[:20])}")

            content = "\n".join(parts)
            safe_name = cls.name.replace("/", "_")
            safe_file = result.file_path.replace("/", "_").replace("\\", "_").replace(".", "_")

            chunks.append(CodeChunk(
                chunk_id=f"{self.repo_id}_class_{safe_file}_{safe_name}",
                repo_id=self.repo_id,
                level=CHUNK_LEVEL_CLASS,
                content=content,
                metadata={
                    "name": cls.name,
                    "type": "class",
                    "file": cls.file,
                    "line_start": cls.line_start,
                    "line_end": cls.line_end,
                    "language": result.language,
                    "base_classes": ", ".join(cls.base_classes),
                },
            ))
        return chunks

    def _file_chunk(
        self,
        result: FileParseResult,
        source_files: Optional[Dict[str, str]] = None,
    ) -> Optional[CodeChunk]:
        if result.parse_error:
            return None

        func_names = [f.name for f in result.functions[:30]]
        class_names = [c.name for c in result.classes[:20]]
        import_modules = [i.imported_module for i in result.imports[:20]]

        parts = [
            f"File: {result.file_path}",
            f"Language: {result.language}",
            f"Lines: {result.total_lines}",
        ]
        if class_names:
            parts.append(f"Classes: {', '.join(class_names)}")
        if func_names:
            parts.append(f"Functions: {', '.join(func_names)}")
        if import_modules:
            parts.append(f"Imports: {', '.join(import_modules[:15])}")

        content = "\n".join(parts)
        safe_file = result.file_path.replace("/", "_").replace("\\", "_").replace(".", "_")

        return CodeChunk(
            chunk_id=f"{self.repo_id}_file_{safe_file}",
            repo_id=self.repo_id,
            level=CHUNK_LEVEL_FILE,
            content=content,
            metadata={
                "type": "file",
                "file": result.file_path,
                "language": result.language,
                "total_lines": result.total_lines,
                "function_count": len(result.functions),
                "class_count": len(result.classes),
            },
        )

    def _module_chunk(self, module_name: str, results: List[FileParseResult]) -> Optional[CodeChunk]:
        if not results:
            return None

        all_funcs = [f.name for r in results for f in r.functions[:10]][:40]
        all_classes = [c.name for r in results for c in r.classes[:5]][:20]
        file_names = [r.file_path for r in results[:20]]

        parts = [
            f"Module: {module_name}",
            f"Files: {len(results)}",
        ]
        if file_names:
            parts.append(f"Contains files: {', '.join(file_names[:10])}")
        if all_classes:
            parts.append(f"Classes: {', '.join(all_classes)}")
        if all_funcs:
            parts.append(f"Functions: {', '.join(all_funcs)}")

        content = "\n".join(parts)
        safe_module = module_name.replace("/", "_").replace("\\", "_").replace(".", "_")

        return CodeChunk(
            chunk_id=f"{self.repo_id}_module_{safe_module}",
            repo_id=self.repo_id,
            level=CHUNK_LEVEL_MODULE,
            content=content,
            metadata={
                "type": "module",
                "module": module_name,
                "file_count": len(results),
            },
        )

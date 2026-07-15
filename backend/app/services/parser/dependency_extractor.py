"""
DevDocsAI — Dependency Extractor
Analyzes import relationships between files to build a dependency map
"""
from collections import defaultdict
from pathlib import Path
from typing import Dict, List, Set, Tuple

from app.core.logging import get_logger
from app.services.parser.ast_parser import FileParseResult, ImportEntity

logger = get_logger(__name__)


class DependencyExtractor:
    """
    Builds a file-level dependency map from parsed import entities.
    Maps: file → [files it imports from]
    """

    def extract(
        self,
        parse_results: List[FileParseResult],
        repo_base: Path,
    ) -> Dict[str, List[str]]:
        """
        Returns a dict: {file_path: [dependency_file_paths]}
        """
        # Build module → file_path map
        file_map = self._build_file_map(parse_results)
        dependencies: Dict[str, List[str]] = defaultdict(list)

        for result in parse_results:
            for imp in result.imports:
                resolved = self._resolve_import(
                    imp, result.file_path, file_map
                )
                if resolved and resolved != result.file_path:
                    dependencies[result.file_path].append(resolved)

        # Remove duplicates
        return {k: list(set(v)) for k, v in dependencies.items()}

    def _build_file_map(self, parse_results: List[FileParseResult]) -> Dict[str, str]:
        """Build a map from module name variants to file paths."""
        file_map: Dict[str, str] = {}
        for result in parse_results:
            path = Path(result.file_path)
            # Register by stem (no extension)
            stem = str(path.with_suffix("")).replace("\\", "/")
            file_map[stem] = result.file_path
            # Register by full path
            file_map[result.file_path] = result.file_path
            # Register by module notation (a/b/c → a.b.c)
            module_key = stem.replace("/", ".")
            file_map[module_key] = result.file_path
        return file_map

    def _resolve_import(
        self,
        imp: ImportEntity,
        current_file: str,
        file_map: Dict[str, str],
    ) -> str | None:
        """Try to resolve an import to a known file in the repo."""
        module = imp.imported_module.strip()

        # Handle relative imports
        if imp.is_relative or module.startswith("."):
            current_dir = str(Path(current_file).parent).replace("\\", "/")
            dots = len(module) - len(module.lstrip("."))
            relative_module = module.lstrip(".")
            # Go up N levels
            parts = current_dir.split("/")
            parts = parts[:max(0, len(parts) - dots + 1)]
            if relative_module:
                candidate = "/".join(parts + [relative_module.replace(".", "/")])
            else:
                candidate = "/".join(parts)
            return file_map.get(candidate) or file_map.get(candidate.replace("/", "."))

        # Try direct lookup variants
        for variant in [
            module,
            module.replace(".", "/"),
            "src/" + module.replace(".", "/"),
            "app/" + module.replace(".", "/"),
        ]:
            if variant in file_map:
                return file_map[variant]

        return None

    def get_dependency_chains(
        self,
        dependencies: Dict[str, List[str]],
        target_file: str,
        max_depth: int = 5,
    ) -> List[List[str]]:
        """
        Find all files that depend on `target_file` (reverse dependency).
        Returns chains: [[dependent_file, intermediate, ..., target_file]]
        """
        reverse_deps: Dict[str, List[str]] = defaultdict(list)
        for file, deps in dependencies.items():
            for dep in deps:
                reverse_deps[dep].append(file)

        chains: List[List[str]] = []

        def dfs(current: str, chain: List[str], depth: int) -> None:
            if depth > max_depth:
                return
            for dependent in reverse_deps.get(current, []):
                if dependent not in chain:
                    new_chain = chain + [dependent]
                    chains.append(new_chain)
                    dfs(dependent, new_chain, depth + 1)

        dfs(target_file, [target_file], 0)
        return chains

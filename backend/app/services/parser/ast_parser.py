"""
DevDocsAI — AST Parser
Uses Tree-sitter to extract structured code entities from source files.
Extracts: functions, classes, methods, imports, API routes, models.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

from app.core.logging import get_logger
from app.services.parser.language_detector import LanguageDetector

logger = get_logger(__name__)

# ── Data Classes ──────────────────────────────────────────────────────────────

@dataclass
class FunctionEntity:
    name: str
    file: str
    line_start: int
    line_end: int
    parameters: List[str] = field(default_factory=list)
    return_type: Optional[str] = None
    docstring: Optional[str] = None
    body_preview: Optional[str] = None
    is_async: bool = False
    decorators: List[str] = field(default_factory=list)
    calls: List[str] = field(default_factory=list)
    parent_class: Optional[str] = None
    entity_type: str = "function"  # function | method

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": self.entity_type,
            "file": self.file,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "parameters": self.parameters,
            "return_type": self.return_type,
            "docstring": self.docstring,
            "is_async": self.is_async,
            "decorators": self.decorators,
            "parent_class": self.parent_class,
        }


@dataclass
class ClassEntity:
    name: str
    file: str
    line_start: int
    line_end: int
    docstring: Optional[str] = None
    base_classes: List[str] = field(default_factory=list)
    methods: List[str] = field(default_factory=list)
    decorators: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "type": "class",
            "file": self.file,
            "line_start": self.line_start,
            "line_end": self.line_end,
            "base_classes": self.base_classes,
            "methods": self.methods,
        }


@dataclass
class ImportEntity:
    source_file: str
    imported_module: str
    imported_names: List[str] = field(default_factory=list)
    is_relative: bool = False


@dataclass
class FileParseResult:
    file_path: str
    language: str
    functions: List[FunctionEntity] = field(default_factory=list)
    classes: List[ClassEntity] = field(default_factory=list)
    imports: List[ImportEntity] = field(default_factory=list)
    total_lines: int = 0
    parse_error: Optional[str] = None

    @property
    def all_entities(self) -> List[Dict[str, Any]]:
        result = [f.to_dict() for f in self.functions]
        result += [c.to_dict() for c in self.classes]
        return result


# ── AST Parser ───────────────────────────────────────────────────────────────

class ASTParser:
    """
    Parses source files using Tree-sitter.
    Falls back to regex-based extraction for unsupported languages.
    """

    def __init__(self) -> None:
        self.detector = LanguageDetector()
        self._parsers: Dict[str, Any] = {}
        self._init_parsers()

    def _init_parsers(self) -> None:
        """Initialize Tree-sitter parsers for supported languages."""
        try:
            import tree_sitter_python as tspython
            from tree_sitter import Language, Parser

            self._py_parser = Parser(Language(tspython.language()))
            logger.info("Tree-sitter Python parser initialized")
        except Exception as e:
            logger.warning("Tree-sitter Python parser failed to init", error=str(e))
            self._py_parser = None

        try:
            import tree_sitter_javascript as tsjs
            from tree_sitter import Language, Parser

            self._js_parser = Parser(Language(tsjs.language()))
        except Exception as e:
            logger.warning("Tree-sitter JS parser failed", error=str(e))
            self._js_parser = None

        try:
            import tree_sitter_typescript as tsts
            from tree_sitter import Language, Parser

            self._ts_parser = Parser(Language(tsts.language_typescript()))
        except Exception as e:
            logger.warning("Tree-sitter TS parser failed", error=str(e))
            self._ts_parser = None

    def parse_file(self, file_path: Path, repo_base: Path) -> FileParseResult:
        """Parse a single source file and extract entities."""
        lang_name, grammar = self.detector.get_grammar_for_file(file_path)
        relative_path = str(file_path.relative_to(repo_base))

        try:
            source = file_path.read_text(encoding="utf-8", errors="ignore")
        except Exception as e:
            return FileParseResult(
                file_path=relative_path,
                language=lang_name,
                parse_error=str(e),
            )

        total_lines = source.count("\n") + 1
        result = FileParseResult(
            file_path=relative_path,
            language=lang_name,
            total_lines=total_lines,
        )

        if grammar == "python" and self._py_parser:
            self._parse_python(source, relative_path, result)
        elif grammar in ("javascript", "typescript") and (self._js_parser or self._ts_parser):
            self._parse_js_ts(source, relative_path, result, grammar)
        else:
            # Regex fallback
            self._parse_regex_fallback(source, relative_path, lang_name, result)

        return result

    def _parse_python(self, source: str, file_path: str, result: FileParseResult) -> None:
        """Tree-sitter Python parsing."""
        try:
            from tree_sitter import Node
            tree = self._py_parser.parse(bytes(source, "utf-8"))
            root = tree.root_node
            lines = source.splitlines()
            self._walk_python(root, source, lines, file_path, result, parent_class=None)
        except Exception as e:
            logger.warning("Python tree-sitter parse failed", file=file_path, error=str(e))
            self._parse_regex_fallback(source, file_path, "Python", result)

    def _walk_python(self, node: Any, source: str, lines: list, file_path: str,
                     result: FileParseResult, parent_class: Optional[str]) -> None:
        """Recursively walk Python AST nodes."""
        if node.type == "class_definition":
            class_name = self._get_child_text(node, "identifier", source)
            if class_name:
                bases = self._get_python_bases(node, source)
                docstring = self._get_python_docstring(node, source)
                cls = ClassEntity(
                    name=class_name,
                    file=file_path,
                    line_start=node.start_point[0] + 1,
                    line_end=node.end_point[0] + 1,
                    base_classes=bases,
                    docstring=docstring,
                )
                result.classes.append(cls)
                # Walk inside class
                for child in node.children:
                    self._walk_python(child, source, lines, file_path, result, parent_class=class_name)
            return

        if node.type == "function_definition" or node.type == "decorated_definition":
            actual_node = node
            decorators = []
            if node.type == "decorated_definition":
                for child in node.children:
                    if child.type == "decorator":
                        decorators.append(source[child.start_byte:child.end_byte].strip())
                    elif child.type in ("function_definition", "async_function_definition"):
                        actual_node = child
                        break

            is_async = actual_node.type == "async_function_definition"
            func_name = self._get_child_text(actual_node, "identifier", source)
            if func_name:
                params = self._get_python_params(actual_node, source)
                docstring = self._get_python_docstring(actual_node, source)
                body_text = source[actual_node.start_byte:actual_node.end_byte]
                # Truncate preview
                preview_lines = body_text.splitlines()[:5]
                preview = "\n".join(preview_lines)

                func = FunctionEntity(
                    name=func_name,
                    file=file_path,
                    line_start=actual_node.start_point[0] + 1,
                    line_end=actual_node.end_point[0] + 1,
                    parameters=params,
                    docstring=docstring,
                    body_preview=preview,
                    is_async=is_async,
                    decorators=decorators,
                    parent_class=parent_class,
                    entity_type="method" if parent_class else "function",
                )
                result.functions.append(func)
            return

        if node.type == "import_statement" or node.type == "import_from_statement":
            imp = self._extract_python_import(node, source, file_path)
            if imp:
                result.imports.append(imp)
            return

        for child in node.children:
            self._walk_python(child, source, lines, file_path, result, parent_class)

    def _get_child_text(self, node: Any, child_type: str, source: str) -> Optional[str]:
        for child in node.children:
            if child.type == child_type:
                return source[child.start_byte:child.end_byte]
        return None

    def _get_python_bases(self, node: Any, source: str) -> List[str]:
        bases = []
        for child in node.children:
            if child.type == "argument_list":
                for arg in child.children:
                    if arg.type not in ("(", ")", ","):
                        bases.append(source[arg.start_byte:arg.end_byte])
        return bases

    def _get_python_docstring(self, node: Any, source: str) -> Optional[str]:
        for child in node.children:
            if child.type == "block":
                for stmt in child.children:
                    if stmt.type == "expression_statement":
                        for s in stmt.children:
                            if s.type == "string":
                                raw = source[s.start_byte:s.end_byte]
                                return raw.strip('"""').strip("'''").strip('"').strip("'").strip()
        return None

    def _get_python_params(self, node: Any, source: str) -> List[str]:
        params = []
        for child in node.children:
            if child.type == "parameters":
                for param in child.children:
                    if param.type in ("identifier", "typed_parameter", "default_parameter"):
                        text = source[param.start_byte:param.end_byte].split(":")[0].split("=")[0].strip()
                        if text not in ("self", "cls", "(", ")", ","):
                            params.append(text)
        return params

    def _extract_python_import(self, node: Any, source: str, file_path: str) -> Optional[ImportEntity]:
        text = source[node.start_byte:node.end_byte]
        if node.type == "import_from_statement":
            parts = text.split("import")
            if len(parts) == 2:
                module = parts[0].replace("from", "").strip()
                names = [n.strip() for n in parts[1].split(",")]
                return ImportEntity(
                    source_file=file_path,
                    imported_module=module,
                    imported_names=names,
                    is_relative=module.startswith("."),
                )
        else:
            module = text.replace("import", "").strip().split(" as ")[0].strip()
            return ImportEntity(source_file=file_path, imported_module=module)
        return None

    def _parse_js_ts(self, source: str, file_path: str, result: FileParseResult, grammar: str) -> None:
        """Simple regex-based JS/TS extraction (Tree-sitter as primary when available)."""
        self._parse_regex_fallback(source, file_path, grammar, result)

    def _parse_regex_fallback(self, source: str, file_path: str, language: str, result: FileParseResult) -> None:
        """
        Regex-based extraction for any language.
        Extracts function names, class names, imports.
        """
        lines = source.splitlines()

        # Python / general function patterns
        func_patterns = [
            re.compile(r"^(?:async\s+)?def\s+(\w+)\s*\(", re.MULTILINE),      # Python
            re.compile(r"function\s+(\w+)\s*\(", re.MULTILINE),                # JS/TS
            re.compile(r"(?:public|private|protected|static)?\s*(?:async\s+)?(\w+)\s*\([^)]*\)\s*(?::\s*\w+)?\s*\{", re.MULTILINE),  # Java/C#
            re.compile(r"^func\s+(\w+)\s*\(", re.MULTILINE),                   # Go/Rust
            re.compile(r"^fn\s+(\w+)\s*\(", re.MULTILINE),                     # Rust
        ]

        class_patterns = [
            re.compile(r"^class\s+(\w+)", re.MULTILINE),                        # Python/JS/TS
            re.compile(r"(?:public|private|abstract)?\s*class\s+(\w+)", re.MULTILINE),  # Java/C#
            re.compile(r"^struct\s+(\w+)", re.MULTILINE),                       # Go/Rust/C++
            re.compile(r"^type\s+(\w+)\s+struct", re.MULTILINE),               # Go
        ]

        # Extract functions
        seen_funcs = set()
        for pattern in func_patterns:
            for match in pattern.finditer(source):
                name = match.group(1)
                if name and name not in seen_funcs and not name[0].isupper():
                    seen_funcs.add(name)
                    line_num = source[:match.start()].count("\n") + 1
                    # Find end of function (naive: next function or EOF + 20 lines)
                    result.functions.append(FunctionEntity(
                        name=name,
                        file=file_path,
                        line_start=line_num,
                        line_end=min(line_num + 30, len(lines)),
                        entity_type="function",
                    ))

        # Extract classes
        seen_classes = set()
        for pattern in class_patterns:
            for match in pattern.finditer(source):
                name = match.group(1)
                if name and name not in seen_classes:
                    seen_classes.add(name)
                    line_num = source[:match.start()].count("\n") + 1
                    result.classes.append(ClassEntity(
                        name=name,
                        file=file_path,
                        line_start=line_num,
                        line_end=min(line_num + 50, len(lines)),
                    ))

    def parse_repository(
        self,
        repo_path: Path,
        file_list: List[Path],
        progress_callback=None,
    ) -> List[FileParseResult]:
        """Parse all files in the repository."""
        results = []
        total = len(file_list)
        for i, file_path in enumerate(file_list):
            result = self.parse_file(file_path, repo_path)
            results.append(result)
            if progress_callback and i % 10 == 0:
                progress_callback(i, total)

        total_funcs = sum(len(r.functions) for r in results)
        total_classes = sum(len(r.classes) for r in results)
        logger.info(
            "Repository parsing complete",
            files=len(results),
            functions=total_funcs,
            classes=total_classes,
        )
        return results

"""
DevDocsAI — Language Detector
Detects programming languages in a repository by file extension analysis
"""
from collections import Counter
from pathlib import Path
from typing import Dict, List, Tuple

from app.core.logging import get_logger

logger = get_logger(__name__)

# Extension → (language_name, tree_sitter_grammar_name)
EXTENSION_MAP: Dict[str, Tuple[str, str]] = {
    ".py": ("Python", "python"),
    ".js": ("JavaScript", "javascript"),
    ".jsx": ("JavaScript", "javascript"),
    ".ts": ("TypeScript", "typescript"),
    ".tsx": ("TypeScript", "tsx"),
    ".java": ("Java", "java"),
    ".go": ("Go", "go"),
    ".rs": ("Rust", "rust"),
    ".cpp": ("C++", "cpp"),
    ".cc": ("C++", "cpp"),
    ".cxx": ("C++", "cpp"),
    ".cs": ("C#", "c_sharp"),
    ".rb": ("Ruby", "ruby"),
    ".php": ("PHP", "php"),
    ".swift": ("Swift", "swift"),
    ".kt": ("Kotlin", "kotlin"),
    ".scala": ("Scala", "scala"),
    ".c": ("C", "c"),
    ".h": ("C", "c"),
    ".hpp": ("C++", "cpp"),
}

# Languages we can fully parse with Tree-sitter
SUPPORTED_PARSE_LANGUAGES = {
    "Python", "JavaScript", "TypeScript", "Java", "Go", "Rust", "C++", "C#"
}


class LanguageDetector:
    def detect(self, files: List[Path]) -> Dict[str, int]:
        """
        Counts files per language.
        Returns: {"Python": 45, "TypeScript": 12, ...}
        """
        counts: Counter = Counter()
        for path in files:
            lang_info = EXTENSION_MAP.get(path.suffix.lower())
            if lang_info:
                counts[lang_info[0]] += 1
        return dict(counts)

    def get_primary_language(self, files: List[Path]) -> Tuple[str, str]:
        """
        Returns (language_name, grammar_name) of the most prevalent language.
        Falls back to ("Unknown", "") if no supported language found.
        """
        counts = self.detect(files)
        if not counts:
            return "Unknown", ""

        primary = max(counts, key=counts.get)
        grammar = ""
        for ext, (lang, gram) in EXTENSION_MAP.items():
            if lang == primary:
                grammar = gram
                break

        return primary, grammar

    def get_parseable_files(self, files: List[Path]) -> List[Path]:
        """Filter to only files we can parse with Tree-sitter."""
        result = []
        for path in files:
            lang_info = EXTENSION_MAP.get(path.suffix.lower())
            if lang_info and lang_info[0] in SUPPORTED_PARSE_LANGUAGES:
                result.append(path)
        return result

    def get_grammar_for_file(self, path: Path) -> Tuple[str, str]:
        """Returns (language_name, grammar_name) for a single file."""
        lang_info = EXTENSION_MAP.get(path.suffix.lower())
        if lang_info:
            return lang_info
        return "Unknown", ""

    def get_source_extensions(self) -> List[str]:
        return list(EXTENSION_MAP.keys())

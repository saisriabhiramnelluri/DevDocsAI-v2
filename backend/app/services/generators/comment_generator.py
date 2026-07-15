"""
DevDocsAI — Code Comment / DocBlock Generator
Adds language-appropriate docstring/comment annotations to source code.
Supports: Python (Google/NumPy/Sphinx), JS/TS (JSDoc), Java (Javadoc),
          Go (godoc), C# (XML), Rust (rustdoc), C++ (Doxygen)
"""
from typing import Literal
from .base import BaseGenerator, DOCBLOCK_SYSTEM

DocStyle = Literal[
    "google", "numpy", "sphinx",        # Python
    "jsdoc",                             # JS / TS
    "javadoc",                           # Java
    "godoc",                             # Go
    "xmldoc",                            # C#
    "rustdoc",                           # Rust
    "doxygen",                           # C++
    "auto",                              # pick from language
]

STYLE_NOTES: dict[str, dict[str, str]] = {
    "python": {
        "google":  "Use Google-style Python docstrings (Args:, Returns:, Raises:).",
        "numpy":   "Use NumPy-style Python docstrings (Parameters\\n----------).",
        "sphinx":  "Use Sphinx/reStructuredText docstrings (:param x:, :returns:).",
        "auto":    "Use Google-style Python docstrings.",
    },
    "javascript": {"jsdoc": "Use JSDoc (@param, @returns, @throws).", "auto": "Use JSDoc."},
    "typescript": {"jsdoc": "Use JSDoc/TSDoc (@param, @returns, @throws).", "auto": "Use TSDoc."},
    "java":   {"javadoc": "Use Javadoc (@param, @return, @throws).", "auto": "Use Javadoc."},
    "go":     {"godoc":   "Use godoc comments (// FunctionName describes...).", "auto": "Use godoc."},
    "csharp": {"xmldoc":  "Use C# XML documentation (/// <summary>).", "auto": "Use XML docs."},
    "rust":   {"rustdoc": "Use Rust doc comments (/// Description.).", "auto": "Use rustdoc."},
    "cpp":    {"doxygen": "Use Doxygen comments (@brief, @param, @return).", "auto": "Use Doxygen."},
}


class CommentGenerator(BaseGenerator):
    """Adds docblock/docstring comments to source code."""

    async def generate(
        self,
        code: str,
        language: str,
        style: DocStyle = "auto",
    ) -> dict:
        lang = language.lower().replace("-", "").replace(" ", "")
        style_map = STYLE_NOTES.get(lang, {})
        style_instruction = style_map.get(style) or style_map.get("auto") or "Use appropriate documentation comments."

        prompt = f"""{style_instruction}

Language: {language}

Add comprehensive documentation comments to EVERY function, class, and method.
Include: description, parameters, return values, raised exceptions where applicable.
Keep ALL original code exactly as-is. Only add comments.

CODE:
```{language}
{code}
```

Return ONLY the commented code. No explanations. No markdown fences."""

        result = await self._call(
            user_prompt=prompt,
            system_prompt=DOCBLOCK_SYSTEM,
            temperature=0.05,
        )

        # Strip accidental markdown fences
        result = result.strip()
        if result.startswith("```"):
            lines = result.split("\n")
            result = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        # Count added comments (rough heuristic)
        original_comment_chars = code.count("#") + code.count("//") + code.count("/*") + code.count('"""')
        new_comment_chars = result.count("#") + result.count("//") + result.count("/*") + result.count('"""')
        comments_added = max(0, new_comment_chars - original_comment_chars)

        return {
            "commented_code": result,
            "language": language,
            "style": style,
            "comments_added": comments_added,
            "original_lines": len(code.splitlines()),
            "output_lines": len(result.splitlines()),
        }

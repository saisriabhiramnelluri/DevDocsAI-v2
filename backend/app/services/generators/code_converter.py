"""
DevDocsAI — Code Language Converter
Translates source code from one programming language to another.
"""
from typing import Literal
from .base import BaseGenerator

SUPPORTED_LANGUAGES = [
    "python", "typescript", "javascript", "java", "go",
    "rust", "csharp", "cpp", "kotlin", "swift", "ruby", "php",
]

LANGUAGE_NOTES = {
    ("python", "typescript"): "Convert Python classes to TypeScript classes with type annotations. Use async/await for async functions.",
    ("python", "javascript"): "Convert Python to modern JavaScript (ES2022+). Use classes, arrow functions.",
    ("typescript", "python"): "Convert TypeScript to Python 3.10+. Use dataclasses or Pydantic for models.",
    ("javascript", "typescript"): "Add full TypeScript types. Use interfaces for objects, generics where appropriate.",
    ("python", "go"): "Convert Python to idiomatic Go. Use structs for classes, interfaces, proper error handling.",
    ("java", "kotlin"): "Convert Java to idiomatic Kotlin. Use data classes, null safety, extension functions.",
}


class CodeConverter(BaseGenerator):
    """Converts source code between programming languages."""

    async def convert(
        self,
        code: str,
        source_language: str,
        target_language: str,
        preserve_comments: bool = True,
    ) -> dict:
        src = source_language.lower().strip()
        tgt = target_language.lower().strip()

        # Language-specific tip
        pair_note = LANGUAGE_NOTES.get((src, tgt), "")
        comment_note = "Preserve all comments, translating them to the target language's comment style." if preserve_comments else "Omit comments."

        prompt = f"""Convert the following {source_language} code to {target_language}.

Rules:
- Preserve ALL business logic exactly — do not add or remove functionality
- Use idiomatic {target_language} patterns (not just a literal translation)
- {comment_note}
- Add a brief comment at the top: "Converted from {source_language} to {target_language}"
- If something has no direct equivalent, add a // NOTE: comment explaining the adaptation
{pair_note}

SOURCE CODE ({source_language}):
```{source_language}
{code}
```

Return ONLY the converted {target_language} code. No markdown fences. No explanations."""

        result = await self._call(user_prompt=prompt, temperature=0.1, max_tokens=4096)

        result = result.strip()
        if result.startswith("```"):
            lines = result.split("\n")
            result = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        warnings = []
        if src == "python" and tgt == "go":
            warnings.append("Python exceptions → Go error returns require manual review.")
        if src in ("javascript", "python") and tgt in ("java", "csharp"):
            warnings.append("Dynamic typing patterns may need explicit type declarations.")

        return {
            "converted_code": result,
            "source_language": source_language,
            "target_language": target_language,
            "original_lines": len(code.splitlines()),
            "output_lines": len(result.splitlines()),
            "warnings": warnings,
        }

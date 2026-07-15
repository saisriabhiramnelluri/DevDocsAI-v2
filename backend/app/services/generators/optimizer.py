"""
DevDocsAI — Code Optimizer / Refactor AI
Analyzes code quality and returns an improved version with a structured diff report.
Focus areas: performance, readability, security, best practices.
"""
from typing import Literal, List
from .base import BaseGenerator

FocusArea = Literal["performance", "readability", "security", "best_practices", "all"]


class CodeOptimizer(BaseGenerator):
    """Refactors and optimizes code, returning improved version + improvement list."""

    async def optimize(
        self,
        code: str,
        language: str,
        focus: FocusArea = "all",
    ) -> dict:
        focus_instructions = {
            "performance": (
                "Focus ONLY on performance: reduce time/space complexity, eliminate redundant "
                "loops, avoid unnecessary allocations, use efficient data structures."
            ),
            "readability": (
                "Focus ONLY on readability: meaningful variable names, small focused functions, "
                "remove dead code, simplify complex conditionals, add clear structure."
            ),
            "security": (
                "Focus ONLY on security: prevent injection attacks, sanitize inputs, "
                "avoid hardcoded secrets, fix insecure defaults, add proper validation."
            ),
            "best_practices": (
                "Focus ONLY on language best practices: idiomatic patterns, proper error handling, "
                "type annotations, avoid anti-patterns, follow SOLID principles."
            ),
            "all": (
                "Address ALL categories: performance, readability, security, and best practices."
            ),
        }

        prompt = f"""You are a senior {language} engineer performing a thorough code review and refactor.

Task: Analyze and improve the following code.
Focus: {focus_instructions[focus]}

IMPORTANT: Return your response in this EXACT format with these exact section headers:

===OPTIMIZED_CODE===
[The fully refactored code here]
===END_OPTIMIZED_CODE===

===IMPROVEMENTS===
[List each improvement on a separate line in this format:]
SEVERITY|LINE_RANGE|CATEGORY|DESCRIPTION
Example: HIGH|15-18|performance|Replaced O(n²) nested loop with O(n) hashmap lookup
===END_IMPROVEMENTS===

===SUMMARY===
[2-3 sentence summary of overall changes]
===END_SUMMARY===

ORIGINAL CODE ({language}):
```{language}
{code}
```"""

        raw = await self._call(user_prompt=prompt, temperature=0.1, max_tokens=6000)

        # Parse structured response
        optimized_code = code  # fallback
        improvements: List[dict] = []
        summary = ""

        try:
            if "===OPTIMIZED_CODE===" in raw:
                optimized_code = raw.split("===OPTIMIZED_CODE===")[1].split("===END_OPTIMIZED_CODE===")[0].strip()
                if optimized_code.startswith("```"):
                    lines = optimized_code.split("\n")
                    optimized_code = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

            if "===IMPROVEMENTS===" in raw:
                imp_block = raw.split("===IMPROVEMENTS===")[1].split("===END_IMPROVEMENTS===")[0].strip()
                for line in imp_block.splitlines():
                    line = line.strip()
                    if "|" in line:
                        parts = line.split("|", 3)
                        if len(parts) == 4:
                            improvements.append({
                                "severity": parts[0].strip(),
                                "line_range": parts[1].strip(),
                                "category": parts[2].strip(),
                                "description": parts[3].strip(),
                            })

            if "===SUMMARY===" in raw:
                summary = raw.split("===SUMMARY===")[1].split("===END_SUMMARY===")[0].strip()

        except Exception:
            # If parsing fails, return the raw response as optimized_code
            optimized_code = raw

        high_count = sum(1 for i in improvements if i.get("severity") == "HIGH")
        med_count = sum(1 for i in improvements if i.get("severity") == "MEDIUM")

        return {
            "original_code": code,
            "optimized_code": optimized_code,
            "improvements": improvements,
            "summary": summary,
            "language": language,
            "focus": focus,
            "stats": {
                "total_improvements": len(improvements),
                "high_severity": high_count,
                "medium_severity": med_count,
                "low_severity": len(improvements) - high_count - med_count,
            },
        }

"""
DevDocsAI — Release Notes Generator
Converts git commit messages into human-readable, categorized release notes.
"""
import re
from typing import Optional, List
from .base import BaseGenerator


CONVENTIONAL_PREFIXES = {
    "feat":     "✨ New Features",
    "fix":      "🐛 Bug Fixes",
    "perf":     "⚡ Performance",
    "refactor": "♻️ Refactoring",
    "docs":     "📝 Documentation",
    "test":     "✅ Tests",
    "chore":    "🔧 Maintenance",
    "ci":       "🤖 CI/CD",
    "build":    "📦 Build",
    "style":    "💄 Style",
    "break":    "💥 Breaking Changes",
    "BREAKING": "💥 Breaking Changes",
}


class ReleaseNotesGenerator(BaseGenerator):
    """Generates changelog / release notes from git commit history."""

    def _classify_commits(self, commits: List[str]) -> dict[str, List[str]]:
        """Heuristic grouping before sending to LLM."""
        groups: dict[str, List[str]] = {v: [] for v in CONVENTIONAL_PREFIXES.values()}
        groups["📋 Other Changes"] = []

        for commit in commits:
            matched = False
            for prefix, label in CONVENTIONAL_PREFIXES.items():
                pattern = rf"^{re.escape(prefix)}[\(:]"
                if re.match(pattern, commit, re.IGNORECASE):
                    groups[label].append(commit)
                    matched = True
                    break
            if not matched:
                groups["📋 Other Changes"].append(commit)

        return {k: v for k, v in groups.items() if v}

    async def generate(
        self,
        commits: List[str],
        version: str = "Next Release",
        from_ref: Optional[str] = None,
        to_ref: Optional[str] = None,
    ) -> dict:
        if not commits:
            return {
                "release_notes": "# Release Notes\n\nNo commits provided.",
                "version": version,
                "commit_count": 0,
                "categories": [],
            }

        commit_text = "\n".join(f"- {c}" for c in commits[:100])
        ref_range = f"{from_ref}...{to_ref}" if from_ref and to_ref else "latest commits"

        prompt = f"""You are a technical writer creating professional release notes.

Convert these git commits ({ref_range}) into clear, human-readable release notes for version {version}.

COMMITS:
{commit_text}

Rules:
1. Group into categories: New Features, Bug Fixes, Performance, Breaking Changes, Improvements, Other
2. Rewrite commit messages into user-friendly language (not just raw commit text)
3. Use past tense ("Added X", "Fixed Y", "Improved Z")
4. Skip trivial commits (merge commits, version bumps, typo fixes)
5. Format as Markdown with ## headings per category

Return ONLY the Markdown release notes starting with: # Release {version}"""

        result = await self._call(user_prompt=prompt, temperature=0.2, max_tokens=3000)
        classified = self._classify_commits(commits)

        return {
            "release_notes": result.strip(),
            "version": version,
            "commit_count": len(commits),
            "categories": list(classified.keys()),
            "from_ref": from_ref,
            "to_ref": to_ref,
        }

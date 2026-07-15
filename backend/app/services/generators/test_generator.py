"""
DevDocsAI — Unit Test Generator
Generates comprehensive unit test suites from source code.
Supports: pytest, unittest (Python), Jest (JS/TS), JUnit (Java), go test (Go)
"""
from typing import Literal
from .base import BaseGenerator

TestFramework = Literal["pytest", "unittest", "jest", "vitest", "junit", "gotest", "auto"]
CoverageLevel = Literal["basic", "medium", "high"]

FRAMEWORK_MAP = {
    "python":     {"auto": "pytest", "pytest": "pytest", "unittest": "unittest"},
    "javascript": {"auto": "jest",   "jest": "jest",     "vitest": "vitest"},
    "typescript": {"auto": "jest",   "jest": "jest",     "vitest": "vitest"},
    "java":       {"auto": "junit",  "junit": "junit"},
    "go":         {"auto": "gotest", "gotest": "gotest"},
}

COVERAGE_INSTRUCTIONS = {
    "basic":  "Cover the happy path only — basic inputs that should work correctly.",
    "medium": "Cover happy path + at least 2 edge cases (empty input, boundary values).",
    "high":   "Cover happy path, edge cases, error/exception cases, boundary values, and null/None inputs. Aim for 100% branch coverage.",
}

FRAMEWORK_NOTES = {
    "pytest":    "Use pytest. Use fixtures where appropriate. Mark parametrized tests with @pytest.mark.parametrize.",
    "unittest":  "Use Python's unittest.TestCase. Use setUp/tearDown where appropriate.",
    "jest":      "Use Jest with describe/it/expect. Mock external dependencies with jest.mock().",
    "vitest":    "Use Vitest with describe/it/expect. Mock with vi.mock().",
    "junit":     "Use JUnit 5 with @Test, @BeforeEach, @AfterEach annotations.",
    "gotest":    "Use Go's testing package. Use t.Run() for subtests and table-driven tests.",
}


class TestGenerator(BaseGenerator):
    """Generates unit test suites from source code."""

    async def generate(
        self,
        code: str,
        language: str,
        framework: TestFramework = "auto",
        coverage: CoverageLevel = "high",
    ) -> dict:
        lang = language.lower().strip()

        # Resolve framework
        resolved_framework = framework
        if framework == "auto":
            lang_map = FRAMEWORK_MAP.get(lang, {})
            resolved_framework = lang_map.get("auto", "pytest")

        fw_note = FRAMEWORK_NOTES.get(resolved_framework, f"Use {resolved_framework}.")
        cov_note = COVERAGE_INSTRUCTIONS[coverage]

        prompt = f"""Generate a comprehensive unit test suite for the following {language} code.

Framework: {resolved_framework}
{fw_note}

Coverage level: {coverage}
{cov_note}

Rules:
- Test EVERY public function and method
- Use descriptive test names that explain what is being tested
- Mock/stub external dependencies (DB calls, HTTP calls, file I/O)
- Do NOT import the module from a hardcoded path — use a relative import matching where the code would live
- Add a brief comment above each test explaining its intent
- Include imports at the top

CODE TO TEST:
```{language}
{code}
```

Return ONLY the test file content. No explanations. No markdown fences."""

        result = await self._call(user_prompt=prompt, temperature=0.2, max_tokens=4096)

        result = result.strip()
        if result.startswith("```"):
            lines = result.split("\n")
            result = "\n".join(lines[1:-1] if lines[-1].strip() == "```" else lines[1:])

        test_count = result.count("def test_") + result.count("it(") + result.count("@Test") + result.count("func Test")

        return {
            "test_code": result,
            "language": language,
            "framework": resolved_framework,
            "coverage_level": coverage,
            "estimated_test_count": test_count,
        }

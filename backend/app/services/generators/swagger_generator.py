"""
DevDocsAI — Swagger / OpenAPI Documentation Generator
Accepts an OpenAPI spec (JSON or YAML) and generates:
  - Human-readable Markdown API reference
  - Code samples in multiple languages
"""
import json
from typing import Optional, List
from .base import BaseGenerator


class SwaggerGenerator(BaseGenerator):
    """Generates human-readable API docs from an OpenAPI/Swagger spec."""

    def _parse_spec(self, spec_text: str) -> dict:
        """Try JSON first, then YAML."""
        try:
            return json.loads(spec_text)
        except json.JSONDecodeError:
            pass
        try:
            import yaml  # pyyaml
            return yaml.safe_load(spec_text)
        except Exception:
            raise ValueError("Could not parse spec — must be valid JSON or YAML.")

    def _extract_summary(self, spec: dict) -> str:
        """Build a brief text summary of the spec for the LLM prompt."""
        info = spec.get("info", {})
        paths = spec.get("paths", {})
        endpoints = []
        for path, methods in list(paths.items())[:30]:
            for method, detail in methods.items():
                if method in ("get", "post", "put", "patch", "delete"):
                    summary = detail.get("summary", "")
                    endpoints.append(f"  {method.upper()} {path} — {summary}")
        return (
            f"API: {info.get('title', 'API')} v{info.get('version', '1.0')}\n"
            f"Description: {info.get('description', '')}\n"
            f"Endpoints ({len(endpoints)} shown):\n" + "\n".join(endpoints)
        )

    async def generate(
        self,
        spec_text: str,
        output_format: str = "markdown",
        language_samples: Optional[List[str]] = None,
    ) -> dict:
        if language_samples is None:
            language_samples = ["python", "javascript", "curl"]

        try:
            spec = self._parse_spec(spec_text)
        except ValueError as e:
            raise RuntimeError(str(e))

        spec_summary = self._extract_summary(spec)
        info = spec.get("info", {})
        paths = spec.get("paths", {})
        endpoint_count = sum(
            sum(1 for m in methods if m in ("get","post","put","patch","delete"))
            for methods in paths.values()
        )

        lang_list = ", ".join(language_samples)
        prompt = f"""You are a technical writer creating professional API documentation.

Given the following OpenAPI spec summary, generate a comprehensive Markdown API reference.

{spec_summary}

Requirements:
1. Start with a brief overview section
2. Document EACH endpoint with:
   - Method + path as a heading
   - Description
   - Request parameters / body (if any)
   - Response schema
   - Code example in each of these languages: {lang_list}
3. Use clear markdown formatting (tables for parameters, code blocks for examples)
4. Make it professional and developer-friendly

Return ONLY the Markdown documentation. No preamble."""

        result = await self._call(user_prompt=prompt, temperature=0.1, max_tokens=6000)

        return {
            "documentation": result.strip(),
            "title": info.get("title", "API Reference"),
            "version": info.get("version", "1.0"),
            "endpoint_count": endpoint_count,
            "format": output_format,
            "language_samples": language_samples,
        }

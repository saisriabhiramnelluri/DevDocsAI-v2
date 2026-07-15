"""
DevDocsAI — Generator Routes  (Module 1 — Backend)
All AI generator endpoints live here.

POST /generators/comment   — DocBlock / docstring generator
POST /generators/test      — Unit test suite generator
POST /generators/uml       — UML class / sequence diagram (Mermaid)
POST /generators/convert   — Code language converter
POST /generators/optimize  — Code optimizer / refactor AI
GET  /generators/tree/{repo_id}  — Repo tree documentation
POST /generators/tree      — Tree doc from raw structure string
"""
from typing import List, Literal, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies.db import get_db
from app.core.logging import get_logger
from app.repositories.repo_repository import RepositoryRepository
from app.services.generators.comment_generator import CommentGenerator
from app.services.generators.test_generator import TestGenerator
from app.services.generators.uml_generator import UMLGenerator
from app.services.generators.code_converter import CodeConverter
from app.services.generators.optimizer import CodeOptimizer
from app.services.generators.tree_generator import TreeGenerator

router = APIRouter()
logger = get_logger(__name__)

# ── Singleton service instances ───────────────────────────────────────────────
_comment_gen = CommentGenerator()
_test_gen = TestGenerator()
_uml_gen = UMLGenerator()
_converter = CodeConverter()
_optimizer = CodeOptimizer()
_tree_gen = TreeGenerator()


# ══════════════════════════════════════════════════════════════════════════════
# 1. Code Comment / DocBlock Generator
# ══════════════════════════════════════════════════════════════════════════════

class CommentRequest(BaseModel):
    code: str = Field(..., min_length=10, description="Source code to annotate")
    language: str = Field(..., description="Programming language (python, javascript, java, ...)")
    style: str = Field("auto", description="Docstring style: google|numpy|sphinx|jsdoc|javadoc|auto")


class CommentResponse(BaseModel):
    commented_code: str
    language: str
    style: str
    comments_added: int
    original_lines: int
    output_lines: int


@router.post(
    "/comment",
    response_model=CommentResponse,
    summary="Add DocBlock / docstring comments to source code",
)
async def generate_comments(request: CommentRequest):
    """
    Takes source code and returns the same code annotated with
    language-appropriate docstrings and inline comments.
    """
    if len(request.code) > 30_000:
        raise HTTPException(status_code=413, detail="Code too large. Maximum 30,000 characters.")

    logger.info("Comment generator called", language=request.language, lines=request.code.count("\n"))

    try:
        result = await _comment_gen.generate(
            code=request.code,
            language=request.language,
            style=request.style,
        )
        return CommentResponse(**result)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


# ══════════════════════════════════════════════════════════════════════════════
# 2. Unit Test Generator
# ══════════════════════════════════════════════════════════════════════════════

class TestRequest(BaseModel):
    code: str = Field(..., min_length=10)
    language: str
    framework: str = Field("auto", description="pytest|unittest|jest|vitest|junit|gotest|auto")
    coverage: str = Field("high", description="basic|medium|high")


class TestResponse(BaseModel):
    test_code: str
    language: str
    framework: str
    coverage_level: str
    estimated_test_count: int


@router.post(
    "/test",
    response_model=TestResponse,
    summary="Generate a unit test suite from source code",
)
async def generate_tests(request: TestRequest):
    """
    Generates a comprehensive test file for the provided source code.
    Auto-selects the appropriate framework for the language when set to 'auto'.
    """
    if len(request.code) > 30_000:
        raise HTTPException(status_code=413, detail="Code too large. Maximum 30,000 characters.")

    logger.info("Test generator called", language=request.language, framework=request.framework)

    try:
        result = await _test_gen.generate(
            code=request.code,
            language=request.language,
            framework=request.framework,
            coverage=request.coverage,
        )
        return TestResponse(**result)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


# ══════════════════════════════════════════════════════════════════════════════
# 3. UML Diagram Generator
# ══════════════════════════════════════════════════════════════════════════════

class UMLFromCodeRequest(BaseModel):
    code: str = Field(..., min_length=10)
    language: str
    diagram_type: str = Field("class", description="class|sequence|component")


class UMLFromRepoRequest(BaseModel):
    repo_id: str
    class_filter: Optional[List[str]] = None
    max_classes: int = Field(20, ge=1, le=60)


class UMLResponse(BaseModel):
    mermaid: str
    source: str
    diagram_type: Optional[str] = None
    language: Optional[str] = None
    classes_count: Optional[int] = None


@router.post(
    "/uml/from-code",
    response_model=UMLResponse,
    summary="Generate UML diagram from raw code",
)
async def uml_from_code(request: UMLFromCodeRequest):
    """Generates a Mermaid UML diagram from a code snippet using LLM analysis."""
    if len(request.code) > 20_000:
        raise HTTPException(status_code=413, detail="Code too large. Maximum 20,000 characters.")

    logger.info("UML generator (code) called", language=request.language, type=request.diagram_type)

    try:
        result = await _uml_gen.generate_from_code(
            code=request.code,
            language=request.language,
            diagram_type=request.diagram_type,
        )
        return UMLResponse(**result)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


@router.post(
    "/uml/from-repo",
    response_model=UMLResponse,
    summary="Generate UML class diagram from analyzed repository",
)
async def uml_from_repo(
    request: UMLFromRepoRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Reads the repository's existing knowledge graph to generate a class diagram.
    Much faster than LLM-based generation — no extra AI calls needed.
    """
    repo_repo = RepositoryRepository(db)
    repo = await repo_repo.get_by_id(request.repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    if repo.status != "ready":
        raise HTTPException(status_code=409, detail=f"Repository not ready: {repo.status}")

    logger.info("UML generator (repo) called", repo_id=request.repo_id)

    result = await _uml_gen.generate_from_repo(
        repo_id=request.repo_id,
        class_filter=request.class_filter,
        max_classes=request.max_classes,
    )
    return UMLResponse(**result)


# ══════════════════════════════════════════════════════════════════════════════
# 4. Code Language Converter
# ══════════════════════════════════════════════════════════════════════════════

class ConvertRequest(BaseModel):
    code: str = Field(..., min_length=10)
    source_language: str
    target_language: str
    preserve_comments: bool = True


class ConvertResponse(BaseModel):
    converted_code: str
    source_language: str
    target_language: str
    original_lines: int
    output_lines: int
    warnings: List[str] = []


@router.post(
    "/convert",
    response_model=ConvertResponse,
    summary="Convert code from one programming language to another",
)
async def convert_code(request: ConvertRequest):
    """
    Translates source code to a target language using idiomatic patterns.
    Returns warnings for constructs that may need manual review.
    """
    if request.source_language.lower() == request.target_language.lower():
        raise HTTPException(status_code=400, detail="Source and target languages must differ.")
    if len(request.code) > 20_000:
        raise HTTPException(status_code=413, detail="Code too large. Maximum 20,000 characters.")

    logger.info(
        "Converter called",
        src=request.source_language,
        tgt=request.target_language,
    )

    try:
        result = await _converter.convert(
            code=request.code,
            source_language=request.source_language,
            target_language=request.target_language,
            preserve_comments=request.preserve_comments,
        )
        return ConvertResponse(**result)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


# ══════════════════════════════════════════════════════════════════════════════
# 5. Code Optimizer / Refactor AI
# ══════════════════════════════════════════════════════════════════════════════

class OptimizeRequest(BaseModel):
    code: str = Field(..., min_length=10)
    language: str
    focus: str = Field("all", description="performance|readability|security|best_practices|all")


class ImprovementItem(BaseModel):
    severity: str
    line_range: str
    category: str
    description: str


class OptimizeStats(BaseModel):
    total_improvements: int
    high_severity: int
    medium_severity: int
    low_severity: int


class OptimizeResponse(BaseModel):
    original_code: str
    optimized_code: str
    improvements: List[ImprovementItem]
    summary: str
    language: str
    focus: str
    stats: OptimizeStats


@router.post(
    "/optimize",
    response_model=OptimizeResponse,
    summary="Optimize and refactor source code with AI",
)
async def optimize_code(request: OptimizeRequest):
    """
    Returns an improved version of the code alongside a structured list of
    changes with severity levels (HIGH/MEDIUM/LOW) and categories.
    """
    if len(request.code) > 20_000:
        raise HTTPException(status_code=413, detail="Code too large. Maximum 20,000 characters.")

    logger.info("Optimizer called", language=request.language, focus=request.focus)

    try:
        result = await _optimizer.optimize(
            code=request.code,
            language=request.language,
            focus=request.focus,
        )
        return OptimizeResponse(**result)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


# ══════════════════════════════════════════════════════════════════════════════
# 6. Tree Documentation Generator
# ══════════════════════════════════════════════════════════════════════════════

class TreeFromStructureRequest(BaseModel):
    structure: str = Field(..., description="Raw directory tree text")
    project_name: str = "Project"


class TreeResponse(BaseModel):
    tree_text: str
    markdown: str
    file_count: int
    directory_descriptions: dict = {}


@router.get(
    "/tree/{repo_id}",
    response_model=TreeResponse,
    summary="Generate annotated tree documentation from analyzed repository",
)
async def tree_from_repo(
    repo_id: str,
    depth: int = 4,
    include_descriptions: bool = True,
    db: AsyncSession = Depends(get_db),
):
    """
    Reads file paths from the repository's knowledge graph and generates
    an annotated directory tree with LLM-generated folder descriptions.
    """
    repo_repo = RepositoryRepository(db)
    repo = await repo_repo.get_by_id(repo_id)
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    if repo.status != "ready":
        raise HTTPException(status_code=409, detail=f"Repository not ready: {repo.status}")

    logger.info("Tree generator (repo) called", repo_id=repo_id, depth=depth)

    result = await _tree_gen.generate_from_repo(
        repo_id=repo_id,
        depth=depth,
        include_descriptions=include_descriptions,
    )
    return TreeResponse(**result)


@router.post(
    "/tree",
    response_model=TreeResponse,
    summary="Generate tree documentation from a raw structure string",
)
async def tree_from_structure(request: TreeFromStructureRequest):
    """
    Accepts a plain text directory structure and returns an enhanced
    markdown document with folder descriptions.
    """
    logger.info("Tree generator (structure) called", project=request.project_name)

    try:
        result = await _tree_gen.generate_from_structure(
            structure=request.structure,
            project_name=request.project_name,
        )
        return TreeResponse(**result)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


# ══════════════════════════════════════════════════════════════════════════════
# 7. Swagger / OpenAPI Documentation Generator
# ══════════════════════════════════════════════════════════════════════════════

from app.services.generators.swagger_generator import SwaggerGenerator  # noqa: E402
_swagger_gen = SwaggerGenerator()


class SwaggerRequest(BaseModel):
    spec: str = Field(..., min_length=20, description="OpenAPI spec as JSON or YAML text")
    output_format: str = Field("markdown", description="markdown")
    language_samples: List[str] = Field(
        default=["python", "javascript", "curl"],
        description="Languages for code samples",
    )


class SwaggerResponse(BaseModel):
    documentation: str
    title: str
    version: str
    endpoint_count: int
    format: str
    language_samples: List[str]


@router.post(
    "/swagger",
    response_model=SwaggerResponse,
    summary="Generate human-readable API docs from OpenAPI/Swagger spec",
)
async def generate_swagger_docs(request: SwaggerRequest):
    """
    Accepts an OpenAPI 3.x or Swagger 2.0 spec (JSON or YAML) and returns
    a polished Markdown API reference with code samples.
    """
    if len(request.spec) > 100_000:
        raise HTTPException(status_code=413, detail="Spec too large. Maximum 100,000 characters.")

    logger.info("Swagger generator called", spec_size=len(request.spec))

    try:
        result = await _swagger_gen.generate(
            spec_text=request.spec,
            output_format=request.output_format,
            language_samples=request.language_samples,
        )
        return SwaggerResponse(**result)
    except (RuntimeError, ValueError) as e:
        raise HTTPException(status_code=422, detail=str(e))


# ══════════════════════════════════════════════════════════════════════════════
# 8. Release Notes Generator
# ══════════════════════════════════════════════════════════════════════════════

from app.services.generators.release_notes_generator import ReleaseNotesGenerator  # noqa: E402
_release_gen = ReleaseNotesGenerator()


class ReleaseNotesRequest(BaseModel):
    commits: List[str] = Field(..., min_length=1, description="List of git commit messages")
    version: str = Field("Next Release", description="Release version label e.g. v2.1.0")
    from_ref: Optional[str] = Field(None, description="Starting git ref / tag")
    to_ref: Optional[str] = Field(None, description="Ending git ref / tag (usually HEAD)")


class ReleaseNotesResponse(BaseModel):
    release_notes: str
    version: str
    commit_count: int
    categories: List[str]
    from_ref: Optional[str] = None
    to_ref: Optional[str] = None


@router.post(
    "/release-notes",
    response_model=ReleaseNotesResponse,
    summary="Generate human-readable release notes from git commits",
)
async def generate_release_notes(request: ReleaseNotesRequest):
    """
    Takes a list of git commit messages (from `git log --oneline`) and
    generates categorized, human-readable release notes.
    """
    if len(request.commits) > 500:
        raise HTTPException(status_code=413, detail="Too many commits. Maximum 500.")

    logger.info("Release notes generator called", commit_count=len(request.commits))

    try:
        result = await _release_gen.generate(
            commits=request.commits,
            version=request.version,
            from_ref=request.from_ref,
            to_ref=request.to_ref,
        )
        return ReleaseNotesResponse(**result)
    except RuntimeError as e:
        raise HTTPException(status_code=502, detail=str(e))


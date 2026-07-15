"""
DevDocsAI — Analysis Pipeline Celery Task
Full repository analysis: Clone → Parse → Graph → Embed → Summarize
This is the main background task. Never run this inside an API route.
"""
import asyncio
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict

from celery import Task

from app.core.logging import get_logger
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


class AnalysisTask(Task):
    """Base task with DB session management."""
    abstract = True

    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error("Analysis task failed", task_id=task_id, error=str(exc))


@celery_app.task(
    bind=True,
    base=AnalysisTask,
    name="app.workers.analysis_tasks.analyze_repository",
    max_retries=2,
)
def analyze_repository(self, repo_id: str, repo_url: str, clone_url: str, branch: str) -> Dict[str, Any]:
    """
    Full repository analysis pipeline.
    Runs synchronously inside Celery worker.
    """
    return asyncio.get_event_loop().run_until_complete(
        _run_analysis(self, repo_id, repo_url, clone_url, branch)
    )


async def _run_analysis(task, repo_id: str, repo_url: str, clone_url: str, branch: str) -> Dict[str, Any]:
    """Async implementation of the analysis pipeline."""
    from sqlalchemy.ext.asyncio import AsyncSession
    from app.database.session import AsyncSessionLocal
    from app.models import Repository, RepositoryMetadata
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        try:
            # ── Stage 1: Update status → cloning ─────────────────────────────
            await _update_status(db, repo_id, "cloning", 5, "Cloning repository...")

            from app.services.github.cloner import RepositoryCloner
            cloner = RepositoryCloner()
            repo_path = await cloner.clone(clone_url, repo_id, branch)

            # ── Stage 2: Language detection ───────────────────────────────────
            await _update_status(db, repo_id, "parsing", 15, "Detecting languages...")

            from app.services.github.cloner import RepositoryCloner
            from app.services.parser.language_detector import LanguageDetector

            detector = LanguageDetector()
            all_files = cloner.get_file_list(repo_id, extensions=detector.get_source_extensions())
            lang_counts = detector.detect(all_files)
            primary_lang, _ = detector.get_primary_language(all_files)
            parseable_files = detector.get_parseable_files(all_files)

            # Update primary language in DB
            await _update_language(db, repo_id, primary_lang, lang_counts)

            # ── Stage 3: AST Parsing ──────────────────────────────────────────
            await _update_status(db, repo_id, "parsing", 25, "Parsing source files...")

            from app.services.parser.ast_parser import ASTParser
            parser = ASTParser()
            parse_results = parser.parse_repository(repo_path, parseable_files[:500])

            total_funcs = sum(len(r.functions) for r in parse_results)
            total_classes = sum(len(r.classes) for r in parse_results)
            total_lines = sum(r.total_lines for r in parse_results)

            logger.info("Parsing complete", files=len(parse_results), funcs=total_funcs, classes=total_classes)

            # ── Stage 4: Dependency Extraction ────────────────────────────────
            await _update_status(db, repo_id, "graph", 40, "Building dependency graph...")

            from app.services.parser.dependency_extractor import DependencyExtractor
            dep_extractor = DependencyExtractor()
            dependencies = dep_extractor.extract(parse_results, repo_path)

            # ── Stage 5: Knowledge Graph ──────────────────────────────────────
            await _update_status(db, repo_id, "graph", 50, "Constructing knowledge graph...")

            from app.services.graph.graph_builder import GraphBuilder
            repo_name = repo_url.rstrip("/").split("/")[-1]
            graph_builder = GraphBuilder()
            graph = graph_builder.build(
                repo_id=repo_id,
                repo_name=repo_name,
                parse_results=parse_results,
                dependencies=dependencies,
            )

            # ── Stage 6: Generate Mermaid Diagram ────────────────────────────
            from app.database.graph_store import graph_to_mermaid
            mermaid_diagram = graph_to_mermaid(graph, max_nodes=60)

            # ── Stage 7: Generate Summary ─────────────────────────────────────
            await _update_status(db, repo_id, "summarizing", 65, "Generating repository summary...")

            summary = _generate_summary_from_parse(
                repo_name, primary_lang, lang_counts,
                parse_results, dependencies, total_funcs, total_classes, total_lines
            )

            framework = _detect_framework(repo_path, parse_results)
            arch_type = _detect_architecture(parse_results, dependencies)

            # ── Stage 8: Create Embeddings ────────────────────────────────────
            await _update_status(db, repo_id, "embedding", 75, "Creating embeddings...")

            from app.services.embeddings.chunker import MultiGranularityChunker
            from app.services.embeddings.embedder import EmbeddingService

            chunker = MultiGranularityChunker(repo_id=repo_id)
            chunks = chunker.create_chunks(parse_results)
            repo_chunk = chunker.create_repo_summary_chunk(summary)
            chunks.append(repo_chunk)

            embedder = EmbeddingService()
            stored_count = embedder.store_chunks(chunks, repo_id)

            logger.info("Embeddings stored", count=stored_count)

            # ── Stage 9: Save Metadata ────────────────────────────────────────
            await _update_status(db, repo_id, "ready", 95, "Finalizing...")

            await _save_metadata(
                db, repo_id, summary, framework, arch_type,
                len(parseable_files), total_funcs, total_classes, total_lines,
                lang_counts, mermaid_diagram
            )

            # ── Stage 10: Mark Ready ──────────────────────────────────────────
            await _update_status(db, repo_id, "ready", 100, "Analysis complete!")
            await _mark_processed(db, repo_id)

            # ── Cleanup cloned repo ───────────────────────────────────────────
            cloner.cleanup(repo_id)

            logger.info("Repository analysis complete", repo_id=repo_id)
            return {"status": "success", "repo_id": repo_id, "chunks": stored_count}

        except Exception as e:
            logger.exception("Analysis pipeline failed", repo_id=repo_id, error=str(e))
            await _update_status(db, repo_id, "failed", 0, f"Analysis failed: {str(e)}", error=str(e))
            raise


# ── Helper DB Update Functions ────────────────────────────────────────────────

async def _update_status(db, repo_id: str, status: str, progress: int, stage: str, error: str = None) -> None:
    from app.models import Repository
    from sqlalchemy import update
    kwargs = {"status": status, "progress": progress, "current_stage": stage}
    if error:
        kwargs["error_message"] = error
    stmt = (
        __import__("sqlalchemy", fromlist=["update"]).update(Repository)
        .where(Repository.id == repo_id)
        .values(**kwargs)
    )
    await db.execute(stmt)
    await db.commit()


async def _update_language(db, repo_id: str, language: str, lang_counts: dict) -> None:
    from app.models import Repository
    from sqlalchemy import update
    stmt = (
        __import__("sqlalchemy", fromlist=["update"]).update(Repository)
        .where(Repository.id == repo_id)
        .values(primary_language=language)
    )
    await db.execute(stmt)
    await db.commit()


async def _mark_processed(db, repo_id: str) -> None:
    from app.models import Repository
    from sqlalchemy import update
    stmt = (
        __import__("sqlalchemy", fromlist=["update"]).update(Repository)
        .where(Repository.id == repo_id)
        .values(processed_at=datetime.now(timezone.utc))
    )
    await db.execute(stmt)
    await db.commit()


async def _save_metadata(
    db, repo_id, summary, framework, arch_type,
    total_files, total_funcs, total_classes, total_lines,
    lang_counts, mermaid_diagram
) -> None:
    from app.models import RepositoryMetadata
    from sqlalchemy import select
    result = await db.execute(
        __import__("sqlalchemy", fromlist=["select"]).select(RepositoryMetadata)
        .where(RepositoryMetadata.repo_id == repo_id)
    )
    meta = result.scalar_one_or_none()
    if meta is None:
        meta = RepositoryMetadata(repo_id=repo_id)
        db.add(meta)

    meta.summary = summary
    meta.framework = framework
    meta.architecture_type = arch_type
    meta.total_files = total_files
    meta.total_functions = total_funcs
    meta.total_classes = total_classes
    meta.total_lines = total_lines
    meta.languages_detected = json.dumps(lang_counts)
    meta.mermaid_diagram = mermaid_diagram
    await db.commit()


# ── Analysis Helpers ──────────────────────────────────────────────────────────

def _generate_summary_from_parse(
    repo_name, primary_lang, lang_counts, parse_results, dependencies,
    total_funcs, total_classes, total_lines
) -> str:
    """Generate a text summary from parse results (no LLM needed for basic summary)."""
    top_files = sorted(
        [r for r in parse_results if r.functions or r.classes],
        key=lambda r: len(r.functions) + len(r.classes),
        reverse=True
    )[:10]

    key_classes = []
    for r in parse_results:
        for cls in r.classes[:3]:
            key_classes.append(f"{cls.name} ({r.file_path})")
        if len(key_classes) >= 10:
            break

    lang_summary = ", ".join(f"{k}: {v} files" for k, v in sorted(lang_counts.items(), key=lambda x: -x[1])[:5])

    parts = [
        f"Repository: {repo_name}",
        f"Primary Language: {primary_lang}",
        f"Languages: {lang_summary}",
        f"Total Files: {len(parse_results)}, Functions: {total_funcs}, Classes: {total_classes}, Lines: {total_lines}",
        f"Key classes: {', '.join(key_classes[:8])}" if key_classes else "",
    ]
    return "\n".join(p for p in parts if p)


def _detect_framework(repo_path: Path, parse_results) -> str:
    """Simple framework detection from file names and imports."""
    file_paths = [r.file_path.lower() for r in parse_results]
    all_imports = [
        imp.imported_module.lower()
        for r in parse_results
        for imp in r.imports
    ]

    if any("django" in i for i in all_imports):
        return "Django"
    if any("fastapi" in i for i in all_imports):
        return "FastAPI"
    if any("flask" in i for i in all_imports):
        return "Flask"
    if any("express" in i for i in all_imports):
        return "Express.js"
    if any("spring" in i for i in all_imports):
        return "Spring Boot"
    if (repo_path / "package.json").exists():
        return "Node.js"
    if (repo_path / "requirements.txt").exists():
        return "Python"
    if (repo_path / "pom.xml").exists():
        return "Java/Maven"
    if (repo_path / "go.mod").exists():
        return "Go"
    return "Unknown"


def _detect_architecture(parse_results, dependencies) -> str:
    """Heuristic architecture type detection."""
    file_paths = [r.file_path.lower() for r in parse_results]

    if any("service" in p and "controller" in p for p in file_paths):
        return "MVC/Service Layer"
    if any("microservice" in p or "gateway" in p for p in file_paths):
        return "Microservices"
    if len(dependencies) > 50:
        return "Modular Monolith"
    return "Monolith"

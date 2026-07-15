"""
DevDocsAI — FastAPI Application Entry Point
"""
import asyncio
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.llm import is_llm_configured
from app.core.logging import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: startup → validation → ready."""
    # ── Startup Validation ────────────────────────────────────────────────────
    logger.info("Starting DevDocsAI", version=settings.app_version, env=settings.environment)

    # 1. Check required environment variables
    missing: list[str] = []
    if not is_llm_configured():
        missing.append("LLM_API_KEY")
    if not settings.secret_key or settings.secret_key.startswith("change-me"):
        missing.append("SECRET_KEY")

    if missing:
        logger.warning(
            "⚠️  Missing/placeholder environment variables detected",
            missing=missing,
            hint="Copy .env.example → .env and fill in the required values.",
        )
    else:
        logger.info("✅ Environment validation passed")

    # 2. Create database tables
    from app.database.session import create_all_tables
    await create_all_tables()
    logger.info("✅ Database tables ready")

    # 3. Pre-create ChromaDB collections
    try:
        from app.database.vector_store import get_chroma_client
        get_chroma_client()
        logger.info("✅ ChromaDB ready", persist_dir=settings.chroma_persist_dir)
    except Exception as e:
        logger.warning("⚠️  ChromaDB init failed — vector search will be unavailable", error=str(e))

    # 4. Ensure clone directory exists
    from pathlib import Path
    Path(settings.repo_clone_dir).mkdir(parents=True, exist_ok=True)
    logger.info("✅ Clone directory ready", path=settings.repo_clone_dir)

    # 5. Check Redis availability (optional — graceful fallback)
    try:
        import redis
        r = redis.from_url(settings.redis_url or "redis://localhost:6379/0", socket_connect_timeout=2)
        r.ping()
        logger.info("✅ Redis connected — Celery workers available")
    except Exception:
        logger.info("ℹ️  Redis unavailable — using FastAPI BackgroundTasks (prototype mode)")

    logger.info("🚀 DevDocsAI startup complete — ready to serve requests")
    yield

    # ── Shutdown ───────────────────────────────────────────────────────────────
    logger.info("DevDocsAI shutting down")


# ── FastAPI App ────────────────────────────────────────────────────────────────
app = FastAPI(
    title="DevDocsAI API",
    description="AI Software Intelligence Platform — Understand any codebase with AI",
    version=settings.app_version,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    lifespan=lifespan,
)

# ── CORS ───────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── Global Exception Handler ───────────────────────────────────────────────────
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error("Unhandled exception", path=request.url.path, error=str(exc), exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error. Please try again."},
    )

# ── Routes ─────────────────────────────────────────────────────────────────────
from app.api.routes import health, repository, chat, documentation, architecture, search, generators

app.include_router(health.router, tags=["Health"])
app.include_router(
    repository.router,
    prefix=f"{settings.api_v1_prefix}/repositories",
    tags=["Repositories"],
)
app.include_router(
    chat.router,
    prefix=f"{settings.api_v1_prefix}/chat",
    tags=["Chat"],
)
app.include_router(
    documentation.router,
    prefix=f"{settings.api_v1_prefix}/docs",
    tags=["Documentation"],
)
app.include_router(
    architecture.router,
    prefix=f"{settings.api_v1_prefix}/architecture",
    tags=["Architecture"],
)
app.include_router(
    search.router,
    prefix=f"{settings.api_v1_prefix}/search",
    tags=["Search"],
)
app.include_router(
    generators.router,
    prefix=f"{settings.api_v1_prefix}/generators",
    tags=["Generators"],
)

# ── V2 Agent Routes ───────────────────────────────────────────────────────────
from app.api.routes import agent_chat

app.include_router(
    agent_chat.router,
    prefix=f"{settings.api_v1_prefix}/agent",
    tags=["Agent Chat (V2)"],
)


@app.get("/")
async def root():
    return {
        "app": settings.app_name,
        "version": settings.app_version,
        "description": "AI Software Intelligence Platform",
        "docs": "/docs",
    }

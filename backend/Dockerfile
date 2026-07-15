# ─────────────────────────────────────────────────────────────────────────────
# DevDocsAI Backend — Dockerfile (Production)
# Optimised for Render.com free tier (512MB RAM)
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.12-slim AS base

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    curl \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# ── Dependency layer (cached unless requirements.txt changes) ─────────────────
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Pre-download embedding model weights during build (avoids cold-start delay)
RUN python -c "\
from sentence_transformers import SentenceTransformer; \
SentenceTransformer('BAAI/bge-large-en-v1.5')" || true

# ── Application code ──────────────────────────────────────────────────────────
COPY . .

# Directories
RUN mkdir -p /tmp/devdocsai_repos /app/chroma_data /app/logs

# Non-root user for security
RUN useradd -m -u 1000 appuser && chown -R appuser:appuser /app /tmp/devdocsai_repos
USER appuser

# Expose
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -sf http://localhost:8000/health || exit 1

# ── Startup ───────────────────────────────────────────────────────────────────
# Uses uvicorn directly (no gunicorn) to keep RAM under 512MB on free tier
CMD ["uvicorn", "main:app", \
     "--host", "0.0.0.0", \
     "--port", "8000", \
     "--workers", "1", \
     "--loop", "asyncio", \
     "--access-log"]

"""
DevDocsAI — ChromaDB Vector Store Client
Singleton client for ChromaDB operations
"""
import chromadb
from chromadb.config import Settings as ChromaSettings

from app.core.config import settings
from app.core.logging import get_logger

from typing import Any
logger = get_logger(__name__)

_client: Any = None
_collection: Any = None


def get_chroma_client() -> Any:
    global _client
    if _client is None:
        _client = chromadb.PersistentClient(
            path=settings.chroma_persist_dir,
            settings=ChromaSettings(anonymized_telemetry=False),
        )
        logger.info("ChromaDB client initialized", path=settings.chroma_persist_dir)
    return _client


def get_collection(collection_name: str | None = None) -> chromadb.Collection:
    global _collection
    client = get_chroma_client()
    name = collection_name or settings.chroma_collection_name
    _collection = client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )
    return _collection


def get_repo_collection(repo_id: str) -> chromadb.Collection:
    """Get or create a per-repository collection."""
    client = get_chroma_client()
    safe_name = f"repo_{repo_id.replace('-', '_')}"
    return client.get_or_create_collection(
        name=safe_name,
        metadata={"hnsw:space": "cosine", "repo_id": repo_id},
    )


def delete_repo_collection(repo_id: str) -> None:
    """Delete a repository's vector collection."""
    client = get_chroma_client()
    safe_name = f"repo_{repo_id.replace('-', '_')}"
    try:
        client.delete_collection(safe_name)
        logger.info("Deleted ChromaDB collection", repo_id=repo_id)
    except Exception as e:
        logger.warning("Collection not found for deletion", repo_id=repo_id, error=str(e))

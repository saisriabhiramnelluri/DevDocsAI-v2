"""
DevDocsAI — Embedder Service
BAAI/bge-large-en-v1.5 embedding creation with batch processing
Stores into ChromaDB per-repository collection
"""
from typing import List

from app.core.config import settings
from app.core.logging import get_logger
from app.database.vector_store import get_repo_collection
from app.services.embeddings.chunker import CodeChunk

logger = get_logger(__name__)


class EmbeddingService:
    """Handles embedding creation and storage in ChromaDB."""

    def __init__(self) -> None:
        self._model = None

    def _get_model(self):
        """Lazy-load embedding model (avoids startup delay)."""
        if self._model is None:
            logger.info("Loading embedding model", model=settings.embedding_model)
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(
                settings.embedding_model,
                device=settings.embedding_device,
            )
            logger.info("Embedding model loaded")
        return self._model

    def embed_texts(self, texts: List[str]) -> List[List[float]]:
        """Embed a list of texts using BGE model."""
        model = self._get_model()
        # BGE models benefit from this instruction prefix for retrieval
        prefixed = [f"Represent this code context for retrieval: {t}" for t in texts]
        embeddings = model.encode(
            prefixed,
            batch_size=settings.embedding_batch_size,
            show_progress_bar=False,
            normalize_embeddings=True,
        )
        return embeddings.tolist()

    def embed_query(self, query: str) -> List[float]:
        """Embed a single query text."""
        model = self._get_model()
        # BGE uses query instruction
        prefixed = f"Represent this question for searching relevant code: {query}"
        embedding = model.encode(
            prefixed,
            normalize_embeddings=True,
        )
        return embedding.tolist()

    def store_chunks(self, chunks: List[CodeChunk], repo_id: str) -> int:
        """
        Embed and store chunks in ChromaDB.
        Returns the number of successfully stored chunks.
        """
        if not chunks:
            return 0

        collection = get_repo_collection(repo_id)
        batch_size = settings.embedding_batch_size
        stored = 0

        for i in range(0, len(chunks), batch_size):
            batch = chunks[i : i + batch_size]
            texts = [c.content for c in batch]
            ids = [c.chunk_id for c in batch]
            metadatas = [c.metadata for c in batch]

            try:
                embeddings = self.embed_texts(texts)
                collection.upsert(
                    ids=ids,
                    embeddings=embeddings,
                    documents=texts,
                    metadatas=metadatas,
                )
                stored += len(batch)
                logger.debug(f"Stored batch {i // batch_size + 1}", count=len(batch))
            except Exception as e:
                logger.error("Failed to store embedding batch", error=str(e), batch_start=i)
                continue

        logger.info("Embeddings stored", repo_id=repo_id, total=stored)
        return stored

    def query_collection(
        self,
        repo_id: str,
        query_text: str,
        n_results: int = 20,
        where: dict | None = None,
    ) -> dict:
        """Query the ChromaDB collection for a repo."""
        collection = get_repo_collection(repo_id)
        query_embedding = self.embed_query(query_text)

        kwargs = {
            "query_embeddings": [query_embedding],
            "n_results": min(n_results, collection.count() or 1),
            "include": ["documents", "metadatas", "distances"],
        }
        if where:
            kwargs["where"] = where

        return collection.query(**kwargs)

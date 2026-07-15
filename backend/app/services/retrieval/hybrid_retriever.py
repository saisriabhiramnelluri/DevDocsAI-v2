"""
DevDocsAI — Hybrid Retriever
Combines Vector Search + Keyword (BM25) Search + Graph Search
Phase 1: Vector + Keyword fusion
Phase 2: + Graph + Metadata
"""
from typing import Any, Dict, List, Optional

from rank_bm25 import BM25Okapi

from app.core.config import settings
from app.core.logging import get_logger
from app.database.vector_store import get_repo_collection
from app.services.embeddings.embedder import EmbeddingService
from app.services.graph.graph_query import GraphQueryService

logger = get_logger(__name__)


class SearchResult:
    def __init__(self, chunk_id: str, content: str, metadata: dict, score: float) -> None:
        self.chunk_id = chunk_id
        self.content = content
        self.metadata = metadata
        self.score = score

    def to_dict(self) -> Dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "content": self.content,
            "metadata": self.metadata,
            "score": self.score,
        }


class HybridRetriever:
    """
    Hybrid retrieval: Vector Search + BM25 Keyword Search.
    Results fused with Reciprocal Rank Fusion (RRF).
    """

    def __init__(self) -> None:
        self.embedder = EmbeddingService()
        self.graph_query = GraphQueryService()

    def retrieve(
        self,
        repo_id: str,
        query: str,
        top_k: int = 50,
        level_filter: Optional[str] = None,
    ) -> List[SearchResult]:
        """
        Run hybrid retrieval and return ranked results.
        """
        # 1. Vector search
        vector_results = self._vector_search(repo_id, query, n_results=top_k, level=level_filter)

        # 2. Keyword (BM25) search over vector results corpus
        keyword_results = self._keyword_search(query, vector_results)

        # 3. Fuse with RRF
        fused = self._reciprocal_rank_fusion(
            [vector_results, keyword_results],
            k=60,
        )

        # 4. Graph context enrichment
        graph_context = self._graph_enrichment(repo_id, query)

        # Add graph context as additional results
        for item in graph_context[:5]:
            if item not in [r.chunk_id for r in fused]:
                fused.append(SearchResult(
                    chunk_id=f"graph:{item.get('node_id', '')}",
                    content=f"Graph context: {item.get('name')} ({item.get('type')}) in {item.get('file', '')}",
                    metadata={"type": "graph_context", **item},
                    score=0.3,
                ))

        logger.info(
            "Hybrid retrieval complete",
            repo_id=repo_id,
            query_preview=query[:50],
            results=len(fused),
        )
        return fused[:top_k]

    def _vector_search(
        self,
        repo_id: str,
        query: str,
        n_results: int = 30,
        level: Optional[str] = None,
    ) -> List[SearchResult]:
        try:
            collection = get_repo_collection(repo_id)
            if collection.count() == 0:
                return []

            query_embedding = self.embedder.embed_query(query)
            kwargs: Dict[str, Any] = {
                "query_embeddings": [query_embedding],
                "n_results": min(n_results, collection.count()),
                "include": ["documents", "metadatas", "distances"],
            }
            if level:
                kwargs["where"] = {"level": level}

            results = collection.query(**kwargs)
            search_results = []
            docs = results.get("documents", [[]])[0]
            metas = results.get("metadatas", [[]])[0]
            dists = results.get("distances", [[]])[0]

            for doc, meta, dist in zip(docs, metas, dists):
                # cosine distance → similarity score
                score = 1.0 - dist
                search_results.append(SearchResult(
                    chunk_id=meta.get("chunk_id", ""),
                    content=doc,
                    metadata=meta,
                    score=score,
                ))
            return search_results
        except Exception as e:
            logger.error("Vector search failed", error=str(e))
            return []

    def _keyword_search(
        self,
        query: str,
        corpus: List[SearchResult],
    ) -> List[SearchResult]:
        """BM25 keyword search over the vector search corpus."""
        if not corpus:
            return []

        try:
            tokenized_corpus = [doc.content.lower().split() for doc in corpus]
            bm25 = BM25Okapi(tokenized_corpus)
            tokenized_query = query.lower().split()
            scores = bm25.get_scores(tokenized_query)

            ranked = sorted(
                zip(scores, corpus),
                key=lambda x: x[0],
                reverse=True,
            )
            return [
                SearchResult(
                    chunk_id=r.chunk_id,
                    content=r.content,
                    metadata=r.metadata,
                    score=float(s),
                )
                for s, r in ranked
            ]
        except Exception as e:
            logger.warning("BM25 search failed", error=str(e))
            return corpus

    def _reciprocal_rank_fusion(
        self,
        result_lists: List[List[SearchResult]],
        k: int = 60,
    ) -> List[SearchResult]:
        """
        Fuse multiple ranked lists using Reciprocal Rank Fusion.
        RRF score = Σ (1 / (k + rank))
        """
        rrf_scores: Dict[str, float] = {}
        chunk_map: Dict[str, SearchResult] = {}

        for ranked_list in result_lists:
            for rank, result in enumerate(ranked_list):
                cid = result.chunk_id or result.content[:50]
                rrf_scores[cid] = rrf_scores.get(cid, 0.0) + 1.0 / (k + rank + 1)
                chunk_map[cid] = result

        sorted_ids = sorted(rrf_scores, key=rrf_scores.get, reverse=True)
        fused = []
        for cid in sorted_ids:
            result = chunk_map[cid]
            fused.append(SearchResult(
                chunk_id=result.chunk_id,
                content=result.content,
                metadata=result.metadata,
                score=rrf_scores[cid],
            ))
        return fused

    def _graph_enrichment(
        self,
        repo_id: str,
        query: str,
    ) -> List[Dict[str, Any]]:
        """Extract entity names from query and do graph lookups."""
        try:
            # Simple entity extraction: capitalized words as potential entity names
            import re
            words = re.findall(r"\b[A-Z][a-zA-Z]+(?:Service|Controller|Manager|Handler|Client|Repository|Store|Agent)?\b", query)
            if not words:
                return []

            graph_results = []
            for word in words[:3]:
                context = self.graph_query.get_node_context(repo_id, word)
                if context:
                    graph_results.append(context)
            return graph_results
        except Exception:
            return []

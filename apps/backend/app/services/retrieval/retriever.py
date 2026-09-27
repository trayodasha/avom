import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from qdrant_client.models import Filter, FieldCondition, MatchValue

from app.models.document import DocumentChunk, Document
from app.services.retrieval.bm25 import BM25Index
from app.services.retrieval.rrf import ReciprocalRankFusion
from app.services.embeddings.factory import get_embedding_provider
from app.core.vector import get_qdrant_client
from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass
class RetrievedCandidate:
    chunk_id: str
    document_id: str
    filename: str
    text: str
    dense_score: float = 0.0
    sparse_score: float = 0.0
    rrf_score: float = 0.0
    initial_rank: int = 1
    rerank_score: Optional[float] = None
    reranked_rank: Optional[int] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


class HybridRetriever:
    """
    Hybrid retriever orchestrating:
    1. Dense vector search over Qdrant
    2. BM25 keyword search over project document chunks
    3. Reciprocal Rank Fusion (RRF) combining dense and sparse results
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self.qdrant = get_qdrant_client()
        self.rrf = ReciprocalRankFusion(k=60)

    def _get_collection_name(self, project_id: str) -> str:
        clean_id = project_id.replace("-", "_")
        return f"{settings.QDRANT_COLLECTION_PREFIX}{clean_id}"

    async def _fetch_project_chunks(self, project_id: str) -> List[Dict[str, Any]]:
        stmt = (
            select(DocumentChunk, Document.filename)
            .join(Document, DocumentChunk.document_id == Document.id)
            .where(DocumentChunk.project_id == project_id)
        )
        res = await self.db.execute(stmt)
        rows = res.all()
        chunks = []
        for chunk, filename in rows:
            chunks.append({
                "id": chunk.id,
                "document_id": chunk.document_id,
                "filename": filename,
                "text": chunk.text_content,
                "metadata": chunk.metadata_json or {},
            })
        return chunks

    async def retrieve_dense(
        self,
        project_id: str,
        query: str,
        embedding_model: str,
        top_k: int = 20
    ) -> List[tuple[str, float]]:
        embed_provider = get_embedding_provider(embedding_model)
        query_vector = await embed_provider.embed_query(query)
        col_name = self._get_collection_name(project_id)

        try:
            results = self.qdrant.search(
                collection_name=col_name,
                query_vector=query_vector,
                limit=top_k,
                with_payload=True,
            )
            return [(str(hit.id), float(hit.score)) for hit in results]
        except Exception as e:
            logger.warning(f"Dense vector search returned error (collection might be empty): {e}")
            return []

    async def retrieve_sparse(
        self,
        project_chunks: List[Dict[str, Any]],
        query: str,
        top_k: int = 20
    ) -> List[tuple[str, float]]:
        if not project_chunks:
            return []
        bm25 = BM25Index()
        bm25.index_documents(project_chunks)
        return bm25.search(query, top_k=top_k)

    async def retrieve(
        self,
        project_id: str,
        query: str,
        retrieval_type: str = "hybrid",
        top_k: int = 20,
        dense_weight: float = 1.0,
        sparse_weight: float = 1.0,
        embedding_model: str = "text-embedding-3-small"
    ) -> List[RetrievedCandidate]:
        project_chunks = await self._fetch_project_chunks(project_id)
        if not project_chunks:
            return []

        chunk_lookup = {c["id"]: c for c in project_chunks}

        strat = (retrieval_type or "hybrid").lower()

        if strat == "dense":
            dense_hits = await self.retrieve_dense(project_id, query, embedding_model, top_k=top_k)
            candidates = []
            for rank, (cid, score) in enumerate(dense_hits, start=1):
                if cid in chunk_lookup:
                    c = chunk_lookup[cid]
                    candidates.append(
                        RetrievedCandidate(
                            chunk_id=cid,
                            document_id=c["document_id"],
                            filename=c["filename"],
                            text=c["text"],
                            dense_score=score,
                            sparse_score=0.0,
                            rrf_score=score,
                            initial_rank=rank,
                            metadata=c["metadata"],
                        )
                    )
            return candidates

        elif strat == "sparse":
            sparse_hits = await self.retrieve_sparse(project_chunks, query, top_k=top_k)
            candidates = []
            for rank, (cid, score) in enumerate(sparse_hits, start=1):
                if cid in chunk_lookup:
                    c = chunk_lookup[cid]
                    candidates.append(
                        RetrievedCandidate(
                            chunk_id=cid,
                            document_id=c["document_id"],
                            filename=c["filename"],
                            text=c["text"],
                            dense_score=0.0,
                            sparse_score=score,
                            rrf_score=score,
                            initial_rank=rank,
                            metadata=c["metadata"],
                        )
                    )
            return candidates

        else:
            # Hybrid Fusion (Dense + BM25 via RRF)
            dense_hits = await self.retrieve_dense(project_id, query, embedding_model, top_k=top_k * 2)
            sparse_hits = await self.retrieve_sparse(project_chunks, query, top_k=top_k * 2)

            fused_items = self.rrf.fuse(
                dense_results=dense_hits,
                sparse_results=sparse_hits,
                dense_weight=dense_weight,
                sparse_weight=sparse_weight,
                top_k=top_k
            )

            candidates = []
            for item in fused_items:
                cid = item["chunk_id"]
                if cid in chunk_lookup:
                    c = chunk_lookup[cid]
                    candidates.append(
                        RetrievedCandidate(
                            chunk_id=cid,
                            document_id=c["document_id"],
                            filename=c["filename"],
                            text=c["text"],
                            dense_score=item["dense_score"],
                            sparse_score=item["sparse_score"],
                            rrf_score=item["rrf_score"],
                            initial_rank=item["initial_rank"],
                            metadata=c["metadata"],
                        )
                    )
            return candidates

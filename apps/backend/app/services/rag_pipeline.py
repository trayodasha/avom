import time
import uuid
import logging
from typing import List, Optional, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status

from app.models.user import User, UserRole
from app.repositories.project_repo import ProjectRepository
from app.schemas.query import QueryRequest, QueryResponse, RAGConfiguration, ScoredChunkResponse, CitationResponse
from app.services.retrieval.retriever import HybridRetriever, RetrievedCandidate
from app.services.reranking.factory import get_reranker
from app.services.generation.providers.factory import get_llm_provider
from app.services.generation.prompts import build_rag_prompt, DEFAULT_RAG_SYSTEM_PROMPT
from app.services.generation.citation_extractor import CitationExtractor
from app.services.tracing_service import TracingService

logger = logging.getLogger(__name__)


class RAGPipeline:
    """
    End-to-end RAG Execution Engine orchestrating:
    1. Query preprocessing
    2. Hybrid Retrieval (Dense Vector + BM25 Sparse Keyword Fusion via RRF)
    3. Cross-Encoder Reranking
    4. Top-K Context Window Assembly
    5. Grounded Prompt Generation with System Guardrails
    6. LLM Completion via Provider Abstraction
    7. Automated Citation Extraction & Trace Metadata Structuring
    """
    def __init__(self, db: AsyncSession):
        self.db = db
        self.retriever = HybridRetriever(db)
        self.proj_repo = ProjectRepository(db)
        self.tracing_service = TracingService(db)

    async def execute_query(
        self,
        request_or_project_id: Any = None,
        user_or_query: Any = None,
        request: Optional[QueryRequest] = None,
        project_id: Optional[str] = None,
        query: Optional[str] = None,
        config: Optional[RAGConfiguration] = None,
        user: Optional[User] = None,
        **kwargs
    ) -> QueryResponse:
        start_time = time.time()
        trace_id = f"tr_{uuid.uuid4().hex[:12]}"
        spans = []

        # Discern target parameters
        req_obj = request or (request_or_project_id if isinstance(request_or_project_id, QueryRequest) else None)
        user_obj = user or (user_or_query if isinstance(user_or_query, User) else None)

        if req_obj is not None:
            target_project_id = req_obj.project_id
            query_text = req_obj.query
            configuration = req_obj.configuration or RAGConfiguration()
        else:
            target_project_id = project_id or (request_or_project_id if isinstance(request_or_project_id, str) else "")
            query_text = query or (user_or_query if isinstance(user_or_query, str) else "")
            configuration = config or RAGConfiguration()

        if not target_project_id:
            raise ValueError("project_id or QueryRequest must be provided to execute_query")

        project_id = target_project_id
        current_user = user_obj

        # 1. Verify project workspace access if user is supplied
        if current_user:
            project = await self.proj_repo.get_by_id(project_id)
            if not project:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Project workspace '{project_id}' not found."
                )
            if project.user_id != current_user.id and current_user.role != UserRole.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Access denied to this project workspace."
                )

        # 2. Hybrid Retrieval (Dense Vector + BM25 Sparse via RRF)
        retrieval_start = time.time()
        candidates: List[RetrievedCandidate] = await self.retriever.retrieve(
            project_id=project_id,
            query=query_text,
            retrieval_type=configuration.retrieval_type,
            top_k=configuration.top_k,
            dense_weight=configuration.dense_weight,
            sparse_weight=configuration.sparse_weight,
            embedding_model=configuration.embedding_model,
        )
        retrieval_latency_ms = round((time.time() - retrieval_start) * 1000, 2)
        spans.append({
            "name": f"{configuration.retrieval_type}_retrieval",
            "start_time_ms": round((retrieval_start - start_time) * 1000, 2),
            "end_time_ms": round((time.time() - start_time) * 1000, 2),
            "duration_ms": retrieval_latency_ms,
            "attributes": {"candidate_count": len(candidates), "top_k": configuration.top_k}
        })

        # 3. Cross-Encoder Reranking
        reranking_start = time.time()
        reranker = get_reranker(enabled=configuration.reranking, model_name=configuration.reranker_model)
        candidates_to_rerank = candidates[:configuration.rerank_top_k]
        
        reranked_candidates = await reranker.rerank(
            query=query_text,
            candidates=candidates_to_rerank,
            top_k=configuration.final_context_k
        )
        rerank_latency_ms = round((time.time() - reranking_start) * 1000, 2)
        spans.append({
            "name": "cross_encoder_rerank",
            "start_time_ms": round((reranking_start - start_time) * 1000, 2),
            "end_time_ms": round((time.time() - start_time) * 1000, 2),
            "duration_ms": rerank_latency_ms,
            "attributes": {"reranker_model": configuration.reranker_model, "enabled": configuration.reranking}
        })

        # 4. Context Window Selection
        final_context = reranked_candidates[:configuration.final_context_k]

        # 5. Prompt Construction
        prompt_start = time.time()
        prompt = build_rag_prompt(query=query_text, context_chunks=final_context)
        prompt_latency_ms = round((time.time() - prompt_start) * 1000, 2)
        spans.append({
            "name": "prompt_construction",
            "start_time_ms": round((prompt_start - start_time) * 1000, 2),
            "end_time_ms": round((time.time() - start_time) * 1000, 2),
            "duration_ms": prompt_latency_ms,
            "attributes": {"context_chunks": len(final_context)}
        })

        # 6. LLM Generation
        gen_start = time.time()
        llm = get_llm_provider(configuration.llm_model)
        llm_response = await llm.generate(
            prompt=prompt,
            system_prompt=DEFAULT_RAG_SYSTEM_PROMPT,
            temperature=configuration.temperature
        )
        gen_latency_ms = round((time.time() - gen_start) * 1000, 2)
        spans.append({
            "name": "llm_synthesis",
            "start_time_ms": round((gen_start - start_time) * 1000, 2),
            "end_time_ms": round((time.time() - start_time) * 1000, 2),
            "duration_ms": gen_latency_ms,
            "attributes": {
                "model": configuration.llm_model,
                "input_tokens": llm_response.input_tokens,
                "output_tokens": llm_response.output_tokens
            }
        })

        # 7. Citation Extraction
        extracted_sources = CitationExtractor.extract_citations(
            answer_text=llm_response.content,
            context_chunks=final_context
        )

        total_latency_ms = round((time.time() - start_time) * 1000, 2)

        # 8. Build Scored Chunks for Retrieval Inspector
        inspector_chunks: List[ScoredChunkResponse] = []
        for c in final_context:
            inspector_chunks.append(
                ScoredChunkResponse(
                    chunk_id=c.chunk_id,
                    document_id=c.document_id,
                    filename=c.filename,
                    text=c.text,
                    dense_score=c.dense_score,
                    sparse_score=c.sparse_score,
                    rrf_score=c.rrf_score,
                    rerank_score=c.rerank_score,
                    initial_rank=c.initial_rank,
                    reranked_rank=c.reranked_rank,
                    metadata=c.metadata,
                )
            )

        citations_list: List[CitationResponse] = []
        for s in extracted_sources:
            citations_list.append(
                CitationResponse(
                    citation_id=s["citation_id"],
                    chunk_id=s["chunk_id"],
                    document_id=s["document_id"],
                    filename=s["filename"],
                    dense_score=s["dense_score"],
                    sparse_score=s["sparse_score"],
                    rerank_score=s["rerank_score"],
                    preview=s["preview"],
                    metadata=s["metadata"],
                )
            )

        # 9. Record trace asynchronously into database
        try:
            await self.tracing_service.record_trace(
                trace_id=trace_id,
                project_id=project_id,
                user_id=user.id if user else None,
                query=query_text,
                answer=llm_response.content,
                total_latency_ms=total_latency_ms,
                configuration=configuration.model_dump(),
                spans=spans,
                input_tokens=llm_response.input_tokens,
                output_tokens=llm_response.output_tokens,
                status="SUCCESS"
            )
        except Exception as te:
            logger.warning(f"Could not persist trace {trace_id}: {te}")

        return QueryResponse(
            answer=llm_response.content,
            sources=citations_list,
            retrieved_chunks=inspector_chunks,
            scores={
                "retrieval_latency_ms": retrieval_latency_ms,
                "rerank_latency_ms": rerank_latency_ms,
                "generation_latency_ms": gen_latency_ms,
                "candidate_count": len(candidates),
                "context_chunk_count": len(final_context),
                "reranker_enabled": configuration.reranking,
            },
            trace_id=trace_id,
            latency_ms=total_latency_ms,
            tokens={
                "input_tokens": llm_response.input_tokens,
                "output_tokens": llm_response.output_tokens,
                "total_tokens": llm_response.input_tokens + llm_response.output_tokens,
            }
        )


# Alias for backward compatibility
RAGPipelineService = RAGPipeline

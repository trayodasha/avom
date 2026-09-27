import re
from typing import List, Dict, Any
from app.services.retrieval.retriever import RetrievedCandidate


class CitationExtractor:
    """
    Parses bracketed citation markers from generated text and links them
    directly to retrieved context chunks and document metadata.
    """
    CITATION_REGEX = re.compile(r'\[(\d+)\]')

    @classmethod
    def extract_citations(
        cls,
        answer_text: str,
        context_chunks: List[RetrievedCandidate]
    ) -> List[Dict[str, Any]]:
        matches = cls.CITATION_REGEX.findall(answer_text)
        cited_indices = sorted(list(set(int(m) for m in matches if m.isdigit())))

        sources: List[Dict[str, Any]] = []
        for idx in cited_indices:
            # 1-based index to 0-based list
            list_idx = idx - 1
            if 0 <= list_idx < len(context_chunks):
                chunk = context_chunks[list_idx]
                sources.append({
                    "citation_id": idx,
                    "chunk_id": chunk.chunk_id,
                    "document_id": chunk.document_id,
                    "filename": chunk.filename,
                    "dense_score": chunk.dense_score,
                    "sparse_score": chunk.sparse_score,
                    "rerank_score": chunk.rerank_score,
                    "metadata": chunk.metadata,
                    "preview": chunk.text[:200] + "..." if len(chunk.text) > 200 else chunk.text
                })

        return sources

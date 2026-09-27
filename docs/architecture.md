# AVOM System Architecture & Design Specification

## 1. System Overview

AVOM is designed around the core principle of **Evaluation-First RAG Engineering**. Instead of treating RAG as a simple prompt injection wrapper, AVOM treats RAG as a measurable, reproducible distributed information retrieval and synthesis pipeline.

---

## 2. Component Design

### 2.1 Storage & Schema Isolation

- **PostgreSQL**: Stores relational metadata with foreign key constraints and transactional integrity:
  - `users` & `projects`: Multi-tenancy and workspace boundaries.
  - `documents` & `document_chunks`: Document hashes, MIME types, chunk offsets, and chunk content.
  - `rag_configurations`: Snapshot of every retrieval parameter (chunking strategy, top-k, dense/sparse weights, reranking models).
  - `datasets` & `dataset_examples`: Gold standard QA pairs, ground-truth document IDs, chunk IDs.
  - `evaluation_runs` & `evaluation_results`: Granular metric breakdowns (Recall@K, MRR, Faithfulness, Relevance).
  - `traces` & `trace_spans`: Request timings, token counts, and failure diagnoses.

- **Qdrant**: Manages dense embeddings with collection partitioning:
  - Vector similarity search (Cosine / Dot product).
  - Metadata payload filtering on `project_id` and `document_id`.

- **Redis**: Coordinates background ingestion jobs, evaluations, and short-term query caching.

---

## 3. RAG Pipeline Architecture

```text
User Query
    │
    ▼
1. Query Preprocessing & Validation
    │
    ├──▶ 2a. Query Embedding Generation (OpenAI / BGE / Local)
    │         │
    │         ▼
    │    Dense Retrieval (Qdrant Vector Search)
    │
    └──▶ 2b. Sparse Tokenization (BM25 / Inverted Index)
              │
              ▼
         Sparse Retrieval (BM25 Keyword Scoring)
    │
    ▼
3. Reciprocal Rank Fusion (RRF)
    score(d) = sum(1 / (k + rank_dense(d))) + sum(1 / (k + rank_sparse(d)))
    │
    ▼
4. Cross-Encoder Reranking (e.g. BAAI/bge-reranker-base)
    [Query, Candidate Chunk] ──▶ Reranker Cross-Attention ──▶ Relevance Score
    │
    ▼
5. Context Selection (Top-K Filter)
    │
    ▼
6. Strict Grounded Prompt Assembly
    │
    ▼
7. LLM Provider Execution (Streamed or Non-Streamed)
    │
    ▼
8. Citation Extraction & Trace Logging
```

---

## 4. Evaluation Architecture

AVOM separates evaluation into **Retrieval Metrics** and **Generation Metrics**:

### 4.1 Retrieval Metrics
- **Recall@K**: Proportion of ground-truth relevant chunks present in top-K candidates.
- **Precision@K**: Proportion of retrieved chunks in top-K that are relevant.
- **MRR (Mean Reciprocal Rank)**: Position of the first relevant chunk in ranked results:
  $$MRR = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i}$$
- **NDCG@K**: Normalized Discounted Cumulative Gain accounting for rank position.

### 4.2 Generation Metrics (LLM-as-a-Judge)
- **Faithfulness**: Verifies whether claims in the generated response can be directly inferred from the retrieved chunks.
- **Answer Relevance**: Verifies whether the response directly addresses the user's intent without extraneous hallucination.
- **Citation Precision**: Verifies whether cited chunks actually support the statement they are attached to.
- Evaluators output structured JSON:
  ```json
  {
    "score": 0.92,
    "reason": "Direct evidence found in chunk #2; claims verified.",
    "passed": true
  }
  ```

---

## 5. Failure Analysis Taxonomy

When a query fails quality checks, AVOM classifies the failure into explicit buckets:
1. `NO_RELEVANT_CONTEXT`: Retrieval returned zero chunks with similarity above the cutoff threshold.
2. `BAD_RETRIEVAL`: Relevant context existed in the corpus, but vector/BM25 retrieval ranked irrelevant chunks higher.
3. `BAD_RERANKING`: Dense/sparse retrieval found relevant chunks, but reranker pushed them out of the top-K window.
4. `INSUFFICIENT_CONTEXT`: The question requires knowledge not present in the indexed documents.
5. `HALLUCINATION`: The LLM produced statements contradicting or unsupported by the retrieved context.
6. `WRONG_CITATION`: Citations point to chunks that do not substantiate the claim.

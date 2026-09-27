# AVOM API Specification (v1)

## Base URL
`/api/v1`

---

## 1. Health & Readiness

### `GET /health`
Liveness check returning service status.

### `GET /api/v1/health`
Detailed service metadata and uptime.

### `GET /api/v1/health/readiness`
Component readiness check verifying connectivity to PostgreSQL database and Qdrant vector engine.

Response:
```json
{
  "status": "ready",
  "service": "AVOM",
  "environment": "development",
  "components": {
    "database": "connected",
    "vector_store": "connected"
  },
  "timestamp": 1727407000.12
}
```

---

## 2. Authentication & Users

### `POST /api/v1/auth/register`
Register a new user account with hashed password storage.
- **Request Body**:
  ```json
  {
    "email": "engineer@avom.ai",
    "password": "strongPassword123!",
    "full_name": "RAG Engineer",
    "role": "USER"
  }
  ```
- **Response**: `201 Created` with sanitized `UserResponse` (password and hash omitted).

### `POST /api/v1/auth/login`
Authenticate user credentials and obtain a signed JWT Bearer access token.
- **Request Body**:
  ```json
  {
    "email": "engineer@avom.ai",
    "password": "strongPassword123!"
  }
  ```
- **Response**: `200 OK`
  ```json
  {
    "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "token_type": "bearer",
    "user": {
      "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
      "email": "engineer@avom.ai",
      "full_name": "RAG Engineer",
      "role": "USER",
      "is_active": true,
      "created_at": "2026-09-27T08:00:00Z",
      "updated_at": "2026-09-27T08:00:00Z"
    }
  }
  ```

### `GET /api/v1/auth/me`
Protected route returning current authenticated user profile.
- **Header**: `Authorization: Bearer <token>`
- **Response**: `200 OK` with `UserResponse`

### `GET /api/v1/auth/admin-only`
Role-protected route restricted exclusively to users possessing the `ADMIN` role.
- **Header**: `Authorization: Bearer <admin_token>`
- **Response**: `200 OK` (or `403 Forbidden` if role is `USER`)

---

## 3. Projects & Workspaces

### `GET /api/v1/projects`
List project workspaces accessible to the authenticated user.
- **Header**: `Authorization: Bearer <token>`
- **Query Parameters**:
  - `skip` (int, default: 0)
  - `limit` (int, default: 100)
- **Response**: `200 OK` List of `ProjectResponse`

### `POST /api/v1/projects`
Create a new isolated project workspace.
- **Header**: `Authorization: Bearer <token>`
- **Request Body**:
  ```json
  {
    "name": "Customer Support Knowledge Base",
    "description": "Internal docs, escalation matrix, and FAQ articles."
  }
  ```
- **Response**: `201 Created`
  ```json
  {
    "id": "e4b281f9-d5c2-488b-a320-b3eec6a93551",
    "user_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "name": "Customer Support Knowledge Base",
    "description": "Internal docs, escalation matrix, and FAQ articles.",
    "created_at": "2026-09-27T08:30:00Z",
    "updated_at": "2026-09-27T08:30:00Z"
  }
  ```

### `GET /api/v1/projects/{project_id}`
Retrieve details for a specific project workspace.
- **Header**: `Authorization: Bearer <token>`
- **Response**: `200 OK` (or `403 Forbidden` if user does not own project and is not `ADMIN`)

### `PUT /api/v1/projects/{project_id}`
Update name or description of an existing project workspace.
- **Header**: `Authorization: Bearer <token>`
- **Response**: `200 OK` with updated `ProjectResponse`

### `DELETE /api/v1/projects/{project_id}`
Permanently delete a project workspace and cascade-delete all associated documents and chunks.
- **Header**: `Authorization: Bearer <token>`
- **Response**: `204 No Content`

---

## 4. Document Ingestion & Chunks

### `POST /api/v1/documents/upload`
Upload and process a document (PDF, TXT, Markdown, DOCX) into an isolated project workspace.
- **Content-Type**: `multipart/form-data`
- **Form Fields**:
  - `file`: Binary document file
  - `project_id`: Target project UUID
  - `chunking_strategy`: `recursive` (default), `fixed`, or `semantic`
  - `chunk_size`: Target character size (e.g. 500)
  - `chunk_overlap`: Character overlap (e.g. 50)
  - `embedding_model`: `text-embedding-3-small` or `bge-small-en-v1.5`
- **Response**: `201 Created`
  ```json
  {
    "id": "70d3abe3-8688-4133-8400-7b14efee73d7",
    "project_id": "0a87fed5-cd2c-415c-a5c8-54a42f32bff3",
    "filename": "security_whitepaper.pdf",
    "file_type": "pdf",
    "file_size": 245100,
    "checksum": "376adf9b950498886bb0e3b06c4444c5...",
    "status": "INDEXED",
    "chunk_count": 18,
    "embedding_model": "bge-small-en-v1.5",
    "chunking_strategy": "recursive",
    "created_at": "2026-09-27T08:45:00Z",
    "updated_at": "2026-09-27T08:45:02Z"
  }
  ```

### `GET /api/v1/documents?project_id={project_id}`
List all ingested documents within a workspace.
- **Header**: `Authorization: Bearer <token>`
- **Response**: `200 OK` List of `DocumentResponse`

### `GET /api/v1/documents/{document_id}`
Get document metadata and status.
- **Header**: `Authorization: Bearer <token>`
- **Response**: `200 OK` with `DocumentResponse`

### `GET /api/v1/documents/{document_id}/chunks`
Inspect all extracted chunks, character offsets, and metadata payloads for a document.
- **Header**: `Authorization: Bearer <token>`
- **Response**: `200 OK`
  ```json
  [
    {
      "id": "5a018a4b-324f-4a66-86d0-e9f44d2c10a8",
      "document_id": "70d3abe3-8688-4133-8400-7b14efee73d7",
      "project_id": "0a87fed5-cd2c-415c-a5c8-54a42f32bff3",
      "chunk_index": 0,
      "text_content": "AVOM is an evaluation-first RAG engineering platform...",
      "start_char": 0,
      "end_char": 482,
      "metadata_json": {
        "source": "security_whitepaper.pdf",
        "page_number": 1,
        "strategy": "recursive"
      },
      "vector_id": "5a018a4b-324f-4a66-86d0-e9f44d2c10a8",
      "created_at": "2026-09-27T08:45:01Z"
    }
  ]
  ```

### `DELETE /api/v1/documents/{document_id}`
Delete a document and cascade deletion to its stored database chunks and Qdrant vector index.
- **Header**: `Authorization: Bearer <token>`
- **Response**: `204 No Content`

---

## 5. RAG Query Engine

- `POST /api/v1/query`: Execute RAG query

Request Payload:
```json
{
  "project_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
  "query": "What is the emergency leave policy?",
  "configuration": {
    "retrieval_type": "hybrid",
    "top_k": 20,
    "reranking": true,
    "reranker_model": "BAAI/bge-reranker-base",
    "final_context_k": 5,
    "llm_model": "gpt-4o-mini",
    "temperature": 0.0
  }
}
```

Response Payload:
```json
{
  "answer": "Employees are eligible for up to 15 days of paid emergency leave...",
  "sources": [
    {
      "citation_id": 1,
      "document_id": "doc-01",
      "filename": "policy.pdf",
      "chunk_id": "chk-12",
      "page": 14
    }
  ],
  "retrieved_chunks": [
    {
      "chunk_id": "chk-12",
      "text": "...",
      "dense_score": 0.88,
      "sparse_score": 0.74,
      "rerank_score": 0.94,
      "rank": 1
    }
  ],
  "trace_id": "tr-98124",
  "latency_ms": 540
}
```

---

## 6. Datasets & Ground Truth QA

### `POST /api/v1/datasets`
Create a new evaluation dataset within a project workspace.
- **Request Body**:
  ```json
  {
    "project_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "name": "Core Architecture QA Suite",
    "description": "Standard benchmark QA dataset"
  }
  ```
- **Response**: `201 Created`

### `GET /api/v1/datasets`
List all evaluation datasets in a project workspace.
- **Query Parameter**: `project_id`
- **Response**: `200 OK` List of `EvaluationDatasetResponse`

### `POST /api/v1/datasets/{dataset_id}/examples`
Bulk add ground truth QA pairs to an evaluation dataset.
- **Request Body**:
  ```json
  {
    "examples": [
      {
        "query": "What database does AVOM use for vector search?",
        "ground_truth": "AVOM uses Qdrant for vector search.",
        "ground_truth_context": "Qdrant powers vector embeddings and similarity search."
      }
    ]
  }
  ```
- **Response**: `201 Created`

### `GET /api/v1/datasets/{dataset_id}/examples`
List all ground truth examples for a dataset.
- **Response**: `200 OK`

### `DELETE /api/v1/datasets/{dataset_id}`
Delete a dataset and cascade deletion to all its examples.
- **Response**: `204 No Content`

---

## 7. Evaluations & LLM-as-a-Judge

### `POST /api/v1/evaluations/run`
Trigger an automated evaluation run executing RAG queries over every QA example in a dataset and calculating retrieval metrics (Recall@K, Precision@K, MRR, NDCG@K, HitRate@K) and generation metrics via LLM-as-a-judge (Faithfulness, Answer Relevance, Context Recall).
- **Request Body**:
  ```json
  {
    "project_id": "3fa85f64-5717-4562-b3fc-2c963f66afa6",
    "dataset_id": "306386c4-e6e2-4bee-bcd1-520c6e15d328",
    "name": "Hybrid + BGE Reranker Experiment",
    "configuration": {
      "retrieval_type": "hybrid",
      "top_k": 10,
      "reranking": true,
      "final_context_k": 3,
      "llm_model": "local-deterministic"
    }
  }
  ```
- **Response**: `201 Created` with full `EvaluationRunDetailResponse` (aggregate scorecards + per-example result items).

### `GET /api/v1/evaluations`
List all evaluation runs logged in a workspace.
- **Query Parameter**: `project_id`
- **Response**: `200 OK`

### `GET /api/v1/evaluations/{run_id}`
Retrieve a specific evaluation run with its full item breakdown and scorecard.
- **Response**: `200 OK`

---

## 8. Experiments & Head-to-Head Comparisons

### `GET /api/v1/experiments/compare`
Compare 2 to 4 evaluation runs side-by-side with a metric matrix and delta calculations against a baseline.
- **Query Parameters**:
  - `run_ids`: List of run IDs (e.g. `?run_ids=run-1&run_ids=run-2`)
  - `baseline_id`: Optional run ID to compute deltas against (defaults to first run)
- **Response**: `200 OK`
  ```json
  {
    "runs": [...],
    "metric_keys": ["recall@k", "precision@k", "mrr", "ndcg@k", "faithfulness", "answer_relevance", "latency_ms"],
    "matrix": {
      "run-1": {"recall@k": 0.72, "faithfulness": 0.89},
      "run-2": {"recall@k": 0.89, "faithfulness": 0.95}
    },
    "deltas": {
      "run-2": {"recall@k": 0.17, "faithfulness": 0.06}
    }
  }
  ```

---

## 9. Observability & Tracing

### `GET /api/v1/traces`
List OpenTelemetry-compatible query execution traces with latency and token breakdowns.
- **Query Parameters**: `project_id`, `limit`, `skip`
- **Response**: `200 OK` List of `TraceRecordResponse`

### `GET /api/v1/traces/{trace_id}`
Retrieve waterfall child spans (`query_embedding`, `retrieval`, `cross_encoder_rerank`, `prompt_construction`, `llm_synthesis`) for a specific trace.
- **Response**: `200 OK`

---

## 10. System Dashboard & Telemetry

### `GET /api/v1/dashboard/stats`
Aggregated system telemetry: total projects, documents, chunks, evaluation runs, query traces, average latency, and average faithfulness.
- **Response**: `200 OK`


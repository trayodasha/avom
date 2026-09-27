import pytest
from httpx import AsyncClient
from tests.test_ingestion import create_user_project


@pytest.mark.asyncio
async def test_dataset_crud_and_evaluations(client: AsyncClient):
    token, project_id = await create_user_project(client, "eval_user@avom.ai")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Upload a document so the project has retrievable knowledge
    doc_text = (
        "PostgreSQL is used as the relational metadata database in AVOM. "
        "Qdrant powers vector embeddings and similarity search using cosine metric. "
        "BM25 provides exact keyword and token frequency matching. "
        "Reciprocal Rank Fusion merges dense and sparse results seamlessly."
    )
    upload_res = await client.post(
        "/api/v1/documents/upload",
        headers=headers,
        data={
            "project_id": project_id,
            "chunking_strategy": "fixed",
            "chunk_size": 150,
            "chunk_overlap": 20,
        },
        files={"file": ("tech_stack.txt", doc_text.encode("utf-8"), "text/plain")},
    )
    assert upload_res.status_code == 201

    # 2. Create Evaluation Dataset
    ds_res = await client.post(
        "/api/v1/datasets",
        headers=headers,
        json={
            "project_id": project_id,
            "name": "Core Architecture QA Suite",
            "description": "Standard benchmark QA dataset for AVOM"
        }
    )
    assert ds_res.status_code == 201
    dataset_id = ds_res.json()["id"]

    # 3. Add Examples to Dataset
    examples_payload = {
        "examples": [
            {
                "query": "What database does AVOM use for vector search?",
                "ground_truth": "AVOM uses Qdrant for vector search.",
                "ground_truth_context": "Qdrant powers vector embeddings and similarity search."
            },
            {
                "query": "What is used for relational metadata in AVOM?",
                "ground_truth": "PostgreSQL is used for relational metadata in AVOM.",
                "ground_truth_context": "PostgreSQL is used as the relational metadata database in AVOM."
            }
        ]
    }
    ex_res = await client.post(
        f"/api/v1/datasets/{dataset_id}/examples",
        headers=headers,
        json=examples_payload
    )
    assert ex_res.status_code == 201
    assert len(ex_res.json()) == 2

    # 4. Trigger an Evaluation Run
    run_payload = {
        "project_id": project_id,
        "dataset_id": dataset_id,
        "name": "Baseline Hybrid + Local Deterministic Run",
        "configuration": {
            "retrieval_type": "hybrid",
            "top_k": 5,
            "reranking": True,
            "final_context_k": 3,
            "llm_model": "local-deterministic"
        }
    }
    eval_res = await client.post(
        "/api/v1/evaluations/run",
        headers=headers,
        json=run_payload
    )
    assert eval_res.status_code == 201
    run_data = eval_res.json()
    assert run_data["status"] == "COMPLETED"
    assert run_data["total_examples"] == 2
    assert run_data["processed_examples"] == 2
    assert "aggregate_metrics" in run_data
    assert "faithfulness" in run_data["aggregate_metrics"]
    assert "answer_relevance" in run_data["aggregate_metrics"]
    assert len(run_data["results"]) == 2

    run_id_1 = run_data["id"]

    # 5. Trigger a second run with different configuration for experiment comparison
    run_payload_2 = {
        "project_id": project_id,
        "dataset_id": dataset_id,
        "name": "Dense Only Run",
        "configuration": {
            "retrieval_type": "dense",
            "top_k": 3,
            "reranking": False,
            "final_context_k": 2,
            "llm_model": "local-deterministic"
        }
    }
    eval_res_2 = await client.post(
        "/api/v1/evaluations/run",
        headers=headers,
        json=run_payload_2
    )
    assert eval_res_2.status_code == 201
    run_id_2 = eval_res_2.json()["id"]

    # 6. Compare Experiments
    compare_res = await client.get(
        f"/api/v1/experiments/compare?run_ids={run_id_1}&run_ids={run_id_2}",
        headers=headers
    )
    assert compare_res.status_code == 200
    comp_data = compare_res.json()
    assert len(comp_data["runs"]) == 2
    assert run_id_1 in comp_data["matrix"]
    assert run_id_2 in comp_data["matrix"]
    assert "deltas" in comp_data

    # 7. Check Traces
    traces_res = await client.get(
        f"/api/v1/traces?project_id={project_id}",
        headers=headers
    )
    assert traces_res.status_code == 200
    traces = traces_res.json()
    assert len(traces) >= 2  # Traces recorded during eval queries

    # 8. Check Dashboard Stats
    stats_res = await client.get("/api/v1/dashboard/stats", headers=headers)
    assert stats_res.status_code == 200
    stats = stats_res.json()
    assert stats["total_projects"] >= 1
    assert stats["total_documents"] >= 1
    assert stats["total_evaluations"] >= 2

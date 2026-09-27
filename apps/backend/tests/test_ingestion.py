import io
import pytest
from httpx import AsyncClient
from pypdf import PdfWriter


async def create_user_project(client: AsyncClient, email: str = "ingest_user@avom.ai") -> tuple[str, str]:
    await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "Password123!",
        "full_name": "Ingestion Tester"
    })
    login_res = await client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "Password123!"
    })
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    proj_res = await client.post("/api/v1/projects", json={
        "name": "Ingestion Project Workspace",
        "description": "Workspace for document ingestion testing"
    }, headers=headers)
    project_id = proj_res.json()["id"]

    return token, project_id


def generate_simple_pdf(text: str) -> bytes:
    writer = PdfWriter()
    writer.add_blank_page(width=200, height=200)
    buf = io.BytesIO()
    writer.write(buf)
    return buf.getvalue()


@pytest.mark.asyncio
async def test_upload_txt_document(client: AsyncClient):
    token, project_id = await create_user_project(client, "txt_user@avom.ai")
    headers = {"Authorization": f"Bearer {token}"}

    content = b"AVOM is an evaluation-first RAG engineering platform. It supports hybrid retrieval with BM25."
    files = {"file": ("test_rag_architecture.txt", content, "text/plain")}
    data = {
        "project_id": project_id,
        "chunking_strategy": "recursive",
        "chunk_size": "50",
        "chunk_overlap": "10",
        "embedding_model": "bge-small-en-v1.5",
    }

    res = await client.post("/api/v1/documents/upload", files=files, data=data, headers=headers)
    assert res.status_code == 201
    doc_data = res.json()
    assert doc_data["filename"] == "test_rag_architecture.txt"
    assert doc_data["status"] == "INDEXED"
    assert doc_data["chunk_count"] >= 1
    doc_id = doc_data["id"]

    # Retrieve chunks for this document
    chunks_res = await client.get(f"/api/v1/documents/{doc_id}/chunks", headers=headers)
    assert chunks_res.status_code == 200
    chunks = chunks_res.json()
    assert len(chunks) == doc_data["chunk_count"]
    assert "AVOM is an evaluation-first" in chunks[0]["text_content"]


@pytest.mark.asyncio
async def test_upload_markdown_document(client: AsyncClient):
    token, project_id = await create_user_project(client, "md_user@avom.ai")
    headers = {"Authorization": f"Bearer {token}"}

    md_content = b"""# Architecture Guide
## Retrieval Pipeline
Hybrid retrieval fuses dense Qdrant vector scores with sparse BM25 scores.
## Reranker
BAAI/bge-reranker-base reorders top candidate chunks.
"""
    files = {"file": ("guide.md", md_content, "text/markdown")}
    data = {
        "project_id": project_id,
        "chunking_strategy": "fixed",
        "chunk_size": "80",
        "chunk_overlap": "15"
    }

    res = await client.post("/api/v1/documents/upload", files=files, data=data, headers=headers)
    assert res.status_code == 201
    assert res.json()["status"] == "INDEXED"


@pytest.mark.asyncio
async def test_upload_duplicate_checksum_fails(client: AsyncClient):
    token, project_id = await create_user_project(client, "dup_user@avom.ai")
    headers = {"Authorization": f"Bearer {token}"}

    content = b"Unique content for duplicate checksum test."
    files = {"file": ("doc.txt", content, "text/plain")}
    data = {"project_id": project_id}

    res1 = await client.post("/api/v1/documents/upload", files=files, data=data, headers=headers)
    assert res1.status_code == 201

    files2 = {"file": ("doc_copy.txt", content, "text/plain")}
    res2 = await client.post("/api/v1/documents/upload", files=files2, data=data, headers=headers)
    assert res2.status_code == 409
    assert "matching checksum already exists" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_upload_unsupported_extension_fails(client: AsyncClient):
    token, project_id = await create_user_project(client, "unsupp_user@avom.ai")
    headers = {"Authorization": f"Bearer {token}"}

    files = {"file": ("malware.exe", b"binary content", "application/octet-stream")}
    data = {"project_id": project_id}

    res = await client.post("/api/v1/documents/upload", files=files, data=data, headers=headers)
    assert res.status_code == 400
    assert "Unsupported file extension" in res.json()["detail"]


@pytest.mark.asyncio
async def test_list_and_delete_document(client: AsyncClient):
    token, project_id = await create_user_project(client, "del_user@avom.ai")
    headers = {"Authorization": f"Bearer {token}"}

    # Upload document
    files = {"file": ("to_delete.txt", b"Document content to delete", "text/plain")}
    data = {"project_id": project_id}
    upload_res = await client.post("/api/v1/documents/upload", files=files, data=data, headers=headers)
    assert upload_res.status_code == 201
    doc_id = upload_res.json()["id"]

    # List documents for project
    list_res = await client.get(f"/api/v1/documents?project_id={project_id}", headers=headers)
    assert list_res.status_code == 200
    docs = list_res.json()
    assert len(docs) == 1
    assert docs[0]["id"] == doc_id

    # Delete document
    del_res = await client.delete(f"/api/v1/documents/{doc_id}", headers=headers)
    assert del_res.status_code == 204

    # Verify not found
    get_res = await client.get(f"/api/v1/documents/{doc_id}", headers=headers)
    assert get_res.status_code == 404

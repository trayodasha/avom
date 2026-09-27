import pytest
from httpx import AsyncClient


async def create_user_and_get_token(client: AsyncClient, email: str, role: str = "USER") -> str:
    await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "Password123!",
        "role": role,
        "full_name": f"User {email}"
    })
    login_res = await client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "Password123!"
    })
    return login_res.json()["access_token"]


@pytest.mark.asyncio
async def test_create_and_get_project(client: AsyncClient):
    token = await create_user_and_get_token(client, "proj_owner@avom.ai")
    headers = {"Authorization": f"Bearer {token}"}

    # Create project
    create_payload = {
        "name": "Customer Support RAG",
        "description": "Knowledge base for tier 1 and tier 2 support docs."
    }
    create_res = await client.post("/api/v1/projects", json=create_payload, headers=headers)
    assert create_res.status_code == 201
    project_data = create_res.json()
    assert project_data["name"] == "Customer Support RAG"
    assert "id" in project_data
    project_id = project_data["id"]

    # Get project by ID
    get_res = await client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert get_res.status_code == 200
    assert get_res.json()["id"] == project_id


@pytest.mark.asyncio
async def test_list_projects_isolation(client: AsyncClient):
    token_a = await create_user_and_get_token(client, "alice@avom.ai")
    token_b = await create_user_and_get_token(client, "bob@avom.ai")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Alice creates 2 projects
    await client.post("/api/v1/projects", json={"name": "Alice Project 1"}, headers=headers_a)
    await client.post("/api/v1/projects", json={"name": "Alice Project 2"}, headers=headers_a)

    # Bob creates 1 project
    await client.post("/api/v1/projects", json={"name": "Bob Project 1"}, headers=headers_b)

    # Alice lists projects -> should only see 2
    res_a = await client.get("/api/v1/projects", headers=headers_a)
    assert res_a.status_code == 200
    projects_a = res_a.json()
    assert len(projects_a) == 2
    assert all(p["name"].startswith("Alice") for p in projects_a)

    # Bob lists projects -> should only see 1
    res_b = await client.get("/api/v1/projects", headers=headers_b)
    assert res_b.status_code == 200
    projects_b = res_b.json()
    assert len(projects_b) == 1
    assert projects_b[0]["name"] == "Bob Project 1"


@pytest.mark.asyncio
async def test_project_cross_user_access_forbidden(client: AsyncClient):
    token_a = await create_user_and_get_token(client, "owner_a@avom.ai")
    token_b = await create_user_and_get_token(client, "intruder_b@avom.ai")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # User A creates a project
    create_res = await client.post(
        "/api/v1/projects",
        json={"name": "Confidential Research"},
        headers=headers_a
    )
    project_id = create_res.json()["id"]

    # User B attempts to read User A's project -> 403 Forbidden
    res_get = await client.get(f"/api/v1/projects/{project_id}", headers=headers_b)
    assert res_get.status_code == 403

    # User B attempts to update User A's project -> 403 Forbidden
    res_put = await client.put(
        f"/api/v1/projects/{project_id}",
        json={"name": "Tampered Name"},
        headers=headers_b
    )
    assert res_put.status_code == 403

    # User B attempts to delete User A's project -> 403 Forbidden
    res_del = await client.delete(f"/api/v1/projects/{project_id}", headers=headers_b)
    assert res_del.status_code == 403


@pytest.mark.asyncio
async def test_update_and_delete_project(client: AsyncClient):
    token = await create_user_and_get_token(client, "lifecycle_user@avom.ai")
    headers = {"Authorization": f"Bearer {token}"}

    # Create
    create_res = await client.post(
        "/api/v1/projects",
        json={"name": "Initial Name", "description": "Initial Desc"},
        headers=headers
    )
    project_id = create_res.json()["id"]

    # Update
    update_res = await client.put(
        f"/api/v1/projects/{project_id}",
        json={"name": "Updated Name", "description": "Updated Desc"},
        headers=headers
    )
    assert update_res.status_code == 200
    assert update_res.json()["name"] == "Updated Name"

    # Delete
    del_res = await client.delete(f"/api/v1/projects/{project_id}", headers=headers)
    assert del_res.status_code == 204

    # Verify not found after delete
    verify_res = await client.get(f"/api/v1/projects/{project_id}", headers=headers)
    assert verify_res.status_code == 404

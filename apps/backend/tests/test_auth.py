import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_user_success(client: AsyncClient):
    payload = {
        "email": "engineer@avom.ai",
        "password": "strongPassword123!",
        "full_name": "RAG Engineer",
        "role": "USER"
    }
    response = await client.post("/api/v1/auth/register", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "engineer@avom.ai"
    assert data["full_name"] == "RAG Engineer"
    assert data["role"] == "USER"
    assert "id" in data
    assert "password" not in data
    assert "hashed_password" not in data


@pytest.mark.asyncio
async def test_register_duplicate_email_fails(client: AsyncClient):
    payload = {
        "email": "duplicate@avom.ai",
        "password": "password123",
        "full_name": "First User"
    }
    res1 = await client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = await client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 409
    assert "already exists" in res2.json()["detail"]


@pytest.mark.asyncio
async def test_login_success_and_token_issue(client: AsyncClient):
    # Register user
    reg_payload = {
        "email": "login_test@avom.ai",
        "password": "correctPassword",
        "full_name": "Tester"
    }
    await client.post("/api/v1/auth/register", json=reg_payload)

    # Login
    login_payload = {
        "email": "login_test@avom.ai",
        "password": "correctPassword"
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "login_test@avom.ai"


@pytest.mark.asyncio
async def test_login_wrong_password_fails(client: AsyncClient):
    reg_payload = {
        "email": "wrong_pw@avom.ai",
        "password": "actualPassword",
    }
    await client.post("/api/v1/auth/register", json=reg_payload)

    login_payload = {
        "email": "wrong_pw@avom.ai",
        "password": "wrongPassword"
    }
    response = await client.post("/api/v1/auth/login", json=login_payload)
    assert response.status_code == 401
    assert "Incorrect email or password" in response.json()["detail"]


@pytest.mark.asyncio
async def test_get_current_user_me_protected(client: AsyncClient):
    # Register and login
    email = "profile_test@avom.ai"
    await client.post("/api/v1/auth/register", json={
        "email": email,
        "password": "password123",
        "full_name": "Profile Owner"
    })
    login_res = await client.post("/api/v1/auth/login", json={
        "email": email,
        "password": "password123"
    })
    token = login_res.json()["access_token"]

    # 1. Unauthenticated request to /me
    unauth_res = await client.get("/api/v1/auth/me")
    assert unauth_res.status_code == 401

    # 2. Authenticated request with Bearer token
    headers = {"Authorization": f"Bearer {token}"}
    auth_res = await client.get("/api/v1/auth/me", headers=headers)
    assert auth_res.status_code == 200
    user_data = auth_res.json()
    assert user_data["email"] == email
    assert user_data["full_name"] == "Profile Owner"


@pytest.mark.asyncio
async def test_role_based_authorization(client: AsyncClient):
    # 1. Register a standard USER
    user_email = "regular_user@avom.ai"
    await client.post("/api/v1/auth/register", json={
        "email": user_email,
        "password": "password123",
        "role": "USER"
    })
    user_login = await client.post("/api/v1/auth/login", json={
        "email": user_email,
        "password": "password123"
    })
    user_token = user_login.json()["access_token"]

    # Regular user attempting admin route should receive 403 Forbidden
    res_user = await client.get(
        "/api/v1/auth/admin-only",
        headers={"Authorization": f"Bearer {user_token}"}
    )
    assert res_user.status_code == 403
    assert "Required role: ADMIN" in res_user.json()["detail"]

    # 2. Register an ADMIN user
    admin_email = "admin_user@avom.ai"
    await client.post("/api/v1/auth/register", json={
        "email": admin_email,
        "password": "password123",
        "role": "ADMIN"
    })
    admin_login = await client.post("/api/v1/auth/login", json={
        "email": admin_email,
        "password": "password123"
    })
    admin_token = admin_login.json()["access_token"]

    # Admin user accessing admin route should receive 200 OK
    res_admin = await client.get(
        "/api/v1/auth/admin-only",
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_admin.status_code == 200
    assert "Role verified" in res_admin.json()["message"]

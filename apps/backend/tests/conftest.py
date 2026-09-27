import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
import app.models  # Ensure models are registered on Base.metadata
from app.core.database import engine, Base
from app.main import app as fastapi_app


@pytest_asyncio.fixture(autouse=True)
async def prepare_database():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

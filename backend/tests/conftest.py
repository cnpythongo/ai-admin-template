from __future__ import annotations

from collections.abc import AsyncGenerator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings
from app.db.session import get_db
from app.main import app

# Use test database
TEST_DATABASE_URL = settings.DATABASE_URL

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture
async def db_session() -> AsyncGenerator[AsyncSession]:
    """Provide a test database session."""
    async with TestSessionLocal() as session:
        yield session


@pytest_asyncio.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient]:
    """Provide an HTTP client with test DB dependency override."""

    async def override_get_db() -> AsyncGenerator[AsyncSession]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(client: AsyncClient, db_session: AsyncSession) -> dict[str, str]:
    """Create a default admin user and return auth headers."""
    from app.core.security import hash_password
    from app.models.user import User

    # Create a test superuser
    user = User(
        username="admin",
        password_hash=hash_password("admin123"),
        nickname="Admin",
        is_superuser=True,
        status=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # Login to get token
    response = await client.post("/api/v1/auth/login", json={
        "username": "admin",
        "password": "admin123",
    })
    data = response.json()
    token = data["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def normal_user_headers(client: AsyncClient, db_session: AsyncSession) -> dict[str, str]:
    """Create a normal (non-superuser) user and return auth headers."""
    from app.core.security import hash_password
    from app.models.user import User

    user = User(
        username="normaluser",
        password_hash=hash_password("test123456"),
        nickname="Normal User",
        is_superuser=False,
        status=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    response = await client.post("/api/v1/auth/login", json={
        "username": "normaluser",
        "password": "test123456",
    })
    data = response.json()
    token = data["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}

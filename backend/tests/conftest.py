import os
from pathlib import Path

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text


BACKEND_DIR = Path(__file__).resolve().parents[1]

# This MUST happen before FactoryPulse modules are imported.
os.environ["FACTORYPULSE_ENV_FILE"] = str(
    BACKEND_DIR / ".env.test"
)


import app.models  # noqa: E402, F401
from app.core.security import create_access_token, hash_password  # noqa: E402
from app.db.base import Base  # noqa: E402
from app.db.session import AsyncSessionLocal, engine  # noqa: E402
from app.main import app  # noqa: E402
from app.models.role import Role  # noqa: E402
from app.models.user import User  # noqa: E402


@pytest_asyncio.fixture(autouse=True)
async def reset_test_database():
    async with engine.begin() as connection:
        await connection.execute(
            text(
                "CREATE EXTENSION IF NOT EXISTS btree_gist"
            )
        )

        await connection.run_sync(
            Base.metadata.drop_all
        )

        await connection.run_sync(
            Base.metadata.create_all
        )

    yield

    async with engine.begin() as connection:
        await connection.run_sync(
            Base.metadata.drop_all
        )

    await engine.dispose()


@pytest_asyncio.fixture
async def client() -> AsyncClient:
    transport = ASGITransport(app=app)

    async with AsyncClient(
        transport=transport,
        base_url="http://test",
    ) as test_client:
        yield test_client


@pytest_asyncio.fixture
async def auth_headers() -> dict[str, dict[str, str]]:
    async with AsyncSessionLocal() as db:
        admin_role = Role(
            name="admin",
            description="Test administrator",
        )

        manager_role = Role(
            name="manager",
            description="Test manager",
        )

        technician_role = Role(
            name="technician",
            description="Test technician",
        )

        operator_role = Role(
            name="operator",
            description="Test operator",
        )

        db.add_all([
            admin_role,
            manager_role,
            technician_role,
            operator_role,
        ])

        await db.flush()

        admin_user = User(
            email="admin@test.factorypulse.local",
            full_name="Test Administrator",
            hashed_password=hash_password("test-admin-password"),
            role_id=admin_role.id,
            is_active=True,
        )

        manager_user = User(
            email="manager@test.factorypulse.local",
            full_name="Test Manager",
            hashed_password=hash_password("test-manager-password"),
            role_id=manager_role.id,
            is_active=True,
        )

        technician_user = User(
            email="technician@test.factorypulse.local",
            full_name="Test Technician",
            hashed_password=hash_password("test-technician-password"),
            role_id=technician_role.id,
            is_active=True,
        )

        operator_user = User(
            email="operator@test.factorypulse.local",
            full_name="Test Operator",
            hashed_password=hash_password("test-operator-password"),
            role_id=operator_role.id,
            is_active=True,
        )

        db.add_all([
            admin_user,
            manager_user,
            technician_user,
            operator_user,
        ])

        await db.commit()

        for user in (
            admin_user,
            manager_user,
            technician_user,
            operator_user,
        ):
            await db.refresh(user)

        return {
            "admin": {
                "Authorization": (
                    f"Bearer {create_access_token(subject=str(admin_user.id))}"
                )
            },
            "manager": {
                "Authorization": (
                    f"Bearer {create_access_token(subject=str(manager_user.id))}"
                )
            },
            "technician": {
                "Authorization": (
                    f"Bearer {create_access_token(subject=str(technician_user.id))}"
                )
            },
            "operator": {
                "Authorization": (
                    f"Bearer {create_access_token(subject=str(operator_user.id))}"
                )
            },
        }
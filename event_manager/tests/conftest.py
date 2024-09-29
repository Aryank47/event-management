import asyncio
import logging
from typing import AsyncGenerator
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils import create_database, database_exists, drop_database

from event_manager.core.config import settings
from event_manager.core.database import create_sessionmaker, with_session
from event_manager.keycloak.utils import validate_and_parse_token
from event_manager.main import app
from event_manager.models import Base

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session", autouse=True)
def event_loop(request):
    """Create an instance of the default event loop for each test case."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


def create_test_database():
    """Creates the test database and tables using a synchronous connection."""

    # Create a synchronous engine using the same URL as your async engine
    logger.info("Creating SYNC ENGINE for db creation...")
    sync_engine = create_engine(settings.TEST_SYNC_DATABASE_URL)
    logger.info("Completed Creating SYNC ENGINE for db creation...")

    if not database_exists(sync_engine.url):
        logger.info("Creating test database...")
        create_database(sync_engine.url)
        logger.info("Test database created successfully.")

        # Create tables using the synchronous engine
        Base.metadata.create_all(sync_engine)


def drop_test_database():
    # Create a synchronous engine using the same URL as your async engine
    logger.info("Creating SYNC ENGINE for db deletion...")
    sync_engine = create_engine(settings.TEST_SYNC_DATABASE_URL)
    logger.info("Completed Creating SYNC ENGINE for db deletion...")

    if database_exists(sync_engine.url):
        logger.info("Dropping test database...")
        drop_database(sync_engine.url)
        logger.info("Test database dropped successfully.")


@pytest.fixture(scope="session", autouse=True)
async def engine() -> AsyncGenerator[AsyncEngine, None]:
    # Create the test database before the async engine is created
    create_test_database()

    engine = create_async_engine(
        settings.TEST_DATABASE_URL,
        # echo=True,  # For detailed logging of all SQL calls (turn off in production)
        connect_args={"timeout": 50},  # Timeout for trying to connect to the database
        future=True,
    )
    try:
        yield engine
    finally:
        drop_test_database()
        await engine.dispose()


@pytest.fixture(scope="session")
async def session_maker(engine) -> AsyncGenerator[AsyncSession, None]:
    return create_sessionmaker(engine)


@pytest.fixture(scope="session")
async def session(session_maker: sessionmaker) -> AsyncGenerator[AsyncSession, None]:
    async with session_maker() as session:
        yield session


@pytest_asyncio.fixture(scope="session")
async def client(session: AsyncSession):
    async def session_override() -> AsyncGenerator[AsyncSession, None]:
        yield session
        await session.close_all()

    async with AsyncClient(app=app, base_url="http://127.0.0.1:8080") as client:
        app.dependency_overrides[with_session] = session_override
        app.dependency_overrides[validate_and_parse_token] = lambda: {
            "realm_access": {
                "roles": [
                    "super_admin",
                    "offline_access",
                    "default-roles-event-manager",
                    "uma_authorization",
                ]
            },
        }
        yield client


@pytest.fixture(scope="session", autouse=True)
def mock_keycloak_user_creation():
    with patch(
        "event_manager.api.routes.user.create_keycloak_user", new_callable=AsyncMock
    ) as mock_create_user:
        with patch(
            "event_manager.api.routes.user.delete_keycloak_user", new_callable=AsyncMock
        ) as mock_delete_user:
            # Set up the mocks
            mock_create_user.return_value = "26061df0-0f9f-4a31-a6c5-512d01b216b2"
            mock_delete_user.return_value = None

            yield

"""Root test configuration and fixtures.

Provides:
- Session-scoped PostgreSQL testcontainer with pgvector
- Per-test async database session with automatic rollback
- Litestar test app and async HTTP client
- Factory session binding for factory_boy
"""

from __future__ import annotations

import os
import sys

# Ensure src/ is at the FRONT of sys.path to prevent tests/services/
# shadowing src/services/ (namespace package)
_src_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
if _src_dir not in sys.path:
    sys.path.insert(0, _src_dir)

# Load test env BEFORE any app imports to override settings
os.environ["ENV"] = "TEST"
os.environ["AUTH_ENABLED"] = "false"
os.environ["AUTH_ENABLED_FOR_SCHEMA"] = "false"
os.environ["DB_TYPE"] = "postgresql"
os.environ["DB_HOST"] = "localhost"
os.environ["DB_PORT"] = "5433"
os.environ["DB_NAME"] = "magnet_test"
os.environ["DB_USER"] = "postgres"
os.environ["DB_PASSWORD"] = "postgres"
os.environ["SECRET_ENCRYPTION_KEY"] = "test-secret-key-32-chars-long!!!"
os.environ["DEBUG_MODE"] = "false"
os.environ["VECTOR_DB_TYPE"] = "PGVECTOR"
os.environ["LOG_LEVEL"] = "30"
os.environ["LOKI_URL"] = ""
os.environ["WEB_INCLUDED"] = "false"
os.environ["STT_ENABLED"] = "false"

from collections.abc import AsyncGenerator  # noqa: E402

import pytest  # noqa: E402
from sqlalchemy import NullPool, text  # noqa: E402
from sqlalchemy.ext.asyncio import (  # noqa: E402
    AsyncEngine,
    AsyncSession,
    create_async_engine,
)


def _clear_settings_caches():
    """Clear all lru_cache'd settings so test env vars are picked up."""
    try:
        from core.config.base import (
            get_auth_settings,
            get_azure_settings,
            get_database_settings,
            get_general_settings,
            get_knowledge_source_settings,
            get_log_settings,
            get_observability_settings,
            get_scheduler_settings,
            get_settings,
            get_vector_database_settings,
        )

        for fn in [
            get_settings,
            get_general_settings,
            get_auth_settings,
            get_database_settings,
            get_log_settings,
            get_vector_database_settings,
            get_scheduler_settings,
            get_observability_settings,
            get_azure_settings,
            get_knowledge_source_settings,
        ]:
            fn.cache_clear()
    except ImportError:
        pass


# ---------------------------------------------------------------------------
# Session-scoped: one PostgreSQL container for the entire test run
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def postgres_container():
    """Start a disposable PostgreSQL + pgvector container."""
    from testcontainers.postgres import PostgresContainer

    with PostgresContainer(
        image="pgvector/pgvector:pg16",
        username="postgres",
        password="postgres",
        dbname="magnet_test",
    ) as pg:
        yield pg


@pytest.fixture(scope="session")
def db_url(postgres_container) -> str:
    """Build an asyncpg connection URL for the test container."""
    host = postgres_container.get_container_host_ip()
    port = postgres_container.get_exposed_port(5432)
    return f"postgresql+asyncpg://postgres:postgres@{host}:{port}/magnet_test"


@pytest.fixture(scope="session")
def _db_schema_initialized(db_url):
    """Synchronous marker: tracks whether the DB schema has been created.

    Returns the db_url so downstream fixtures can create engines in the
    correct event loop.
    """
    # Schema init happens lazily in the first engine fixture call
    return {"db_url": db_url, "initialized": False}


# ---------------------------------------------------------------------------
# Function-scoped engine + session (same event loop as the test)
# ---------------------------------------------------------------------------


@pytest.fixture
async def engine(_db_schema_initialized) -> AsyncGenerator[AsyncEngine, None]:
    """Per-test engine that lives in the test's event loop."""
    url = _db_schema_initialized["db_url"]
    eng = create_async_engine(url, echo=False, poolclass=NullPool)

    if not _db_schema_initialized["initialized"]:
        _clear_settings_caches()
        _import_all_models()

        from advanced_alchemy.base import UUIDv7AuditBase

        async with eng.begin() as conn:
            await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
            await conn.run_sync(UUIDv7AuditBase.metadata.create_all)

        _db_schema_initialized["initialized"] = True

    yield eng
    await eng.dispose()


@pytest.fixture
async def db_session(engine) -> AsyncGenerator[AsyncSession, None]:
    """Provide a per-test session that rolls back after each test."""
    async with engine.connect() as conn:
        trans = await conn.begin()
        session = AsyncSession(bind=conn, expire_on_commit=False)

        try:
            yield session
        finally:
            await session.close()
            if trans.is_active:
                await trans.rollback()


# ---------------------------------------------------------------------------
# Factory-boy session binding (only when db_session is used)
# ---------------------------------------------------------------------------


@pytest.fixture(autouse=True)
def _bind_factory_session(request):
    """Bind the test DB session to factory_boy factories (only when DB is used)."""
    if "db_session" not in request.fixturenames:
        return
    db_session = request.getfixturevalue("db_session")
    from tests.factories.base import BaseFactory

    BaseFactory._meta.sqlalchemy_session = db_session


# ---------------------------------------------------------------------------
# Litestar test app & HTTP client
# ---------------------------------------------------------------------------


@pytest.fixture
async def test_app(engine):
    """Build a Litestar app for E2E tests (no startup side-effects)."""
    from litestar import Litestar
    from litestar.plugins.problem_details import (
        ProblemDetailsConfig,
        ProblemDetailsPlugin,
    )
    from litestar.plugins.sqlalchemy import AsyncSessionConfig, SQLAlchemyAsyncConfig
    from advanced_alchemy.extensions.litestar import SQLAlchemyPlugin

    _clear_settings_caches()

    # Ensure src/ is first in path so imports resolve from src/
    if _src_dir not in sys.path or sys.path.index(_src_dir) > 0:
        if _src_dir in sys.path:
            sys.path.remove(_src_dir)
        sys.path.insert(0, _src_dir)

    from routes import get_route_handlers

    route_handlers = get_route_handlers(auth_enabled=False, web_included=False)

    test_alchemy_config = SQLAlchemyAsyncConfig(
        engine_instance=engine,
        before_send_handler="autocommit",
        session_config=AsyncSessionConfig(expire_on_commit=False),
    )

    alchemy_plugin = SQLAlchemyPlugin(config=test_alchemy_config)
    problem_details_plugin = ProblemDetailsPlugin(
        config=ProblemDetailsConfig(enable_for_all_http_exceptions=True)
    )

    from core.server.plugins import DependenciesPlugin

    app = Litestar(
        route_handlers=route_handlers,
        debug=True,
        plugins=[
            alchemy_plugin,
            problem_details_plugin,
            DependenciesPlugin(),
        ],
    )
    return app


@pytest.fixture
async def client(test_app) -> AsyncGenerator:
    """Async HTTP test client."""
    from litestar.testing import AsyncTestClient

    async with AsyncTestClient(app=test_app) as c:
        yield c


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _import_all_models():
    """Import every model so metadata.create_all creates all tables."""
    import core.db.models  # noqa: F401
    import core.db.models.agent  # noqa: F401
    import core.db.models.agent_conversation  # noqa: F401
    import core.db.models.prompt  # noqa: F401
    import core.db.models.rag_tool  # noqa: F401
    import core.db.models.retrieval_tool  # noqa: F401
    import core.db.models.api_server  # noqa: F401
    import core.db.models.api_tool  # noqa: F401
    import core.db.models.evaluation_set  # noqa: F401
    import core.db.models.mcp_server  # noqa: F401
    import core.db.models.knowledge_graph  # noqa: F401
    import core.db.models.prompt_queue  # noqa: F401
    import core.db.models.deep_research  # noqa: F401

    try:
        import core.db.models.slack  # noqa: F401
    except ImportError:
        pass
    try:
        import core.db.models.teams  # noqa: F401
    except ImportError:
        pass
    try:
        import core.db.models.transcription  # noqa: F401
    except ImportError:
        pass

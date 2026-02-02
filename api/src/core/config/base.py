from __future__ import annotations

import os
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final, cast

from litestar.data_extractors import RequestExtractorField
from litestar.serialization import decode_json, encode_json
from litestar.utils.module_loader import module_to_os_path
from sqlalchemy import event
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine
from sqlalchemy.pool import NullPool

from ._utils import get_env


def json_serializer_for_sqlalchemy(obj: Any) -> str:
    """
    Wrapper for encode_json that returns str instead of bytes for SQLAlchemy.
    SQLAlchemy expects json_serializer to return str, not bytes.
    """
    result = encode_json(obj)
    if isinstance(result, bytes):
        return result.decode("utf-8")
    elif isinstance(result, (bytearray, memoryview)):
        return bytes(result).decode("utf-8")
    return str(result)


DEFAULT_MODULE_NAME = "app"
BASE_DIR: Final[Path] = module_to_os_path(DEFAULT_MODULE_NAME)

if TYPE_CHECKING:
    from collections.abc import Callable

    from litestar.data_extractors import ResponseExtractorField


#### GENERAL SETTINGS ####
@dataclass
class GeneralSettings:
    """General application configuration"""

    """Environment name."""
    ENV: str = field(default_factory=get_env("ENV", ""))

    """Default text when no answer is available."""
    NO_ANSWER_TEXT: str = field(
        default_factory=get_env(
            "NO_ANSWER_TEXT",
            "It seems that the answer to your question is not available in the resources I have access to. Please modify your question.",
        )
    )

    """Application port."""
    PORT: int = field(default_factory=get_env("PORT", 8000))

    """CORS allowed origins."""
    CORS_OVERRIDE_ALLOWED_ORIGINS: str = field(
        default_factory=get_env("CORS_OVERRIDE_ALLOWED_ORIGINS", "")
    )

    """Key used for encrypting secrets."""
    SECRET_ENCRYPTION_KEY: str = field(
        default_factory=get_env("SECRET_ENCRYPTION_KEY", "my-secret-key-tsmh5r")
    )


### DATABASE SETTINGS ###
@dataclass
class DatabaseSettings:
    """Enable SQLAlchemy engine logs."""

    ECHO: bool = field(default_factory=get_env("DATABASE_ECHO", True))
    """Enable SQLAlchemy connection pool logs."""
    ECHO_POOL: bool = field(default_factory=get_env("DATABASE_ECHO_POOL", True))
    """Enable detailed SQLAlchemy error logs."""
    ECHO_ERRORS: bool = field(default_factory=get_env("DATABASE_ECHO_ERRORS", True))
    """Disable SQLAlchemy pool configuration."""
    POOL_DISABLED: bool = field(
        default_factory=get_env("DATABASE_POOL_DISABLED", False)
    )
    """Max overflow for SQLAlchemy connection pool"""
    POOL_MAX_OVERFLOW: int = field(
        default_factory=get_env("DATABASE_MAX_POOL_OVERFLOW", 10)
    )
    """Pool size for SQLAlchemy connection pool"""
    POOL_SIZE: int = field(default_factory=get_env("DATABASE_POOL_SIZE", 5))
    """Time in seconds for timing connections out of the connection pool."""
    POOL_TIMEOUT: int = field(default_factory=get_env("DATABASE_POOL_TIMEOUT", 30))
    """Amount of time to wait before recycling connections."""
    POOL_RECYCLE: int = field(default_factory=get_env("DATABASE_POOL_RECYCLE", 300))
    """Optionally ping database before fetching a session from the connection pool."""
    POOL_PRE_PING: bool = field(
        default_factory=get_env("DATABASE_PRE_POOL_PING", False)
    )
    """SQLAlchemy Database URL."""
    URL: str = field(default_factory=get_env("DATABASE_URL", ""))
    """Database type (postgresql, mysql, sqlite, etc.)."""
    TYPE: str = field(default_factory=get_env("DB_TYPE", "postgresql"))
    """Database host."""
    HOST: str = field(default_factory=get_env("DB_HOST", "localhost"))
    """Database port."""
    PORT: str = field(default_factory=get_env("DB_PORT", "5432"))
    """Database name."""
    NAME: str = field(default_factory=get_env("DB_NAME", "test_magnet_ai"))
    """Database user."""
    USER: str = field(default_factory=get_env("DB_USER", "postgres"))
    """Database password."""
    PASSWORD: str = field(default_factory=get_env("DB_PASSWORD", "password"))
    """The path to the `alembic.ini` configuration file."""
    MIGRATION_CONFIG: str = field(
        default_factory=get_env(
            "DATABASE_MIGRATION_CONFIG", f"{BASE_DIR}/db/migrations/alembic.ini"
        )
    )
    """The path to the `alembic` database migrations."""
    MIGRATION_PATH: str = field(
        default_factory=get_env("DATABASE_MIGRATION_PATH", f"{BASE_DIR}/db/migrations")
    )
    """The name to use for the `alembic` versions table name."""
    MIGRATION_DDL_VERSION_TABLE: str = field(
        default_factory=get_env("DATABASE_MIGRATION_DDL_VERSION_TABLE", "ddl_version")
    )
    """The path to JSON fixture files to load into tables."""
    FIXTURE_PATH: str = field(
        default_factory=get_env("DATABASE_FIXTURE_PATH", f"{BASE_DIR}/db/fixtures")
    )
    _engine_instance: AsyncEngine | None = None
    """SQLAlchemy engine instance generated from settings."""

    def build_database_url(self) -> str:
        """Build database URL from individual components."""
        if not self.TYPE or not self.HOST:
            return ""

        # Map database types to their SQLAlchemy drivers
        driver_mapping = {
            "postgresql": "postgresql+asyncpg",
            "mysql": "mysql+aiomysql",
            "sqlite": "sqlite+aiosqlite",
            "oracle": "oracle+oracledb",
        }

        driver = driver_mapping.get(self.TYPE.lower(), self.TYPE)

        if self.TYPE.lower() == "sqlite":
            # SQLite doesn't use host/port/user/password
            db_name = self.NAME or "db.sqlite3"
            return f"{driver}:///{db_name}"

        # Build URL for other database types
        auth_part = ""
        if self.USER:
            if self.PASSWORD:
                auth_part = f"{self.USER}:{self.PASSWORD}@"
            else:
                auth_part = f"{self.USER}@"

        port_part = f":{self.PORT}" if self.PORT else ""
        db_part = f"/{self.NAME}" if self.NAME else ""

        return f"{driver}://{auth_part}{self.HOST}{port_part}{db_part}"

    @property
    def effective_url(self) -> str:
        """Get the effective database URL - either from DATABASE_URL or built from components."""
        # If DATABASE_URL is explicitly set to something other than default, use it
        if self.URL != "":
            return self.URL

        # Try to build URL from components
        built_url = self.build_database_url()
        if built_url:
            return built_url

        # Fall back to the default URL
        return self.URL

    @property
    def sync_url(self) -> str:
        """Get synchronous database URL for APScheduler (converts async drivers to sync)."""
        async_url = self.effective_url

        # Convert async drivers to sync for APScheduler
        if "postgresql+asyncpg://" in async_url:
            return async_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
        elif "mysql+aiomysql://" in async_url:
            return async_url.replace("mysql+aiomysql://", "mysql+pymysql://")
        elif "sqlite+aiosqlite://" in async_url:
            return async_url.replace("sqlite+aiosqlite://", "sqlite://")
        elif "oracle+oracledb://" in async_url:
            return async_url.replace("oracle+oracledb://", "oracle+cx_oracle://")

        # Return as-is if no async driver detected
        return async_url

    @property
    def engine(self) -> AsyncEngine:
        return self.get_engine()

    def get_engine(self) -> AsyncEngine:
        if self._engine_instance is not None:
            return self._engine_instance

        effective_url = self.effective_url
        if effective_url.startswith("postgresql+asyncpg"):
            engine = create_async_engine(
                url=effective_url,
                future=True,
                json_serializer=json_serializer_for_sqlalchemy,
                json_deserializer=decode_json,
                echo=self.ECHO,
                echo_pool=self.ECHO_POOL,
                max_overflow=self.POOL_MAX_OVERFLOW,
                pool_size=self.POOL_SIZE,
                pool_timeout=self.POOL_TIMEOUT,
                pool_recycle=self.POOL_RECYCLE,
                pool_pre_ping=self.POOL_PRE_PING,
                pool_use_lifo=True,  # use lifo to reduce the number of idle connections
                poolclass=NullPool if self.POOL_DISABLED else None,
            )
            """Database session factory.

            See [`async_sessionmaker()`][sqlalchemy.ext.asyncio.async_sessionmaker].
            """

        elif effective_url.startswith("sqlite+aiosqlite"):
            engine = create_async_engine(
                url=effective_url,
                future=True,
                json_serializer=json_serializer_for_sqlalchemy,
                json_deserializer=decode_json,
                echo=self.ECHO,
                echo_pool=self.ECHO_POOL,
                pool_recycle=self.POOL_RECYCLE,
                pool_pre_ping=self.POOL_PRE_PING,
            )
            """Database session factory.

            See [`async_sessionmaker()`][sqlalchemy.ext.asyncio.async_sessionmaker].
            """

            @event.listens_for(engine.sync_engine, "connect")
            def _sqla_on_connect(
                dbapi_connection: Any, _: Any
            ) -> Any:  # pragma: no cover
                """Override the default begin statement.  The disables the built in begin execution."""
                dbapi_connection.isolation_level = None

            @event.listens_for(engine.sync_engine, "begin")
            def _sqla_on_begin(dbapi_connection: Any) -> Any:  # pragma: no cover
                """Emits a custom begin"""
                dbapi_connection.exec_driver_sql("BEGIN")
        else:
            engine = create_async_engine(
                url=effective_url,
                future=True,
                json_serializer=json_serializer_for_sqlalchemy,
                json_deserializer=decode_json,
                echo=self.ECHO,
                echo_pool=self.ECHO_POOL,
                max_overflow=self.POOL_MAX_OVERFLOW,
                pool_size=self.POOL_SIZE,
                pool_timeout=self.POOL_TIMEOUT,
                pool_recycle=self.POOL_RECYCLE,
                pool_pre_ping=self.POOL_PRE_PING,
                pool_use_lifo=True,  # use lifo to reduce the number of idle connections
                poolclass=NullPool if self.POOL_DISABLED else None,
            )
        self._engine_instance = engine

        return self._engine_instance


@dataclass
class SchedulerSettings:
    """Scheduler pool settings"""

    SCHEDULER_POOL_SIZE: int = field(default_factory=get_env("SCHEDULER_POOL_SIZE", 10))
    """Scheduler connection pool size."""
    SCHEDULER_MAX_POOL_OVERFLOW: int = field(
        default_factory=get_env("SCHEDULER_MAX_POOL_OVERFLOW", 20)
    )
    """Scheduler connection pool max overflow."""
    SCHEDULER_POOL_TIMEOUT: int = field(
        default_factory=get_env("SCHEDULER_POOL_TIMEOUT", 30)
    )
    """Scheduler connection pool timeout."""
    SCHEDULER_POOL_RECYCLE: int = field(
        default_factory=get_env("SCHEDULER_POOL_RECYCLE", 3600)
    )
    """Scheduler connection pool recycle time."""
    SCHEDULER_POOL_PRE_PING: bool = field(
        default_factory=get_env("SCHEDULER_POOL_PRE_PING", True)
    )
    """Scheduler connection pool pre-ping."""

    def get_scheduler_database_url(self, db_settings: DatabaseSettings) -> str:
        """Get synchronous database URL for APScheduler jobstore."""
        return db_settings.sync_url

    def get_engine_options(self) -> dict:
        """Get SQLAlchemy engine options for APScheduler jobstore."""
        return {
            "pool_size": self.SCHEDULER_POOL_SIZE,
            "max_overflow": self.SCHEDULER_MAX_POOL_OVERFLOW,
            "pool_timeout": self.SCHEDULER_POOL_TIMEOUT,
            "pool_recycle": self.SCHEDULER_POOL_RECYCLE,
            "pool_pre_ping": self.SCHEDULER_POOL_PRE_PING,
            "echo": get_env("DATABASE_ECHO", False)(),
            "echo_pool": get_env("DATABASE_ECHO_POOL", False)(),
            "pool_reset_on_return": "commit",
        }


### LOGGING SETTINGS ###
@dataclass
class LogSettings:
    """Logger configuration"""

    """Enable debug mode and event loop debugging."""
    DEBUG_MODE: bool = field(default_factory=get_env("DEBUG_MODE", False))

    # https://stackoverflow.com/a/1845097/6560549
    """Regex to exclude paths from logging."""
    EXCLUDE_PATHS: str = r"\A(?!x)x"  # Not used
    """Log event name for logs from Litestar handlers."""
    HTTP_EVENT: str = "HTTP"  # Not used
    """Include 'body' of compressed responses in log output."""
    INCLUDE_COMPRESSED_BODY: bool = False  # Not used
    """Stdlib log levels.

    Only emit logs at this level, or higher.
    """
    LEVEL: int = field(default_factory=get_env("LOG_LEVEL", 10))
    """Request cookie keys to obfuscate."""
    OBFUSCATE_COOKIES: set[str] = field(
        default_factory=lambda: {"session", "XSRF-TOKEN"}
    )  # Not used
    """Request header keys to obfuscate."""
    OBFUSCATE_HEADERS: set[str] = field(
        default_factory=lambda: {"Authorization", "X-API-KEY", "X-XSRF-TOKEN"}
    )  # Not used
    """Attributes of the SAQ.

    [`Job`](https://github.com/tobymao/saq/blob/master/saq/job.py) to be
    logged.
    """
    JOB_FIELDS: list[str] = field(
        default_factory=lambda: [
            "function",
            "kwargs",
            "key",
            "scheduled",
            "attempts",
            "completed",
            "queued",
            "started",
            "result",
            "error",
        ],
    )  # Not used
    """Attributes of the [Request][litestar.connection.request.Request] to be
    logged."""
    REQUEST_FIELDS: list[RequestExtractorField] = field(
        default_factory=get_env(
            "LOG_REQUEST_FIELDS",
            [
                "path",
                "method",
                "query",
                "path_params",
            ],
            list[RequestExtractorField],
        ),
    )
    """Attributes of the [Response][litestar.response.Response] to be
    logged."""
    RESPONSE_FIELDS: list[ResponseExtractorField] = field(
        default_factory=cast(
            "Callable[[],list[ResponseExtractorField]]",
            get_env(
                "LOG_RESPONSE_FIELDS",
                ["status_code"],
            ),
        )
    )
    """Log event name for logs from SAQ worker."""
    WORKER_EVENT: str = "Worker"  # Not used
    """Level to log SAQ logs."""
    SAQ_LEVEL: int = field(default_factory=get_env("SAQ_LOG_LEVEL", 50))  # Not used
    """Level to log SQLAlchemy logs."""
    SQLALCHEMY_LEVEL: int = field(default_factory=get_env("SQLALCHEMY_LOG_LEVEL", 10))
    """Level to log uvicorn access logs."""
    ASGI_ACCESS_LEVEL: int = field(default_factory=get_env("ASGI_ACCESS_LOG_LEVEL", 10))
    """Level to log uvicorn error logs."""
    ASGI_ERROR_LEVEL: int = field(default_factory=get_env("ASGI_ERROR_LOG_LEVEL", 10))
    """Level to log Knowledge Graph logs."""
    KNOWLEDGE_GRAPH_LEVEL: int = field(
        default_factory=get_env("KNOWLEDGE_GRAPH_LOG_LEVEL", 10)
    )
    """Loki URL for sending logs (optional)."""
    LOKI_URL: str = field(default_factory=get_env("LOKI_URL", ""))


### OBSERVABILITY SETTINGS ###


@dataclass
class ObservabilitySettings:
    """Observability configuration"""

    ENABLED: bool = field(default_factory=get_env("OBSERVABILITY_ENABLED", True))
    """Enable observability features."""
    TRACES_EXPORTERS: str = field(
        default_factory=get_env("OBSERVABILITY_TRACES_EXPORTERS", "internal")
    )
    """Comma-separated list of traces exporters."""
    TRACES_MAX_EXPORT_BATCH_SIZE: int = field(
        default_factory=get_env("OBSERVABILITY_TRACES_MAX_EXPORT_BATCH_SIZE", 100)
    )
    """Maximum batch size for traces export."""
    USAGE_SHOW_USERS: bool = field(
        default_factory=get_env("OBSERVABILITY_USAGE_SHOW_USERS", True)
    )
    """Show users in usage statistics."""

    METRICS_EXPORTERS: str = field(
        default_factory=get_env("OBSERVABILITY_METRICS_EXPORTERS", "")
    )
    """Comma-separated list of metrics exporters."""
    METRICS_EXPORT_INTERVAL_MS: int = field(
        default_factory=get_env("OBSERVABILITY_METRICS_EXPORT_INTERVAL_MS", 3000)
    )
    """Metrics export interval in milliseconds."""


@dataclass
class AzureSettings:
    """Azure services configuration"""

    APPLICATIONINSIGHTS_CONNECTION_STRING: str = field(
        default_factory=get_env("APPLICATIONINSIGHTS_CONNECTION_STRING", "")
    )
    """Azure Application Insights connection string."""


### AUTHENTICATION SETTINGS ###


@dataclass
class AuthSettings:
    """Authentication configuration"""

    AUTH_ENABLED: bool = field(default_factory=get_env("AUTH_ENABLED", False))
    """Enable authentication."""
    MICROSOFT_ENTRA_ID_TENANT_ID: str = field(
        default_factory=get_env("MICROSOFT_ENTRA_ID_TENANT_ID", "")
    )
    """Microsoft Entra ID tenant ID."""
    MICROSOFT_ENTRA_ID_CLIENT_ID: str = field(
        default_factory=get_env("MICROSOFT_ENTRA_ID_CLIENT_ID", "")
    )
    """Microsoft Entra ID client ID."""
    MICROSOFT_ENTRA_ID_CLIENT_SECRET: str = field(
        default_factory=get_env("MICROSOFT_ENTRA_ID_CLIENT_SECRET", "")
    )
    """Microsoft Entra ID client secret."""
    MICROSOFT_ENTRA_ID_REDIRECT_URI: str = field(
        default_factory=get_env("MICROSOFT_ENTRA_ID_REDIRECT_URI", "")
    )
    """Microsoft Entra ID redirect URI."""


### VECTOR DATABASE SETTINGS ###


@dataclass
class VectorDatabaseSettings:
    """Database connection configuration"""

    VECTOR_DB_TYPE: str = field(default_factory=get_env("VECTOR_DB_TYPE", "PGVECTOR"))
    """Database type."""

    """PGVector database connection string."""
    PGVECTOR_HOST: str = field(default_factory=get_env("PGVECTOR_HOST", ""))
    """PGVector database host."""
    PGVECTOR_PORT: str = field(default_factory=get_env("PGVECTOR_PORT", ""))
    """PGVector database port."""
    PGVECTOR_DATABASE: str = field(default_factory=get_env("PGVECTOR_DATABASE", ""))
    """PGVector database name."""
    PGVECTOR_USER: str = field(default_factory=get_env("PGVECTOR_USER", ""))
    """PGVector database user."""
    PGVECTOR_PASSWORD: str = field(default_factory=get_env("PGVECTOR_PASSWORD", ""))
    """PGVector database password."""
    PGVECTOR_POOL_SIZE: int = field(default_factory=get_env("PGVECTOR_POOL_SIZE", 5))
    """PGVector connection pool size."""

    PGVECTOR_CONNECTION_STRING: str = field(
        default_factory=get_env("PGVECTOR_CONNECTION_STRING", "")
    )

    # Cosmos DB configuration

    COSMOS_DB_CONNECTION_STRING: str = field(
        default_factory=get_env("COSMOS_DB_CONNECTION_STRING", "")
    )
    """Cosmos DB connection string."""
    COSMOS_DB_DB_NAME: str = field(
        default_factory=get_env("COSMOS_DB_DB_NAME", "magnet-test")
    )
    """Cosmos DB database name."""

    # Oracle configuration
    ORACLE_HOST: str = field(default_factory=get_env("ORACLE_HOST", ""))
    """Oracle database host."""
    ORACLE_PASSWORD: str = field(default_factory=get_env("ORACLE_PASSWORD", ""))
    """Oracle database password."""
    ORACLE_PORT: int = field(default_factory=get_env("ORACLE_PORT", 1522))
    """Oracle database port."""
    ORACLE_USERNAME: str = field(default_factory=get_env("ORACLE_USERNAME", ""))
    """Oracle database username."""
    ORACLE_SERVICE_NAME: str = field(default_factory=get_env("ORACLE_SERVICE_NAME", ""))
    """Oracle database service name."""
    ORACLE_MONGO_CONNECTION_STRING: str = field(
        default_factory=get_env("ORACLE_MONGO_CONNECTION_STRING", "")
    )
    """Oracle MongoDB connection string."""

    # MongoDB configuration
    MONGO_DB_CONNECTION_STRING: str = field(
        default_factory=get_env("MONGO_DB_CONNECTION_STRING", "")
    )
    """MongoDB connection string."""
    MONGO_DB_DB_NAME: str = field(
        default_factory=get_env("MONGO_DB_DB_NAME", "magnet-dev")
    )
    """MongoDB database name."""

    # QDrant configuration
    DB_VECTOR_TYPE: str = field(default_factory=get_env("DB_VECTOR_TYPE", ""))
    """Vector database type."""
    QDRANT_DB_HOST: str = field(default_factory=get_env("QDRANT_DB_HOST", ""))
    """QDrant database host."""
    QDRANT_DB_API_KEY: str = field(default_factory=get_env("QDRANT_DB_API_KEY", ""))
    """QDrant database API key."""
    QDRANT_DB_PORT: int = field(default_factory=get_env("QDRANT_DB_PORT", 6333))
    """QDrant database port."""

    def apply_database_defaults(self, db_settings: DatabaseSettings) -> None:
        """
        Apply DatabaseSettings values to PGVECTOR settings if they are not explicitly set
        and the database type is PostgreSQL.
        """
        # Only apply defaults if database type is PostgreSQL
        if db_settings.TYPE.lower() != "postgresql":
            return

        # Check if PGVECTOR settings are not explicitly set via environment variables
        # If they are empty strings or default values, use DatabaseSettings values
        if not self.PGVECTOR_HOST or self.PGVECTOR_HOST == "localhost":
            self.PGVECTOR_HOST = db_settings.HOST

        if not self.PGVECTOR_PORT or self.PGVECTOR_PORT == "5432":
            self.PGVECTOR_PORT = db_settings.PORT

        if not self.PGVECTOR_DATABASE or self.PGVECTOR_DATABASE == "magnet_dev":
            self.PGVECTOR_DATABASE = db_settings.NAME

        if not self.PGVECTOR_USER or self.PGVECTOR_USER == "postgres":
            self.PGVECTOR_USER = db_settings.USER

        if not self.PGVECTOR_PASSWORD or self.PGVECTOR_PASSWORD == "password":
            self.PGVECTOR_PASSWORD = db_settings.PASSWORD

        if self.PGVECTOR_POOL_SIZE == 0:
            self.PGVECTOR_POOL_SIZE = db_settings.POOL_SIZE


### KNOWLEDGE SOURCE SETTINGS ###


@dataclass
class KnowledgeSourceSettings:
    """Knowledge source configuration"""

    # HubSpot configuration
    HUBSPOT: str = field(default_factory=get_env("KNOWLEDGE_SOURCE_HUBSPOT", ""))
    """HubSpot knowledge source token."""

    # Fluid Topics configuration
    FLUID_TOPICS_API_KEY: str = field(
        default_factory=get_env("FLUID_TOPICS_API_KEY", "")
    )
    """Fluid Topics API key."""
    FLUID_TOPICS_SEARCH_API_URL: str = field(
        default_factory=get_env("FLUID_TOPICS_SEARCH_API_URL", "")
    )
    """Fluid Topics search API URL."""
    FLUID_TOPICS_PDF_API_URL: str = field(
        default_factory=get_env("FLUID_TOPICS_PDF_API_URL", "")
    )
    """Fluid Topics PDF API URL."""
    FLUID_TOPICS_MAP_CONTENT: str = field(
        default_factory=get_env("FLUID_TOPICS_MAP_CONTENT", "")
    )
    """Fluid Topics topic content API URL template."""
    FLUID_TOPICS_MAP_TOC: str = field(
        default_factory=get_env("FLUID_TOPICS_MAP_TOC", "")
    )
    """Fluid Topics map TOC API URL template."""
    FLUID_TOPICS_MAP_STRUCTURE: str = field(
        default_factory=get_env("FLUID_TOPICS_MAP_STRUCTURE", "")
    )
    """Fluid Topics map structure API URL template."""
    FLUID_TOPICS_VIEWER_BASE_URL: str = field(
        default_factory=get_env("FLUID_TOPICS_VIEWER_BASE_URL", "")
    )
    """Fluid Topics viewer base URL."""

    # Oracle Knowledge configuration
    ORACLE_KNOWLEDGE_USERNAME: str = field(
        default_factory=get_env("ORACLE_KNOWLEDGE_USERNAME", "")
    )
    """Oracle Knowledge username."""
    ORACLE_KNOWLEDGE_PASSWORD: str = field(
        default_factory=get_env("ORACLE_KNOWLEDGE_PASSWORD", "")
    )
    """Oracle Knowledge password."""

    # SharePoint configuration
    SHAREPOINT_TENANT_ID: str = field(
        default_factory=get_env("SHAREPOINT_TENANT_ID", "")
    )
    """SharePoint tenant ID."""
    SHAREPOINT_CLIENT_ID: str = field(
        default_factory=get_env("SHAREPOINT_CLIENT_ID", "")
    )
    """SharePoint client ID."""
    SHAREPOINT_CLIENT_SECRET: str = field(
        default_factory=get_env("SHAREPOINT_CLIENT_SECRET", "")
    )
    """SharePoint client secret."""
    SHAREPOINT_CLIENT_CERT_THUMBPRINT: str = field(
        default_factory=get_env("SHAREPOINT_CLIENT_CERT_THUMBPRINT", "")
    )
    """SharePoint client certificate thumbprint."""
    SHAREPOINT_CLIENT_CERT_PRIVATE_KEY: str = field(
        default_factory=get_env("SHAREPOINT_CLIENT_CERT_PRIVATE_KEY", "")
    )
    """SharePoint client certificate private key."""


@dataclass
class Settings:
    general: GeneralSettings = field(default_factory=GeneralSettings)
    auth: AuthSettings = field(default_factory=AuthSettings)
    db: DatabaseSettings = field(default_factory=DatabaseSettings)
    db_connections: VectorDatabaseSettings = field(
        default_factory=VectorDatabaseSettings
    )
    scheduler: SchedulerSettings = field(default_factory=SchedulerSettings)
    log: LogSettings = field(default_factory=LogSettings)
    observability: ObservabilitySettings = field(default_factory=ObservabilitySettings)
    azure: AzureSettings = field(default_factory=AzureSettings)
    knowledge_sources: KnowledgeSourceSettings = field(
        default_factory=KnowledgeSourceSettings
    )

    @classmethod
    def from_env(cls, dotenv_filename: str = ".env") -> Settings:
        from litestar.cli._utils import console

        # Try to find .env file in the project root directory
        # Look for .env file starting from current directory and going up to project root
        current_dir = Path(os.getcwd())
        env_file = None

        # Look for .env file in current directory and parent directories
        for path in [current_dir] + list(current_dir.parents):
            potential_env_file = path / dotenv_filename
            if potential_env_file.is_file():
                env_file = potential_env_file
                break

        if env_file and env_file.is_file():
            from dotenv import load_dotenv

            console.print(
                f"[yellow]Loading environment configuration from {env_file}[/]"
            )

            load_dotenv(env_file, override=True)

        # Create settings instance
        settings = Settings()

        # Apply database defaults to vector database settings if PostgreSQL is used
        settings.db_connections.apply_database_defaults(settings.db)

        return settings


@lru_cache(maxsize=1, typed=True)
def get_settings() -> Settings:
    return Settings.from_env()


@lru_cache(maxsize=1, typed=True)
def get_general_settings() -> GeneralSettings:
    return get_settings().general


@lru_cache(maxsize=1, typed=True)
def get_auth_settings() -> AuthSettings:
    return get_settings().auth


@lru_cache(maxsize=1, typed=True)
def get_database_settings() -> DatabaseSettings:
    return get_settings().db


@lru_cache(maxsize=1, typed=True)
def get_log_settings() -> LogSettings:
    return get_settings().log


@lru_cache(maxsize=1, typed=True)
def get_observability_settings() -> ObservabilitySettings:
    return get_settings().observability


@lru_cache(maxsize=1, typed=True)
def get_azure_settings() -> AzureSettings:
    return get_settings().azure


@lru_cache(maxsize=1, typed=True)
def get_vector_database_settings() -> VectorDatabaseSettings:
    return get_settings().db_connections


@lru_cache(maxsize=1, typed=True)
def get_scheduler_settings() -> SchedulerSettings:
    return get_settings().scheduler


@lru_cache(maxsize=1, typed=True)
def get_knowledge_source_settings() -> KnowledgeSourceSettings:
    return get_settings().knowledge_sources


def get_env_vars_with_prefix(prefix: str) -> dict[str, str]:
    """Get all environment variables with a specific prefix."""
    import os

    return {key: value for key, value in os.environ.items() if key.startswith(prefix)}

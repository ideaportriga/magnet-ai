"""Unit tests for configuration and settings."""

from __future__ import annotations


import pytest

from core.config.base import DatabaseSettings, GeneralSettings


@pytest.mark.unit
class TestDatabaseSettings:
    """Tests for DatabaseSettings URL building."""

    def test_build_postgresql_url(self):
        """Should build a valid PostgreSQL async URL."""
        settings = DatabaseSettings()
        settings.TYPE = "postgresql"
        settings.HOST = "localhost"
        settings.PORT = "5432"
        settings.NAME = "testdb"
        settings.USER = "user"
        settings.PASSWORD = "pass"

        url = settings.build_database_url()
        assert url == "postgresql+asyncpg://user:pass@localhost:5432/testdb"

    def test_build_sqlite_url(self):
        """Should build a valid SQLite URL without host/port."""
        settings = DatabaseSettings()
        settings.TYPE = "sqlite"
        settings.NAME = "test.db"

        url = settings.build_database_url()
        assert url == "sqlite+aiosqlite:///test.db"

    def test_build_mysql_url(self):
        """Should build a valid MySQL async URL."""
        settings = DatabaseSettings()
        settings.TYPE = "mysql"
        settings.HOST = "db.example.com"
        settings.PORT = "3306"
        settings.NAME = "mydb"
        settings.USER = "root"
        settings.PASSWORD = "secret"

        url = settings.build_database_url()
        assert url == "mysql+aiomysql://root:secret@db.example.com:3306/mydb"

    def test_build_oracle_url(self):
        """Should build a valid Oracle URL."""
        settings = DatabaseSettings()
        settings.TYPE = "oracle"
        settings.HOST = "oracle.example.com"
        settings.PORT = "1521"
        settings.NAME = "ORCL"
        settings.USER = "sys"
        settings.PASSWORD = "pass"

        url = settings.build_database_url()
        assert url == "oracle+oracledb://sys:pass@oracle.example.com:1521/ORCL"

    def test_effective_url_prefers_explicit_url(self):
        """When DATABASE_URL is set, effective_url should use it."""
        settings = DatabaseSettings()
        settings.URL = "postgresql+asyncpg://explicit:url@host/db"
        settings.TYPE = "postgresql"
        settings.HOST = "other-host"

        assert settings.effective_url == "postgresql+asyncpg://explicit:url@host/db"

    def test_effective_url_falls_back_to_built(self):
        """When DATABASE_URL is empty, effective_url should build from components."""
        settings = DatabaseSettings()
        settings.URL = ""
        settings.TYPE = "postgresql"
        settings.HOST = "localhost"
        settings.PORT = "5432"
        settings.NAME = "testdb"
        settings.USER = "user"
        settings.PASSWORD = "pass"

        assert (
            settings.effective_url
            == "postgresql+asyncpg://user:pass@localhost:5432/testdb"
        )

    def test_sync_url_converts_asyncpg(self):
        """sync_url should convert asyncpg to psycopg2."""
        settings = DatabaseSettings()
        settings.URL = "postgresql+asyncpg://user:pass@host/db"

        assert "psycopg2" in settings.sync_url
        assert "asyncpg" not in settings.sync_url

    def test_build_url_no_type_returns_empty(self):
        """Should return empty string when no DB type set."""
        settings = DatabaseSettings()
        settings.TYPE = ""
        settings.HOST = ""

        assert settings.build_database_url() == ""

    def test_build_url_without_password(self):
        """Should handle missing password."""
        settings = DatabaseSettings()
        settings.TYPE = "postgresql"
        settings.HOST = "localhost"
        settings.PORT = "5432"
        settings.NAME = "db"
        settings.USER = "user"
        settings.PASSWORD = ""

        url = settings.build_database_url()
        assert url == "postgresql+asyncpg://user@localhost:5432/db"


@pytest.mark.unit
class TestGeneralSettings:
    """Tests for GeneralSettings defaults."""

    def test_default_encryption_key(self):
        """Default encryption key should be the development fallback."""
        settings = GeneralSettings()
        # Default key exists (not empty)
        assert len(settings.SECRET_ENCRYPTION_KEY) > 0

    def test_default_port(self):
        """Default port should be 8000."""
        settings = GeneralSettings()
        assert settings.PORT == 8000

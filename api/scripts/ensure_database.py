#!/usr/bin/env python3
"""Script to ensure database exists before running migrations."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from sqlalchemy import create_engine, text
from sqlalchemy.exc import OperationalError
from core.config.base import get_settings


def get_postgres_url_without_db(db_url: str) -> str:
    """Get PostgreSQL URL pointing to 'postgres' database instead of target database."""
    # Replace database name with 'postgres' (default admin database)
    if "/" in db_url:
        parts = db_url.rsplit("/", 1)
        # Remove any query parameters from database name
        if "?" in parts[1]:
            query_params = "?" + parts[1].split("?", 1)[1]
        else:
            query_params = ""
        return parts[0] + "/postgres" + query_params
    return db_url


def extract_db_name(db_url: str) -> str:
    """Extract database name from connection URL."""
    if "/" in db_url:
        db_part = db_url.rsplit("/", 1)[1]
        # Remove query parameters
        if "?" in db_part:
            db_part = db_part.split("?", 1)[0]
        return db_part
    return ""


def ensure_database_exists():
    """Check if database exists and create it if it doesn't."""
    settings = get_settings()

    # Get the database URL (convert async to sync for this operation)
    db_url = settings.db.effective_url

    # Convert async URL to sync
    if "postgresql+asyncpg://" in db_url:
        sync_url = db_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")
    else:
        sync_url = db_url

    db_name = extract_db_name(sync_url)

    if not db_name:
        print("❌ Could not extract database name from URL")
        sys.exit(1)

    print(f"🔍 Checking if database '{db_name}' exists...")

    # Connect to 'postgres' database to check if target database exists
    admin_url = get_postgres_url_without_db(sync_url)

    try:
        # Create engine for admin connection
        engine = create_engine(admin_url, isolation_level="AUTOCOMMIT")

        with engine.connect() as conn:
            # Check if database exists
            result = conn.execute(
                text("SELECT 1 FROM pg_database WHERE datname = :dbname"),
                {"dbname": db_name},
            )

            if result.fetchone():
                print(f"✅ Database '{db_name}' already exists")
            else:
                print(f"📦 Database '{db_name}' does not exist, creating...")
                # Create the database
                conn.execute(text(f'CREATE DATABASE "{db_name}"'))
                print(f"✅ Database '{db_name}' created successfully")

        engine.dispose()

    except OperationalError as e:
        print(f"❌ Connection error: {e}")
        print(
            "\nMake sure PostgreSQL is running and connection parameters are correct."
        )
        print(
            f"Connection URL (without password): {admin_url.split('@')[1] if '@' in admin_url else admin_url}"
        )
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    ensure_database_exists()

"""Utility functions for PgVector store operations."""

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)


def clean_connection_string_for_asyncpg(connection_string: str) -> str:
    """
    Clean connection string to be compatible with asyncpg.

    Removes SQLAlchemy-specific driver suffixes like '+asyncpg' from the scheme.

    Args:
        connection_string: Original connection string

    Returns:
        Cleaned connection string compatible with asyncpg

    Examples:
        >>> clean_connection_string_for_asyncpg("postgresql+asyncpg://user:pass@host:5432/db")
        "postgresql://user:pass@host:5432/db"
        >>> clean_connection_string_for_asyncpg("postgres+asyncpg://user:pass@host:5432/db")
        "postgres://user:pass@host:5432/db"
    """
    if not connection_string:
        return connection_string

    # Remove SQLAlchemy driver suffixes
    patterns = [
        (r"^postgresql\+asyncpg://", "postgresql://"),
        (r"^postgres\+asyncpg://", "postgres://"),
        (r"^postgresql\+psycopg2://", "postgresql://"),
        (r"^postgres\+psycopg2://", "postgres://"),
    ]

    cleaned = connection_string
    for pattern, replacement in patterns:
        cleaned = re.sub(pattern, replacement, cleaned)

    return cleaned


def mask_password_in_connection_string(connection_string: str) -> str:
    """
    Mask password in connection string for logging purposes.

    Args:
        connection_string: Original connection string

    Returns:
        Connection string with password masked

    Example:
        >>> mask_password_in_connection_string("postgresql://user:secret@host:5432/db")
        "postgresql://user:***@host:5432/db"
    """
    if not connection_string or "@" not in connection_string:
        return connection_string

    # Pattern to match and replace password
    pattern = r"(://[^:]+:)[^@]+(@)"
    replacement = r"\1***\2"

    return re.sub(pattern, replacement, connection_string)


def format_connection_string(
    host: str = "localhost",
    port: int = 5432,
    database: str = "postgres",
    user: str = "postgres",
    password: str = "password",
    **kwargs,
) -> str:
    """Format PostgreSQL connection string.

    Args:
        host: Database host
        port: Database port
        database: Database name
        user: Database user
        password: Database password
        **kwargs: Additional connection parameters

    Returns:
        Formatted connection string
    """
    base_url = f"postgresql://{user}:{password}@{host}:{port}/{database}"

    if kwargs:
        params = "&".join(f"{k}={v}" for k, v in kwargs.items())
        base_url += f"?{params}"

    return base_url


def validate_vector_dimension(dimension: int) -> None:
    """Validate vector dimension.

    Args:
        dimension: Vector dimension to validate

    Raises:
        ValueError: If dimension is invalid
    """
    if not isinstance(dimension, int) or dimension <= 0:
        raise ValueError(
            f"Vector dimension must be a positive integer, got: {dimension}"
        )

    if dimension > 16000:  # pgvector limit
        raise ValueError(f"Vector dimension cannot exceed 16000, got: {dimension}")


def prepare_metadata_for_json(metadata: dict) -> dict:
    """Prepare metadata dictionary for JSON serialization.

    Args:
        metadata: Metadata dictionary

    Returns:
        JSON-serializable metadata dictionary
    """
    if not isinstance(metadata, dict):
        return {}

    result = {}
    for key, value in metadata.items():
        # Convert non-serializable types to strings
        if isinstance(value, (str, int, float, bool, list, dict)) or value is None:
            result[key] = value
        else:
            result[key] = str(value)

    return result


async def check_table_exists(client, table_name: str) -> bool:
    """Check if a table exists in the database.

    Args:
        client: Database client
        table_name: Name of the table to check

    Returns:
        True if table exists, False otherwise
    """
    try:
        result = await client.fetchval(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = $1
            )
        """,
            table_name,
        )
        return bool(result)
    except Exception as e:
        logger.error("Error checking if table %s exists: %s", table_name, e)
        return False


async def get_table_info(client, table_name: str) -> dict[str, Any]:
    """Get information about a table.

    Args:
        client: Database client
        table_name: Name of the table

    Returns:
        Dictionary with table information
    """
    try:
        # Get table size and row count
        stats = await client.fetchrow(f"""
            SELECT 
                pg_size_pretty(pg_total_relation_size('{table_name}')) as table_size,
                (SELECT count(*) FROM {table_name}) as row_count
        """)

        # Get column information
        columns = await client.execute_query(
            """
            SELECT column_name, data_type, is_nullable
            FROM information_schema.columns
            WHERE table_name = $1
            ORDER BY ordinal_position
        """,
            table_name,
        )

        return {
            "table_name": table_name,
            "table_size": stats["table_size"] if stats else "Unknown",
            "row_count": stats["row_count"] if stats else 0,
            "columns": [
                {
                    "name": col["column_name"],
                    "type": col["data_type"],
                    "nullable": col["is_nullable"] == "YES",
                }
                for col in columns
            ],
        }
    except Exception as e:
        logger.error("Error getting table info for %s: %s", table_name, e)
        return {
            "table_name": table_name,
            "error": str(e),
        }

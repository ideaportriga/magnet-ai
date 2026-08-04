"""Ensure every pgvector collection documents table has its vector indexes.

PgVectorStore creates an HNSW index on `embedding` and a GIN index on
`metadata` when it creates a collection's documents table. Tables that
predate that code, were created by other tooling, or had indexes dropped
manually get no backfill: Alembic cannot manage them because the vector
store may live in a separate database (PGVECTOR_* settings) and the tables
are created at runtime, not by migrations. Without the HNSW index every
similarity search is a sequential scan over the whole collection.

This script connects using the application's PGVECTOR_* configuration,
walks all collections, and reports/creates missing indexes. Index names and
parameters mirror PgVectorStore._create_documents_table exactly. All
creation statements are idempotent (CREATE INDEX IF NOT EXISTS).

Embedding columns wider than 2000 dimensions cannot be indexed (pgvector
limit) and are reported but skipped.

Usage (from the api/ directory):
    python scripts/pgvector_ensure_indexes.py --dry-run   # report only
    python scripts/pgvector_ensure_indexes.py             # create missing
"""

import argparse
import asyncio
import logging
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))

from dotenv import load_dotenv

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("pgvector_ensure_indexes")

# pgvector HNSW/IVFFlat indexes support at most 2000 dimensions.
MAX_INDEXABLE_DIMS = 2000


async def main(dry_run: bool) -> int:
    try:
        from stores.pgvector_db import pgvector_client, pgvector_store  # noqa: F401
    except ImportError:
        logger.error(
            "PgVector store is not configured (VECTOR_DB_TYPE != PGVECTOR); nothing to do"
        )
        return 1

    from stores.pgvector_db.store import PgVectorStore

    collections = await pgvector_client.execute_query(
        f"SELECT id::text AS id, name FROM {PgVectorStore.COLLECTIONS_TABLE} ORDER BY name"
    )
    logger.info("Found %d collection(s)", len(collections))

    missing = 0
    created = 0
    for collection in collections:
        collection_id = collection["id"]
        table_name = (
            f"{PgVectorStore.DOCUMENTS_TABLE_PREFIX}{collection_id.replace('-', '_')}"
        )

        table_exists = await pgvector_client.fetchval(
            "SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = $1)",
            table_name,
        )
        if not table_exists:
            logger.info(
                "- %s (%s): no documents table yet, skipping",
                collection["name"],
                collection_id,
            )
            continue

        row_count = await pgvector_client.fetchval(f"SELECT count(*) FROM {table_name}")

        has_hnsw = await pgvector_client.fetchval(
            "SELECT EXISTS (SELECT FROM pg_indexes WHERE tablename = $1 "
            "AND indexdef LIKE '%USING hnsw (embedding %')",
            table_name,
        )
        has_metadata_gin = await pgvector_client.fetchval(
            "SELECT EXISTS (SELECT FROM pg_indexes WHERE tablename = $1 "
            "AND indexdef LIKE '%USING gin (metadata%')",
            table_name,
        )

        if not has_hnsw:
            dims = await pgvector_store._get_current_vector_size(table_name)
            if dims is not None and dims > MAX_INDEXABLE_DIMS:
                logger.warning(
                    "- %s (%s): embedding has %d dimensions, exceeds the pgvector "
                    "index limit of %d — cannot be indexed, searches will stay sequential",
                    collection["name"],
                    collection_id,
                    dims,
                    MAX_INDEXABLE_DIMS,
                )
            else:
                missing += 1
                logger.info(
                    "- %s (%s): missing HNSW index on embedding (%s rows)%s",
                    collection["name"],
                    collection_id,
                    row_count,
                    " [dry-run]" if dry_run else ", creating (may take a while)...",
                )
                if not dry_run:
                    # Same name and parameters as PgVectorStore._create_documents_table
                    await pgvector_client.execute_command(
                        f"CREATE INDEX IF NOT EXISTS idx_{table_name}_embedding_cosine "
                        f"ON {table_name} USING hnsw (embedding vector_cosine_ops) "
                        f"WITH (m = 16, ef_construction = 64)"
                    )
                    created += 1

        if not has_metadata_gin:
            missing += 1
            logger.info(
                "- %s (%s): missing GIN index on metadata%s",
                collection["name"],
                collection_id,
                " [dry-run]" if dry_run else ", creating...",
            )
            if not dry_run:
                await pgvector_client.execute_command(
                    f"CREATE INDEX IF NOT EXISTS idx_{table_name}_metadata_gin "
                    f"ON {table_name} USING GIN (metadata)"
                )
                created += 1

    if missing == 0:
        logger.info("All collection documents tables already have their indexes")
    elif dry_run:
        logger.info(
            "%d missing index(es) found; rerun without --dry-run to create them",
            missing,
        )
    else:
        logger.info("Created %d of %d missing index(es)", created, missing)

    await pgvector_client.close_pool()
    return 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Report missing indexes without creating them",
    )
    args = parser.parse_args()
    sys.exit(asyncio.run(main(args.dry_run)))

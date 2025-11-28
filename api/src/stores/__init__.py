# Async compatibility check: True

from core.config.base import get_vector_database_settings
from stores.document_store import DocumentStore


# TODO - move elsewhere
class RecordNotFoundError(Exception):
    pass


def get_db_client():
    db_settings = get_vector_database_settings()
    db_type = db_settings.VECTOR_DB_TYPE

    if db_type == "ORACLE":
        from stores.oracle import oracle_db_client

        return oracle_db_client
    if db_type == "COSMOS":
        from stores.cosmos_db import cosmos_db_client

        return cosmos_db_client
    if db_type == "PGVECTOR":
        from stores.pgvector_db import pgvector_client

        return pgvector_client
    if db_type == "MONGODB":
        from stores.mongo_db import mongo_db_client

        return mongo_db_client
    raise ValueError(f"Unsupported VECTOR_DB_TYPE: {db_type}")


def get_db_store() -> DocumentStore:
    db_settings = get_vector_database_settings()
    db_type = db_settings.VECTOR_DB_TYPE

    if db_type == "ORACLE":
        from stores.oracle import oracle_db_store

        return oracle_db_store
    if db_type == "COSMOS":
        from stores.cosmos_db import cosmos_db_store

        return cosmos_db_store
    if db_type == "PGVECTOR":
        from stores.pgvector_db import pgvector_store

        return pgvector_store
    if db_type == "MONGODB":
        from stores.mongo_db import mongo_db_store

        return mongo_db_store
    raise ValueError(f"Unsupported VECTOR_DB_TYPE: {db_type}")

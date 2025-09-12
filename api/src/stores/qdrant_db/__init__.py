import os

from qdrant_client import AsyncQdrantClient

from stores.qdrant_db.store import QdrantVectorStore

database_name = os.environ.get("MONGO_DB_DB_NAME", "")
db_vector_type = os.environ.get("DB_VECTOR_TYPE", "QDRANT")


if db_vector_type == "QDRANT":
    host = os.environ.get("QDRANT_DB_HOST", "")
    port_str = os.environ.get("QDRANT_DB_PORT")
    port = int(port_str) if port_str is not None else None
    api_key = os.environ.get("QDRANT_DB_API_KEY", "")

    vector_db_client = AsyncQdrantClient(url=host, port=port, api_key=api_key)

    vector_db_store = QdrantVectorStore(client=vector_db_client, prefix=database_name)

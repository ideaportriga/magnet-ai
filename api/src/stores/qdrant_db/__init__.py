from qdrant_client import AsyncQdrantClient

from core.config.base import get_vector_database_settings, get_general_settings
from stores.qdrant_db.store import QdrantVectorStore

general_settings = get_general_settings()
db_settings = get_vector_database_settings()

database_name = db_settings.MONGO_DB_DB_NAME
db_vector_type = db_settings.DB_VECTOR_TYPE


if db_vector_type == "QDRANT":
    host = db_settings.QDRANT_DB_HOST
    port_str = db_settings.QDRANT_DB_PORT
    port = int(port_str) if port_str is not None else None
    api_key = db_settings.QDRANT_DB_API_KEY

    vector_db_client = AsyncQdrantClient(url=host, port=port, api_key=api_key)

    vector_db_store = QdrantVectorStore(client=vector_db_client, prefix=database_name)

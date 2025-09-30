from core.config.base import get_vector_database_settings, get_general_settings
from stores.mongo_db.client import MongoDBClient
from stores.mongo_db.store import MongoDbStore
from stores.qdrant_db import vector_db_store

general_settings = get_general_settings()
db_settings = get_vector_database_settings()

db_type = db_settings.VECTOR_DB_TYPE


database_name = db_settings.MONGO_DB_DB_NAME

if db_type == "MONGODB":
    connection_string = db_settings.MONGO_DB_CONNECTION_STRING

    mongo_db_client = MongoDBClient(
        connection_string=connection_string,
        database_name=database_name,
    )


mongo_db_store = MongoDbStore(client=mongo_db_client, vector_store=vector_db_store)

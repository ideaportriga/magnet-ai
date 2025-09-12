import os

from stores.mongo_db.client import MongoDBClient
from stores.mongo_db.store import MongoDbStore
from stores.qdrant_db import vector_db_store

db_type = os.environ.get("DB_TYPE", "MONGO")


database_name = os.environ.get("MONGO_DB_DB_NAME", "")

if db_type == "MONGODB":
    connection_string = os.environ.get("MONGO_DB_CONNECTION_STRING", "")

    mongo_db_client = MongoDBClient(
        connection_string=connection_string,
        database_name=database_name,
    )


mongo_db_store = MongoDbStore(client=mongo_db_client, vector_store=vector_db_store)

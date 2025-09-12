import os

from stores.cosmos_db.client import CosmosDbClient
from stores.cosmos_db.store import CosmosDbStore

db_type = os.environ.get("DB_TYPE", "COSMOS")

if db_type == "COSMOS":
    connection_string = os.environ.get("COSMOS_DB_CONNECTION_STRING", "")
    database_name = os.environ.get("COSMOS_DB_DB_NAME", "")

    cosmos_db_client = CosmosDbClient(
        connection_string=connection_string,
        database_name=database_name,
    )

    cosmos_db_store = CosmosDbStore(client=cosmos_db_client)

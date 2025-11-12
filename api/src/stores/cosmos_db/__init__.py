from core.config.base import get_vector_database_settings, get_general_settings
from stores.cosmos_db.client import CosmosDbClient
from stores.cosmos_db.store import CosmosDbStore

general_settings = get_general_settings()
db_settings = get_vector_database_settings()

db_type = db_settings.VECTOR_DB_TYPE

if db_type == "COSMOS":
    connection_string = db_settings.COSMOS_DB_CONNECTION_STRING
    database_name = db_settings.COSMOS_DB_DB_NAME

    cosmos_db_client = CosmosDbClient(
        connection_string=connection_string,
        database_name=database_name,
    )

    cosmos_db_store = CosmosDbStore(client=cosmos_db_client)

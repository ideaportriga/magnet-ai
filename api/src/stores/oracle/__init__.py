from urllib.parse import quote_plus

from core.config.base import get_vector_database_settings, get_general_settings
from stores.oracle.client import OracleDbClient
from stores.oracle.store import OracleDbStore

# from open_ai.oci_embedding import oci_embedding

general_settings = get_general_settings()
db_settings = get_vector_database_settings()

db_type = db_settings.VECTOR_DB_TYPE

if db_type == "ORACLE":
    oracle_username = db_settings.ORACLE_USERNAME
    oracle_password = db_settings.ORACLE_PASSWORD
    oracle_host = db_settings.ORACLE_HOST
    oracle_port = db_settings.ORACLE_PORT
    oracle_service_name = db_settings.ORACLE_SERVICE_NAME
    oracle_mongo_connection_string = db_settings.ORACLE_MONGO_CONNECTION_STRING

    dsn = f"(DESCRIPTION=\
                (RETRY_COUNT=20)(RETRY_DELAY=3)\
                (ADDRESS=(PROTOCOL=TCPS)(PORT={oracle_port})(HOST={oracle_host}))\
                (CONNECT_DATA=(SERVICE_NAME={oracle_service_name}))\
                (SECURITY=(SSL_SERVER_DN_MATCH=YES)))"

    encoded_oracle_password = quote_plus(oracle_password)
    mongo_user_info = f"{oracle_username}:{encoded_oracle_password}@"
    mongo_connection_string = oracle_mongo_connection_string.replace(
        "[user:password@]", mongo_user_info
    ).replace("[user]", oracle_username)

    oracle_db_client = OracleDbClient(
        user=oracle_username,
        password=oracle_password,
        dsn=dsn,
        mongo_connection_string=mongo_connection_string,
    )

    oracle_db_store = OracleDbStore(client=oracle_db_client)

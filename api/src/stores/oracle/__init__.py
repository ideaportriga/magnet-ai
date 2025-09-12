import os
from urllib.parse import quote_plus

from stores.oracle.client import OracleDbClient
from stores.oracle.store import OracleDbStore

# from open_ai.oci_embedding import oci_embedding

db_type = os.environ.get("DB_TYPE", "")

if db_type == "ORACLE":
    oracle_username = os.environ.get("ORACLE_USERNAME", "")
    oracle_password = os.environ.get("ORACLE_PASSWORD", "")
    oracle_host = os.environ.get("ORACLE_HOST", "")
    oracle_port = os.environ.get("ORACLE_PORT", "")
    oracle_service_name = os.environ.get("ORACLE_SERVICE_NAME", "")
    oracle_mongo_connection_string = os.environ.get(
        "ORACLE_MONGO_CONNECTION_STRING", ""
    )

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

# TODO - also migrate templates from Strapi


# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../src")))
from dotenv import load_dotenv

load_dotenv()

from logging import getLogger  # noqa: E402

from stores.cosmos_db import cosmos_db_client  # noqa: E402

logger = getLogger(__name__)


db = cosmos_db_client.database

res = db.command(
    {
        "createIndexes": "documents",
        "indexes": [
            {
                "name": "VectorSearchIndex",
                "key": {"contentVector": "cosmosSearch"},
                "cosmosSearchOptions": {
                    "kind": "vector-hnsw",
                    "m": 16,  # default value
                    "efConstruction": 64,  # default value
                    "similarity": "COS",
                    "dimensions": 1536,
                },
            },
        ],
    },
)

logger.info("res = ", res)

from logging import getLogger

import setup  # noqa: F401

logger = getLogger(__name__)

from pymongo import MongoClient  # noqa: E402
from core.config.base import get_vector_database_settings  # noqa: E402

db_settings = get_vector_database_settings()
COSMOS_DB_CONNECTION_STRING = db_settings.COSMOS_DB_CONNECTION_STRING


def clone_database(source_db_name, target_db_name):
    # Connect to source MongoDB
    client = MongoClient(COSMOS_DB_CONNECTION_STRING)
    source_db = client[source_db_name]
    target_db = client[target_db_name]

    # List all collections in the source database
    collections = source_db.list_collection_names()

    for collection_name in collections:
        logger.info(f"Copy collection {collection_name}")
        # Get a reference to each collection
        source_collection = source_db[collection_name]
        target_collection = target_db[collection_name]

        # # Drop target collection if it exists (start with a clean slate)
        if collection_name in target_db.list_collection_names():
            target_db.drop_collection(collection_name)

        # Insert documents from source collection to target collection
        source_documents = list(source_collection.find())

        if source_documents:
            logger.info(f"Inserting {len(source_documents)} documents")
            target_collection.insert_many(source_documents)
        else:
            logger.info("No documents to insert")

        for index_name, index in source_collection.index_information().items():
            if index_name == "VectorSearchIndex":
                logger.info("Create index VectorSearchIndex")

                target_db.command(
                    {
                        "createIndexes": collection_name,
                        "indexes": [
                            {
                                "name": "VectorSearchIndex",
                                "key": {"embedding": "cosmosSearch"},
                                "cosmosSearchOptions": {
                                    "kind": "vector-ivf",
                                    "numLists": 1,
                                    "similarity": "COS",
                                    "dimensions": 1536,
                                },
                            },
                        ],
                    },
                )

                logger.info("Created index VectorSearchIndex")
            # target_collection.create_index(index["key"], name=index_name, unique=index.get("unique", False))

    logger.info("Database cloning completed successfully!")


if __name__ == "__main__":
    clone_database(source_db_name="magnet-dev", target_db_name="magnet-test")

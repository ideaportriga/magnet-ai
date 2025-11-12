from logging import getLogger

import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorCollection

from stores.database_client import DatabaseClient

logger = getLogger(__name__)


class MongoDBClient(DatabaseClient):
    def __init__(self, connection_string: str, database_name: str):
        self.client = motor.motor_asyncio.AsyncIOMotorClient(connection_string)
        self.database = self.client[database_name]

    def get_collection(self, name: str) -> AsyncIOMotorCollection:
        return self.database[name]

    async def close(self):
        self.client.close()

    async def close_pool(self):
        # Motor does not require explicit connection pool management
        pass

    # TODO - do we need wrapper methods for mongo commands?

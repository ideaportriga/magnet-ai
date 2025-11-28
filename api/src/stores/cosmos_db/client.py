from logging import getLogger

import motor.motor_asyncio
from motor.motor_asyncio import AsyncIOMotorCollection

from stores.database_client import DatabaseClient

logger = getLogger(__name__)


class CosmosDbClient(DatabaseClient):
    def __init__(self, connection_string: str, database_name: str):
        try:
            self.client = motor.motor_asyncio.AsyncIOMotorClient(connection_string)
            self.database = self.client[database_name]
        except Exception as e:
            logger.error(f"Failed to connect to MongoDB: {e}")
            raise

    def get_collection(self, name: str) -> AsyncIOMotorCollection:
        # In motor, getting a collection is not an async operation, but we keep the method async for consistency.
        return self.database[name]

    async def close(self):
        self.client.close()

    async def close_pool(self):
        # Alias for close, for compatibility
        await self.close()

    # TODO - do we need wrapper methods for mongo commands?

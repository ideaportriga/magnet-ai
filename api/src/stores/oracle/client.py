import threading
from contextlib import asynccontextmanager
from logging import getLogger

import oracledb
from motor.motor_asyncio import AsyncIOMotorClient

from stores.database_client import DatabaseClient

logger = getLogger(__name__)


class OracleDbClient(DatabaseClient):
    _local = threading.local()

    def __init__(
        self,
        user: str,
        password: str,
        dsn: str,
        mongo_connection_string: str,
    ):
        self.user = user
        self.password = password
        self.dsn = dsn
        # self.connect()
        self._pool = oracledb.create_pool_async(
            user=self.user,
            password=self.password,
            dsn=self.dsn,
            min=1,
            max=15,
            increment=1,
            ping_interval=60,
        )
        # Mongo (async)
        self.client = AsyncIOMotorClient(mongo_connection_string)
        self.database = self.client[user]

    def get_collection(self, name: str):
        if name == "collections":
            name = "COLLECTIONS_DV"
        elif name == "documents":
            name = "DOCUMENTS_DV"
        return self.database[name]

    @asynccontextmanager
    async def execute(self, sql: str, params: dict | None = None):
        logger.debug(f"Executing SQL: {sql} with params: {params}")
        if self._pool is None:
            raise RuntimeError(
                "Connection pool is not initialized. Call await init_pool() first."
            )
        async with await self._pool.acquire() as connection:
            async with connection.cursor() as cursor:
                logger.info(
                    f"execute 2, pool: opened {self._pool.opened}, busy {self._pool.busy}",
                )
                assert cursor is not None, "Cursor is not initialized after connect."
                try:
                    if params is not None:
                        await cursor.execute(sql, params)
                    else:
                        await cursor.execute(sql)
                    yield cursor
                except oracledb.Error as e:
                    (error_obj,) = e.args
                    logger.error(f"Database error code: {error_obj.code}")
                    logger.error(f"Database error message: {error_obj.message}")
                    logger.error(f"Database error context: {error_obj.context}")
                    if error_obj.full_code == "DPY-4011":
                        logger.warning("Connection lost in execute...")
                        # async with await self._pool.acquire() as connection2:
                        #     async with connection2.cursor() as cursor2:
                        #         assert cursor2 is not None, (
                        #             "Cursor is not initialized after reconnect."
                        #         )
                        #         if params is not None:
                        #             await cursor2.execute(sql, params)
                        #         else:
                        #             await cursor2.execute(sql)
                        #         return cursor2
                    else:
                        logger.error(f"An error occurred: {e}")
                        await connection.rollback()
                        raise

    async def close_pool(self):
        if self._pool:
            logger.info(
                f"Closing the connection pool...: opened {self._pool.opened}, busy {self._pool.busy}",
            )
            await self._pool.close()
            logger.info("Connection pool closed")
        else:
            logger.warning(
                "Connection pool is already closed or was never initialized.",
            )

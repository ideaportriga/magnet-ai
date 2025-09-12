# Async compatibility check: True
from abc import ABC, abstractmethod

from motor.motor_asyncio import AsyncIOMotorCollection


class DatabaseClient(ABC):
    @abstractmethod
    def get_collection(self, collection_name: str) -> AsyncIOMotorCollection: ...

from abc import ABC, abstractmethod
from typing import Generic, TypeVar

T = TypeVar("T")


class DataSource(ABC, Generic[T]):
    @property
    @abstractmethod
    def name(self) -> str: ...

    @abstractmethod
    async def get_data(self) -> list[T]: ...

"""Unified file storage module.

Re-exports the main public API so consumers can write::

    from storage import StorageService, StoredFile, FileLimits, setup_storage
"""

from .backends import setup_storage
from .config import StorageConfig
from .limits import FileLimits
from .models import StoredFile
from .service import StorageService

__all__ = [
    "FileLimits",
    "StorageConfig",
    "StorageService",
    "StoredFile",
    "setup_storage",
]

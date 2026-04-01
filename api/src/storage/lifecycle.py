"""SQLAlchemy event listeners for automatic file cleanup on entity deletion."""

from __future__ import annotations

import asyncio
import logging
from typing import TYPE_CHECKING, Any

from sqlalchemy import event

if TYPE_CHECKING:
    from sqlalchemy.engine import Connection
    from sqlalchemy.orm import Mapper

    from .service import StorageService

log = logging.getLogger(__name__)

# Pairs of (model_class, entity_type) to register.
# Extended as more phases are implemented.
_ENTITY_LISTENERS: list[tuple[str, str, str]] = [
    # (module_path, class_name, entity_type)
    ("core.db.models.knowledge_graph", "KnowledgeGraphSource", "kg_source"),
    ("core.db.models.knowledge_graph", "KnowledgeGraph", "kg_upload"),
]


def register_storage_listeners(storage_service: StorageService) -> None:
    """Attach after_delete listeners that soft-delete associated stored files.

    The listeners schedule async cleanup via ``asyncio.ensure_future``.
    This is a pragmatic approach that works when there is a running event loop
    (the normal Litestar request context).  A more robust implementation could
    use a background task queue — see roadmap Phase 9 notes.
    """
    for module_path, class_name, entity_type in _ENTITY_LISTENERS:
        try:
            import importlib

            mod = importlib.import_module(module_path)
            model_cls = getattr(mod, class_name)
        except (ImportError, AttributeError):
            log.warning(
                "Could not register storage listener for %s.%s — model not found",
                module_path,
                class_name,
            )
            continue

        def _make_listener(et: str) -> Any:
            def _on_delete(
                mapper: Mapper[Any], connection: Connection, target: Any
            ) -> None:
                try:
                    loop = asyncio.get_running_loop()
                except RuntimeError:
                    log.warning(
                        "No running event loop — skipping storage cleanup for %s %s",
                        et,
                        target.id,
                    )
                    return
                asyncio.ensure_future(
                    _safe_delete(storage_service, et, target.id),
                    loop=loop,
                )

            return _on_delete

        event.listen(model_cls, "after_delete", _make_listener(entity_type))
        log.debug(
            "Registered storage lifecycle listener for %s.%s", module_path, class_name
        )


async def _safe_delete(
    service: StorageService, entity_type: str, entity_id: Any
) -> None:
    """Soft-delete all files for the given entity using a fresh DB session."""
    try:
        from core.config.base import get_settings
        from sqlalchemy.ext.asyncio import AsyncSession

        settings = get_settings()
        engine = settings.db.get_engine()
        async with AsyncSession(engine, expire_on_commit=False) as session:
            await service.delete_entity_files(session, entity_type, entity_id)
            await session.commit()
            log.info("Soft-deleted stored files for %s/%s", entity_type, entity_id)
    except Exception:
        log.exception("Failed to cleanup files for %s/%s", entity_type, entity_id)

"""Recovery job for knowledge-graph sources stuck in 'syncing' state.

If a process dies (OOM kill, deployment, crash) while a source is being
synced, the row stays ``status='syncing'`` forever.  This job periodically
checks for sources that have been in that state for longer than a threshold
and transitions them to ``'failed'``.
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update

from core.db.models.knowledge_graph.knowledge_graph_source import KnowledgeGraphSource
from core.db.session import get_async_session

logger = logging.getLogger(__name__)

STUCK_THRESHOLD_MINUTES = 30


async def recover_stuck_syncing_sources() -> None:
    """Mark sources stuck in 'syncing' for > STUCK_THRESHOLD_MINUTES as 'failed'."""
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=STUCK_THRESHOLD_MINUTES)

    async with get_async_session() as session:
        # Find stuck sources
        result = await session.execute(
            select(KnowledgeGraphSource.id, KnowledgeGraphSource.name)
            .where(KnowledgeGraphSource.status == "syncing")
            .where(KnowledgeGraphSource.updated_at < cutoff)
        )
        stuck_rows = result.all()

        if not stuck_rows:
            return

        stuck_ids = [row.id for row in stuck_rows]
        logger.warning(
            "Recovering %d stuck syncing source(s): %s",
            len(stuck_ids),
            [row.name for row in stuck_rows],
        )

        await session.execute(
            update(KnowledgeGraphSource)
            .where(KnowledgeGraphSource.id.in_(stuck_ids))
            .values(status="failed")
        )
        await session.commit()

        logger.info("Marked %d source(s) as failed", len(stuck_ids))

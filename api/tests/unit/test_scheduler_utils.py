"""Regression tests for scheduler.utils.update_job_status
(BACKEND_FIXES_ROADMAP.md §B.1).

System cron jobs (ks_upload_cleanup, kg_sync_recovery, etc.) are registered
with string IDs and have no row in the `jobs` table. update_job_status must
skip the DB round-trip for those instead of crashing on UUID parsing.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from scheduler.types import JobStatus
from scheduler.utils import update_job_status


@pytest.mark.asyncio
async def test_system_job_skips_db_update(caplog):
    """String-id system jobs must not hit the DB at all."""
    with patch("scheduler.utils.alchemy") as mock_alchemy:
        await update_job_status("ks_upload_cleanup", JobStatus.WAITING)
        mock_alchemy.get_session.assert_not_called()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "job_id",
    [
        "ks_upload_cleanup",
        "kg_sync_recovery",
        "note_taker_pending_cleanup",
        "refresh_token_cleanup",
        "",
        "not-a-uuid",
    ],
)
async def test_non_uuid_ids_are_silent(job_id):
    with patch("scheduler.utils.alchemy") as mock_alchemy:
        await update_job_status(job_id, JobStatus.COMPLETED)
        mock_alchemy.get_session.assert_not_called()


@pytest.mark.asyncio
async def test_uuid_job_reaches_service():
    """User jobs (UUID id) must still be persisted."""
    uuid_str = "11111111-1111-1111-1111-111111111111"

    mock_session = AsyncMock()
    # Async context manager that yields the session
    mock_cm = MagicMock()
    mock_cm.__aenter__ = AsyncMock(return_value=mock_session)
    mock_cm.__aexit__ = AsyncMock(return_value=None)

    with (
        patch("scheduler.utils.alchemy") as mock_alchemy,
        patch("scheduler.utils.JobsService") as mock_service_cls,
    ):
        mock_alchemy.get_session.return_value = mock_cm
        mock_service = mock_service_cls.return_value
        mock_service.update = AsyncMock()

        await update_job_status(uuid_str, JobStatus.WAITING)

        mock_alchemy.get_session.assert_called_once()
        mock_service.update.assert_called_once()

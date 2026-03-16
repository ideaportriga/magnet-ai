"""Periodic cleanup of temporary uploaded files for knowledge sources.

Files uploaded via the knowledge-source file-upload endpoint are stored in a
temporary directory (default ``/tmp/ks_uploads``).  After a configurable TTL
the files are no longer needed (the data has been extracted and loaded into the
vector store) and can be safely removed.

Environment variables
---------------------
KS_UPLOAD_DIR
    Root directory for temporary knowledge-source uploads.
    Default: ``/tmp/ks_uploads``

KS_UPLOAD_TTL_HOURS
    Number of hours after which an uploaded file is eligible for deletion.
    Default: ``24``

KS_UPLOAD_CLEANUP_INTERVAL_MINUTES
    How often (in minutes) the cleanup job runs.
    Default: ``60``
"""

import logging
import os
import shutil
import time

logger = logging.getLogger(__name__)

KS_UPLOAD_DIR: str = os.environ.get("KS_UPLOAD_DIR", "/tmp/ks_uploads")
KS_UPLOAD_TTL_HOURS: int = int(os.environ.get("KS_UPLOAD_TTL_HOURS", "24"))
KS_UPLOAD_CLEANUP_INTERVAL_MINUTES: int = int(
    os.environ.get("KS_UPLOAD_CLEANUP_INTERVAL_MINUTES", "60")
)


def cleanup_old_uploads() -> None:
    """Remove uploaded files and empty collection directories older than the TTL.

    This function is designed to be called from a scheduler job and is
    intentionally synchronous (APScheduler's ``AsyncIOExecutor`` wraps it).
    """
    if not os.path.isdir(KS_UPLOAD_DIR):
        return

    cutoff = time.time() - KS_UPLOAD_TTL_HOURS * 3600
    removed_files = 0
    removed_dirs = 0

    for collection_dir_name in os.listdir(KS_UPLOAD_DIR):
        collection_path = os.path.join(KS_UPLOAD_DIR, collection_dir_name)
        if not os.path.isdir(collection_path):
            continue

        for filename in os.listdir(collection_path):
            file_path = os.path.join(collection_path, filename)
            if not os.path.isfile(file_path):
                continue
            try:
                if os.path.getmtime(file_path) < cutoff:
                    os.remove(file_path)
                    removed_files += 1
            except OSError:
                logger.warning("Failed to remove expired upload %s", file_path)

        # Remove empty collection directories
        try:
            if not os.listdir(collection_path):
                shutil.rmtree(collection_path, ignore_errors=True)
                removed_dirs += 1
        except OSError:
            pass

    if removed_files or removed_dirs:
        logger.info(
            "Knowledge source upload cleanup: removed %d file(s), %d empty dir(s)",
            removed_files,
            removed_dirs,
        )

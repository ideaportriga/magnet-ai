import logging
from typing import Any, override

from litestar.exceptions import ClientException
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.knowledge_graph import KnowledgeGraphSource
from services.observability import observability_context, observe

from ...models import SourceType, SyncPipelineConfig
from ..abstract_source import AbstractDataSource
from ..provider_utils import get_kg_provider, resolve_provider_params
from .confluence_models import ConfluenceRuntimeConfig
from .confluence_sync import ConfluenceSyncPipeline

logger = logging.getLogger(__name__)


class ConfluenceSource(AbstractDataSource):
    """Confluence pages source for Knowledge Graph.

    Credentials are resolved from a referenced Knowledge Source provider record
    (stored in ``source.config['ks_provider_id']``).

    Provider fields (set in the Knowledge Source Provider UI):
    - ``endpoint`` (required): Confluence instance base URL,
      e.g. ``https://mycompany.atlassian.net``
    - ``connection_config`` — non-sensitive identifiers (visible in UI):
        - ``username``: Confluence login e-mail / username
    - ``secrets_encrypted`` — sensitive credentials (stored encrypted):
        - ``token``: Confluence API token (Cloud) or password (Server/DC)

    Per-source config (``source.config``):
    - ``ks_provider_id`` (required): UUID of the KS provider that holds Confluence
      credentials.
    - ``space_key`` (required): Confluence space key, e.g. ``ENG``.
    - ``include_root_prefix`` (optional, default ``True``): prepend the root ancestor
      page title to each page title (mirrors legacy behaviour).
    - ``metadata_fields`` (optional): comma-separated metadata field labels to store
      on each document (e.g. ``"title,version_when,created_date"``).

    Concurrency model:
    - One listing worker that paginates through the Confluence space.
    - Two content-fetch workers that resolve root-ancestor title prefixes.
    - Three document-processing workers that embed and store pages.
    """

    LISTING_QUEUE_MAX = 100
    CONTENT_FETCH_QUEUE_MAX = 10_000
    DOCUMENT_PROCESSING_QUEUE_MAX = 100

    LISTING_WORKERS = 1
    CONTENT_FETCH_WORKERS = 2
    DOCUMENT_PROCESSING_WORKERS = 3

    def __init__(self, source: KnowledgeGraphSource) -> None:
        if source.type != SourceType.CONFLUENCE:
            raise ValueError("Source must be a Confluence source")
        super().__init__(source)

    @override
    @observe(name="Sync Confluence source")
    async def sync_source(self, db_session: AsyncSession) -> dict[str, Any]:
        """Synchronize Confluence pages into the Knowledge Graph."""

        logger.info(
            "Confluence sync started",
            extra={
                "graph_id": str(self.source.graph_id),
                "source_id": str(self.source.id),
            },
        )

        cfg = await self._get_sync_config(db_session)
        embedding_model = await self._require_embedding_model(db_session)

        observability_context.update_current_span(
            input={
                "source_id": str(self.source.id),
                "space_key": cfg.space_key,
            }
        )

        pipeline = ConfluenceSyncPipeline(
            source=self,
            pipeline_config=SyncPipelineConfig(
                name="confluence",
                listing_queue_max=int(self.LISTING_QUEUE_MAX),
                content_fetch_queue_max=int(self.CONTENT_FETCH_QUEUE_MAX),
                document_processing_queue_max=int(self.DOCUMENT_PROCESSING_QUEUE_MAX),
                listing_workers=max(1, int(self.LISTING_WORKERS)),
                content_fetch_workers=max(1, int(self.CONTENT_FETCH_WORKERS)),
                document_processing_workers=max(
                    1, int(self.DOCUMENT_PROCESSING_WORKERS)
                ),
                semaphores={"confluence": 2},
            ),
            confluence_config=cfg,
            embedding_model=embedding_model,
        )

        try:
            counters = await pipeline.run()
        except Exception as e:  # noqa: BLE001
            logger.error(
                "Confluence sync failed",
                extra={
                    "graph_id": str(self.source.graph_id),
                    "source_id": str(self.source.id),
                    "error": e,
                },
            )
            raise

        await self._finalize(db_session, counters=counters)

        summary = {
            "source_id": str(self.source.id),
            "documents_created": counters.content_changed,
            "documents_metadata_updated_only": counters.metadata_only_updated,
            "documents_content_changed": counters.content_changed,
            "documents_unchanged": counters.unchanged_skipped,
            "documents_failed": counters.failed,
            "documents_deleted": counters.deleted,
            "total_in_source": counters.total_found,
            "status": self.source.status,
            "last_sync_at": self.source.last_sync_at,
        }

        logger.info("Confluence sync completed", extra=summary)
        observability_context.update_current_span(output=summary)
        return summary

    async def _get_sync_config(
        self, db_session: AsyncSession
    ) -> ConfluenceRuntimeConfig:
        """Resolve credentials from the referenced KS provider and merge with source config."""
        cfg = self.source.config or {}

        # --- KS provider lookup + credential resolution ---
        provider = await get_kg_provider(db_session, cfg, expected_type="confluence")
        # params = resolved connection_config (placeholders injected) merged with secrets.
        # Non-sensitive values (username) belong in connection_config;
        # sensitive values (token) in secrets_encrypted.
        # Both are accessible transparently via params.
        params = resolve_provider_params(provider)

        endpoint: str = params.get("endpoint") or ""
        if not endpoint:
            raise ClientException(
                f"Confluence provider '{provider.name}' has no Endpoint configured. "
                "Set the Endpoint to the Confluence instance URL, "
                "e.g. https://mycompany.atlassian.net"
            )

        username: str = params.get("username") or ""
        token: str = params.get("token") or ""

        if not token:
            raise ClientException(
                f"Confluence provider '{provider.name}' has no API token configured. "
                "Add the Confluence API token to the provider's secrets."
            )

        # --- Source-level config ---
        space_key: str = cfg.get("space_key") or ""
        if not space_key.strip():
            raise ClientException(
                "Confluence source is missing 'space_key'. "
                "Provide the Confluence space key, e.g. 'ENG'."
            )

        include_root_prefix: bool = bool(cfg.get("include_root_prefix", True))
        metadata_fields: str = (
            cfg.get("metadata_fields") or "title,version_when,created_date"
        )

        return ConfluenceRuntimeConfig(
            endpoint=endpoint.rstrip("/"),
            username=username,
            token=token,
            space_key=space_key.strip(),
            include_root_prefix=include_root_prefix,
            metadata_fields=metadata_fields,
        )

import logging
import re
from typing import Any, override
from uuid import UUID

from litestar.exceptions import ClientException
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.knowledge_graph import KnowledgeGraphSource
from services.observability import observability_context, observe

from ...models import SourceType, SyncPipelineConfig
from ..abstract_source import AbstractDataSource
from .salesforce_models import SalesforceRuntimeConfig
from .salesforce_sync import SalesforceSyncPipeline

logger = logging.getLogger(__name__)

_OBJECT_API_NAME_RE = re.compile(r"^[a-zA-Z][a-zA-Z0-9]*(?:_[a-zA-Z0-9]+)*__kav$")
_DEFAULT_OBJECT_API_NAME = "Knowledge__kav"


class SalesforceSource(AbstractDataSource):
    """Salesforce Knowledge Articles source for Knowledge Graph.

    Credentials are resolved from a referenced Knowledge Source provider record
    (stored in ``source.config['ks_provider_id']``).  The provider record is expected
    to have the following ``secrets_encrypted`` fields:
    - ``username``
    - ``password``
    - ``security_token``

    Per-source config (``source.config``):
    - ``ks_provider_id`` (required): UUID of the KS provider that holds Salesforce credentials.
    - ``object_api_name`` (optional, default ``"Knowledge__kav"``): Salesforce Knowledge
      Article View object API name.
    - ``output_config`` (required): a single Python-style format-string template referencing
      field names in curly braces, e.g. ``"question: {Question__c}\\nanswer: {Answer__c}"``.

    Concurrency model:
    - One listing worker that issues a single SOQL ``query_all`` call.
    - One trivial content-fetch pass-through worker.
    - Three document-processing workers.
    """

    LISTING_QUEUE_MAX = 1
    CONTENT_FETCH_QUEUE_MAX = 10_000
    DOCUMENT_PROCESSING_QUEUE_MAX = 100

    LISTING_WORKERS = 1
    CONTENT_FETCH_WORKERS = 1
    DOCUMENT_PROCESSING_WORKERS = 3

    def __init__(self, source: KnowledgeGraphSource) -> None:
        if source.type != SourceType.SALESFORCE:
            raise ValueError("Source must be a Salesforce source")
        super().__init__(source)

    @override
    @observe(name="Sync Salesforce source")
    async def sync_source(self, db_session: AsyncSession) -> dict[str, Any]:
        """Synchronize Salesforce Knowledge Articles into the Knowledge Graph."""

        logger.info(
            "Salesforce sync started",
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
                "object_api_name": cfg.object_api_name,
            }
        )

        pipeline = SalesforceSyncPipeline(
            source=self,
            pipeline_config=SyncPipelineConfig(
                name="salesforce",
                listing_queue_max=int(self.LISTING_QUEUE_MAX),
                content_fetch_queue_max=int(self.CONTENT_FETCH_QUEUE_MAX),
                document_processing_queue_max=int(self.DOCUMENT_PROCESSING_QUEUE_MAX),
                listing_workers=max(1, int(self.LISTING_WORKERS)),
                content_fetch_workers=max(1, int(self.CONTENT_FETCH_WORKERS)),
                document_processing_workers=max(
                    1, int(self.DOCUMENT_PROCESSING_WORKERS)
                ),
                semaphores={"salesforce": 1},
            ),
            salesforce_config=cfg,
            embedding_model=embedding_model,
        )

        try:
            counters = await pipeline.run()
        except Exception as e:  # noqa: BLE001
            logger.error(
                "Salesforce sync failed",
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

        logger.info("Salesforce sync completed", extra=summary)
        observability_context.update_current_span(output=summary)
        return summary

    async def _get_sync_config(
        self, db_session: AsyncSession
    ) -> SalesforceRuntimeConfig:
        """Resolve credentials from the referenced KS provider and merge with source config."""

        from core.domain.providers.service import ProvidersService

        cfg = self.source.config or {}

        # --- KS provider lookup ---
        ks_provider_id: str | None = cfg.get("ks_provider_id")
        if not ks_provider_id:
            raise ClientException(
                "Salesforce source is missing 'ks_provider_id' in config. "
                "Select a Salesforce Knowledge Source provider."
            )

        try:
            provider_uuid = UUID(ks_provider_id)
        except ValueError as exc:
            raise ClientException(
                f"Salesforce source has invalid 'ks_provider_id': {ks_provider_id}"
            ) from exc

        providers_service = ProvidersService(session=db_session)
        try:
            provider = await providers_service.get(provider_uuid)
        except Exception as exc:
            raise ClientException(
                f"Knowledge Source provider '{ks_provider_id}' not found."
            ) from exc

        if provider.type.lower() != "salesforce":
            raise ClientException(
                f"Provider '{provider.name}' has type '{provider.type}', expected 'salesforce'."
            )

        secrets: dict[str, Any] = provider.secrets_encrypted or {}
        # conn_cfg: dict[str, Any] = provider.connection_config or {}

        # --- Auth flow resolution ---
        # Primary: Client Credentials (client_id + client_secret)
        client_id = secrets.get("client_id") or ""
        client_secret = secrets.get("client_secret") or ""

        # Fallback: Username/Password/Security Token
        username = secrets.get("username") or ""
        password = secrets.get("password") or ""
        security_token = secrets.get("security_token") or ""

        if client_id and client_secret:
            # Client credentials flow — ready
            pass
        elif username and password and security_token:
            # Password flow — ready
            pass
        else:
            raise ClientException(
                f"Salesforce provider '{provider.name}' has incomplete credentials. "
                "Provide either (client_id + client_secret) for Client Credentials flow "
                "or (username + password + security_token) for Password flow."
            )

        # Domain: parse from provider.endpoint (e.g. https://xxx.my.salesforce.com → xxx.my)
        if not provider.endpoint:
            raise ClientException(
                f"Salesforce provider '{provider.name}' has no Endpoint configured. "
                "Set the Endpoint to the full Salesforce instance URL, "
                "e.g. https://your-org.develop.my.salesforce.com"
            )

        from urllib.parse import urlparse

        hostname = urlparse(provider.endpoint).hostname or ""
        sf_suffix = ".salesforce.com"
        if hostname.lower().endswith(sf_suffix):
            domain: str = hostname[: -len(sf_suffix)]
        elif hostname:
            domain = hostname
        else:
            raise ClientException(
                f"Salesforce provider '{provider.name}' has an invalid Endpoint URL: "
                f"'{provider.endpoint}'. Expected a URL like "
                "https://your-org.my.salesforce.com"
            )

        # --- Source-level config ---
        object_api_name: str = cfg.get("object_api_name") or _DEFAULT_OBJECT_API_NAME
        if not _OBJECT_API_NAME_RE.match(object_api_name):
            raise ClientException(
                f"Invalid Salesforce object API name '{object_api_name}'. "
                "Must match the pattern <Name>__kav (Knowledge Article View)."
            )

        output_config: str = cfg.get("output_config") or ""
        if not output_config.strip():
            raise ClientException(
                "Salesforce source is missing 'output_config'. "
                "Provide a template string referencing article fields, e.g. "
                "'{Question__c}\\n{Answer__c}'."
            )

        article_id_field: str = cfg.get("article_id_field") or "ArticleNumber"
        title_field: str = cfg.get("title_field") or "Title"

        # metadata_fields: stored as comma-separated string, passed through as-is
        metadata_fields: str = (
            cfg.get("metadata_fields") or "Title, CreatedDate, LastModifiedDate"
        )

        return SalesforceRuntimeConfig(
            client_id=client_id or None,
            client_secret=client_secret or None,
            username=username or None,
            password=password or None,
            security_token=security_token or None,
            domain=domain,
            object_api_name=object_api_name,
            output_config=output_config,
            article_id_field=article_id_field,
            title_field=title_field,
            metadata_fields=metadata_fields,
        )

import re
from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True)
class SalesforceRuntimeConfig:
    """Resolved configuration for a single Salesforce sync run.

    Authentication is determined by which credentials are present:
    - **Client Credentials** (primary): ``client_id`` + ``client_secret``.
      Uses OAuth 2.0 client credentials flow (no user context required).
    - **Password flow** (fallback): ``username`` + ``password`` + ``security_token``.
      Used when ``client_id``/``client_secret`` are absent.

    ``domain`` selects the Salesforce login host:
    - ``"login"`` (default) — production
    - ``"test"`` — sandbox / developer edition
    """

    object_api_name: str  # e.g. "Knowledge__kav"
    output_config: str  # single template string, e.g. "{Summary}"
    domain: str = "login"  # 'login' (production) or 'test' (sandbox)

    # Configurable standard field names
    article_id_field: str = "ArticleNumber"  # stable identifier across versions (vs "Id" which is version-specific)
    title_field: str = "Title"  # field used as document title

    # Extra fields to store as document metadata, as a comma-separated string
    metadata_fields: str = "Title, CreatedDate, LastModifiedDate"

    # Optional URL template for generating external_link per article
    external_url_template: str = ""

    @property
    def metadata_fields_list(self) -> list[str]:
        """Parsed list of metadata field names."""
        return [f.strip() for f in self.metadata_fields.split(",") if f.strip()]

    # Client Credentials flow (primary)
    client_id: str | None = None
    client_secret: str | None = None

    # Password flow (fallback)
    username: str | None = None
    password: str | None = None
    security_token: str | None = None

    @property
    def auth_flow(self) -> Literal["client_credentials", "password"]:
        """Which OAuth flow will be used for this config."""
        if self.client_id and self.client_secret:
            return "client_credentials"
        return "password"

    @property
    def columns_to_select(self) -> list[str]:
        """Extract unique field names referenced in output_config template."""
        return list(dict.fromkeys(re.findall(r"\{([^}]+)\}", self.output_config)))

    @property
    def url_columns_to_select(self) -> list[str]:
        """Extract unique field names referenced in external_url_template."""
        if not self.external_url_template:
            return []
        return list(
            dict.fromkeys(re.findall(r"\{([^}]+)\}", self.external_url_template))
        )

    def format_record(self, record: dict[str, Any]) -> str:
        """Render the output template with actual record field values.

        Missing fields are silently replaced with an empty string rather than
        raising KeyError, so a misconfigured output_config produces degraded
        content rather than skipping the document entirely.
        """
        safe = defaultdict(str, {k: "" if v is None else v for k, v in record.items()})
        return self.output_config.format_map(safe)

    def format_external_url(self, record: dict[str, Any]) -> str | None:
        """Render external_url_template with record field values, or None if not configured."""
        if not self.external_url_template:
            return None
        safe = defaultdict(str, {k: "" if v is None else v for k, v in record.items()})
        return self.external_url_template.format_map(safe)


@dataclass(frozen=True)
class SalesforceListingTask:
    """Task that triggers the Salesforce SOQL query (one per sync)."""


@dataclass(frozen=True)
class SalesforceRecordTask:
    """Task for the document processing stage — one per Knowledge Article record."""

    record: dict[str, Any]

from dataclasses import dataclass


@dataclass(frozen=True)
class ConfluenceRuntimeConfig:
    """Resolved configuration for a single Confluence sync run.

    Credentials are resolved from a referenced Knowledge Source provider record
    (stored in ``source.config['ks_provider_id']``).

    Provider fields (set in the Knowledge Source Provider UI):
    - ``endpoint``: Confluence instance URL,
      e.g. ``https://mycompany.atlassian.net``
    - ``connection_config``:
        - ``username``: Confluence login e-mail / username
    - ``secrets_encrypted``:
        - ``token``: Confluence API token (Cloud) or password (Server/DC)

    Per-source config (``source.config``):
    - ``ks_provider_id`` (required): UUID of the KS provider with Confluence credentials.
    - ``space_key`` (required): Confluence space key, e.g. ``ENG``.
    - ``include_root_prefix`` (optional, default ``True``): prepend root ancestor page
      title to each page title — mirrors legacy ``data_sources/confluence`` behaviour.
    - ``metadata_fields`` (optional): comma-separated list of extra metadata keys to
      store on each document.  Defaults to ``"title,version_when,created_date"``.
    """

    endpoint: str  # Confluence base URL (no trailing slash)
    username: str  # login e-mail / username
    token: str  # API token (Cloud) or password (Server/DC)
    space_key: str  # target Confluence space, e.g. "ENG"

    include_root_prefix: bool = True  # prepend root ancestor title to page titles

    # Extra metadata fields stored on each KG document (human-readable labels)
    metadata_fields: str = "title,version_when,created_date"

    @property
    def metadata_fields_list(self) -> list[str]:
        return [f.strip() for f in self.metadata_fields.split(",") if f.strip()]


@dataclass(frozen=True)
class ConfluenceListingPageTask:
    """Task that requests one page of results from ``get_all_pages_from_space``."""

    start: int = 0
    limit: int = 100


@dataclass(frozen=True)
class ConfluencePageFetchTask:
    """Task that carries a Confluence page's metadata to the content-fetch stage.

    The actual HTML body is already available from the listing response, so the
    content-fetch worker only needs to resolve the optional root-ancestor prefix.
    """

    page_id: str
    title: str  # raw page title (may be prefixed later if include_root_prefix=True)
    html_body: str  # body.storage.value from the listing response
    last_modified: str  # ISO-8601 from version.when
    created_at: str  # ISO-8601 from history.createdDate
    web_url: str  # _links.webui path (relative, e.g. "/wiki/spaces/ENG/pages/123")


@dataclass(frozen=True)
class ConfluenceProcessDocumentTask:
    """Task that carries a fully-resolved Confluence page ready for embedding."""

    page_id: str
    title: str  # final title (possibly prefixed with root ancestor)
    html_body: str  # HTML content to embed
    last_modified: str  # ISO-8601
    created_at: str  # ISO-8601
    web_url: str  # resolved source URL

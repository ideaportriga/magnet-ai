from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime
from typing import Any, cast
from uuid import UUID

from litestar.exceptions import ClientException
from office365.runtime.auth.authentication_context import AuthenticationContext
from office365.sharepoint.client_context import ClientContext
from office365.sharepoint.files.file import File, Folder

from core.config.base import get_knowledge_source_settings

from ...models import MetadataMultiValueContainer
from .sharepoint_models import SharePointFileRef, SharePointRuntimeConfig

logger = logging.getLogger(__name__)


def normalize_server_relative_url(url: str) -> str:
    """Normalize a server-relative URL/path for de-duplication/logging."""

    return str(url or "").strip().rstrip("/")


def resolve_sharepoint_site_url(cfg: dict[str, Any]) -> str:
    """Resolve SharePoint site URL from source config.

    Supported keys:
    - sharepoint_site_url / site_url (direct URL)
    - endpoint + site_path (plugin-style)
    """

    site_url = (cfg.get("sharepoint_site_url") or cfg.get("site_url") or "").strip()
    if site_url:
        return site_url.rstrip("/")

    endpoint = (cfg.get("endpoint") or "").strip().rstrip("/")
    site_path = (cfg.get("site_path") or "").strip().lstrip("/")
    if endpoint and site_path:
        return f"{endpoint}/{site_path}"

    return endpoint


def resolve_sharepoint_location(cfg: dict[str, Any]) -> tuple[str, str | None, bool]:
    """Resolve library/folder/recursive from source config.

    If library is 'SitePages', returns (SitePages, None, False) - pages mode.
    Otherwise uses configurable library/folder/recursive - documents mode.
    """
    from .sharepoint_models import SharePointLibrary

    library = (
        cfg.get("library") or cfg.get("sharepoint_library") or ""
    ).strip() or None

    # Pages mode: SitePages library, no folder, no recursion
    if library == SharePointLibrary.PAGES:
        return SharePointLibrary.PAGES, None, False

    # Documents mode: configurable library/folder/recursive
    folder = (
        cfg.get("folder_path") or cfg.get("sharepoint_folder") or ""
    ).strip() or None
    recursive_val = cfg.get("recursive", cfg.get("sharepoint_recursive", False))
    recursive = bool(recursive_val)

    if not library:
        library = SharePointLibrary.DOCUMENTS

    return library, folder, recursive


def resolve_sharepoint_auth(
    cfg: dict[str, Any],
) -> tuple[str, str | None, str | None, str | None, str | None]:
    """Resolve auth parameters from source config or environment.

    Returns: (client_id, client_secret, tenant, thumbprint, private_key)
    """

    settings = get_knowledge_source_settings()

    client_id = (
        cfg.get("client_id")
        or cfg.get("sharepoint_client_id")
        or settings.SHAREPOINT_CLIENT_ID
        or ""
    )
    client_secret = (
        cfg.get("client_secret")
        or cfg.get("sharepoint_client_secret")
        or settings.SHAREPOINT_CLIENT_SECRET
        or ""
    )
    tenant = (
        cfg.get("tenant")
        or cfg.get("sharepoint_tenant_id")
        or settings.SHAREPOINT_TENANT_ID
        or ""
    )
    thumbprint = (
        cfg.get("thumbprint")
        or cfg.get("sharepoint_client_cert_thumbprint")
        or settings.SHAREPOINT_CLIENT_CERT_THUMBPRINT
        or ""
    )
    private_key = (
        cfg.get("private_key")
        or cfg.get("sharepoint_client_cert_private_key")
        or settings.SHAREPOINT_CLIENT_CERT_PRIVATE_KEY
        or ""
    )

    client_id = str(client_id).strip()
    client_secret = str(client_secret).strip()
    tenant = str(tenant).strip()
    thumbprint = str(thumbprint).strip()
    private_key = str(private_key).strip()

    if private_key:
        private_key = private_key.replace("\\n", "\n")

    return (
        client_id,
        (client_secret or None),
        (tenant or None),
        (thumbprint or None),
        (private_key or None),
    )


def validate_sharepoint_runtime_config(cfg: SharePointRuntimeConfig) -> None:
    if not cfg.site_url or not str(cfg.site_url).strip():
        raise ClientException("SharePoint site URL is required in source.config")

    if not cfg.client_id or not str(cfg.client_id).strip():
        raise ClientException(
            "SharePoint client_id is missing (set in source.config or SHAREPOINT_CLIENT_ID env)."
        )

    has_secret = bool(cfg.client_secret and cfg.client_secret.strip())
    has_cert = bool(
        cfg.tenant
        and cfg.thumbprint
        and cfg.private_key
        and cfg.tenant.strip()
        and cfg.thumbprint.strip()
        and cfg.private_key.strip()
    )

    if not (has_secret or has_cert):
        raise ClientException(
            "SharePoint credentials are missing: provide client_secret or (tenant, thumbprint, private_key)."
        )


def _create_sharepoint_context_sync(cfg: SharePointRuntimeConfig) -> ClientContext:
    """Create an authenticated SharePoint ClientContext (sync, blocking)."""

    auth_ctx = AuthenticationContext(url=cfg.site_url)
    if cfg.client_secret:
        auth_ctx.acquire_token_for_app(
            client_id=cfg.client_id,
            client_secret=cfg.client_secret,
        )
    else:
        auth_ctx.with_client_certificate(
            tenant=cast(str, cfg.tenant),
            client_id=cfg.client_id,
            thumbprint=cast(str, cfg.thumbprint),
            private_key=cast(str, cfg.private_key),
        )

    return ClientContext(cfg.site_url, auth_ctx)


async def create_sharepoint_context(cfg: SharePointRuntimeConfig) -> ClientContext:
    """Async wrapper around SharePoint auth/context creation."""

    return await asyncio.to_thread(_create_sharepoint_context_sync, cfg)


def _folder_name(cfg: SharePointRuntimeConfig) -> str:
    if cfg.folder:
        return f"{cfg.library}/{cfg.folder}"
    return cfg.library


def get_root_folder_server_relative_url(cfg: SharePointRuntimeConfig) -> str:
    """Return the configured root folder path/url for listing."""

    return _folder_name(cfg)


def _get_folder_files_sync(
    ctx: ClientContext, *, folder_name: str, recursive: bool
) -> list[File]:
    folder = ctx.web.get_folder_by_server_relative_url(folder_name)
    files: list[File] = []

    if recursive:

        def process_folder(current_folder: Folder) -> None:
            current_folder.expand(["Files", "Folders"]).get().execute_query_retry()
            if current_folder.files and len(current_folder.files) > 0:
                files.extend(cast(list[File], current_folder.files))
            if current_folder.folders:
                for subfolder in current_folder.folders:
                    process_folder(subfolder)

        process_folder(folder)
        return files

    folder.expand(["Files"]).get().execute_query_retry()
    if folder.files and len(folder.files) > 0:
        files.extend(cast(list[File], folder.files))
    return files


def _file_ref_from_office365_file(file: File) -> SharePointFileRef | None:
    name = str(getattr(file, "name", "") or "").strip()
    if not name:
        return None

    # Different office365 versions expose different shapes; try best-effort.
    server_relative_url = (
        getattr(file, "serverRelativeUrl", None)
        or getattr(file, "server_relative_url", None)
        or None
    )
    if not server_relative_url:
        props = getattr(file, "properties", None) or {}
        if isinstance(props, dict):
            server_relative_url = props.get("ServerRelativeUrl") or props.get(
                "serverRelativeUrl"
            )
            if not server_relative_url:
                srp = props.get("ServerRelativePath") or props.get("serverRelativePath")
                if isinstance(srp, dict):
                    server_relative_url = srp.get("DecodedUrl") or srp.get("decodedUrl")
                else:
                    # Some versions use a ResourcePath-like object with DecodedUrl attribute
                    server_relative_url = getattr(srp, "DecodedUrl", None) or getattr(
                        srp, "decodedUrl", None
                    )

    server_relative_url = str(server_relative_url or "").strip()
    if not server_relative_url:
        return None

    return SharePointFileRef(name=name, server_relative_url=server_relative_url)


def _file_ref_from_office365_file_with_parent(
    file: File, *, parent_folder_url: str
) -> SharePointFileRef | None:
    """Build a SharePointFileRef, falling back to parent_folder_url/name when needed."""

    name = str(getattr(file, "name", "") or "").strip()
    if not name:
        # Some versions store Name only in properties
        props = getattr(file, "properties", None) or {}
        if isinstance(props, dict):
            name = str(props.get("Name") or props.get("name") or "").strip()
    if not name:
        return None

    base = normalize_server_relative_url(parent_folder_url)
    ref = _file_ref_from_office365_file(file)
    if ref:
        return ref

    # Best-effort: construct URL from folder + filename
    return SharePointFileRef(name=name, server_relative_url=f"{base}/{name}")


def _folder_ref_from_office365_folder(
    folder: Folder, *, parent_folder_url: str
) -> str | None:
    """Return server-relative URL for a Folder, falling back to parent/name when needed."""

    name = str(getattr(folder, "name", "") or "").strip()

    server_relative_url = (
        getattr(folder, "serverRelativeUrl", None)
        or getattr(folder, "server_relative_url", None)
        or None
    )
    if not server_relative_url:
        props = getattr(folder, "properties", None) or {}
        if isinstance(props, dict):
            server_relative_url = props.get("ServerRelativeUrl") or props.get(
                "serverRelativeUrl"
            )
            if not name:
                name = str(props.get("Name") or props.get("name") or "").strip()
            if not server_relative_url:
                srp = props.get("ServerRelativePath") or props.get("serverRelativePath")
                if isinstance(srp, dict):
                    server_relative_url = srp.get("DecodedUrl") or srp.get("decodedUrl")
                else:
                    server_relative_url = getattr(srp, "DecodedUrl", None) or getattr(
                        srp, "decodedUrl", None
                    )

    server_relative_url = str(server_relative_url or "").strip()
    if server_relative_url:
        return server_relative_url

    name = str(name or "").strip()
    if not name:
        return None

    base = normalize_server_relative_url(parent_folder_url)
    return f"{base}/{name}"


def _get_folder_children_sync(
    ctx: ClientContext, *, folder_server_relative_url: str
) -> tuple[list[File], list[Folder]]:
    """Return immediate (files, subfolders) for a single folder (sync, blocking)."""

    folder = ctx.web.get_folder_by_server_relative_url(folder_server_relative_url)
    folder.expand(["Files", "Folders"]).get().execute_query_retry()

    files: list[File] = []
    folders: list[Folder] = []

    if folder.files and len(folder.files) > 0:
        files.extend(cast(list[File], folder.files))

    if folder.folders and len(folder.folders) > 0:
        folders.extend(cast(list[Folder], folder.folders))

    return files, folders


async def list_sharepoint_folder_children(
    ctx: ClientContext,
    *,
    folder_server_relative_url: str,
) -> tuple[list[SharePointFileRef], list[str]]:
    """List immediate files + subfolders for a single folder (non-recursive)."""

    folder_url = normalize_server_relative_url(folder_server_relative_url)
    if not folder_url:
        raise ClientException("SharePoint folder_server_relative_url is required")

    files, folders = await asyncio.to_thread(
        _get_folder_children_sync,
        ctx,
        folder_server_relative_url=folder_url,
    )

    file_refs: list[SharePointFileRef] = []
    for f in files:
        ref = _file_ref_from_office365_file_with_parent(f, parent_folder_url=folder_url)
        if not ref:
            continue

        file_refs.append(ref)

    folder_refs: list[str] = []
    for sub in folders:
        sub_url = _folder_ref_from_office365_folder(sub, parent_folder_url=folder_url)
        if not sub_url:
            continue
        folder_refs.append(sub_url)

    return file_refs, folder_refs


async def list_sharepoint_files(
    ctx: ClientContext, *, cfg: SharePointRuntimeConfig
) -> list[SharePointFileRef]:
    """List files in the configured library/folder."""

    folder_name = _folder_name(cfg)
    files = await asyncio.to_thread(
        _get_folder_files_sync, ctx, folder_name=folder_name, recursive=cfg.recursive
    )

    out: list[SharePointFileRef] = []
    for f in files:
        ref = _file_ref_from_office365_file(f)
        if not ref:
            continue

        out.append(ref)

    return out


def _download_file_bytes_sync(ctx: ClientContext, *, server_relative_url: str) -> bytes:
    # For some versions of office365, File.download can return empty content in certain threading
    # contexts. Using get_content is more reliable (mirrors existing implementation elsewhere).
    f = ctx.web.get_file_by_server_relative_url(server_relative_url)
    content = f.get_content().execute_query()
    raw = getattr(content, "value", b"")
    if isinstance(raw, (bytes, bytearray)):
        return bytes(raw)
    return bytes(raw or b"")


async def download_sharepoint_file_bytes(
    ctx: ClientContext, *, server_relative_url: str
) -> bytes:
    """Download file bytes by server-relative URL."""

    if not server_relative_url:
        raise ClientException(
            "Missing SharePoint server_relative_url for file download"
        )

    return await asyncio.to_thread(
        _download_file_bytes_sync, ctx, server_relative_url=server_relative_url
    )


def _is_simple_scalar(value: Any) -> bool:
    return value is None or isinstance(
        value, (str, bool, int, float, datetime, date, UUID)
    )


def _extract_sharepoint_choice_values(value: Any) -> list[Any] | None:
    """Best-effort extraction of multi-choice values from SharePoint list item fields."""

    if value is None or isinstance(value, MetadataMultiValueContainer):
        return None

    if isinstance(value, dict):
        # SharePoint choice fields come back as an index->value mapping:
        # {0: "Choice 3", 1: "Choice 2"} (or {"0": "...", "1": "..."})
        indexed_items: list[tuple[int, Any]] = []
        for k, v in value.items():
            if isinstance(k, int):
                idx = k
            elif isinstance(k, str) and k.strip().isdigit():
                idx = int(k.strip())
            else:
                indexed_items = []
                break
            indexed_items.append((idx, v))

        if indexed_items and all(_is_simple_scalar(v) for _, v in indexed_items):
            indexed_items.sort(key=lambda t: t[0])
            return [v for _, v in indexed_items]

        return None

    return None


def _normalize_sharepoint_choice_fields(metadata: dict[str, Any]) -> None:
    """Wrap detected SharePoint multi-choice values in `MetadataMultiValueContainer`."""
    for key, value in list((metadata or {}).items()):
        values = _extract_sharepoint_choice_values(value)
        if values is None:
            continue
        metadata[key] = MetadataMultiValueContainer.from_iterable(values)


def _fetch_file_list_item_fields_sync(
    ctx: ClientContext, *, server_relative_url: str
) -> dict[str, Any]:
    """Fetch SharePoint list item fields for a file (sync, blocking).

    This mirrors the legacy SharePoint processor behavior, returning a dict of
    list-item properties with a few noisy/large fields removed.
    """
    f = ctx.web.get_file_by_server_relative_url(server_relative_url)

    list_item = (
        getattr(f, "listItemAllFields", None)
        or getattr(f, "list_item_all_fields", None)
        or None
    )
    if not list_item:
        return {}

    # Load fields
    list_item.get().execute_query()

    props = getattr(list_item, "properties", None) or {}
    if not isinstance(props, dict):
        return {}

    # Remove noisy / large fields (legacy behavior)
    cleaned = dict(props)
    cleaned.pop("ParentList", None)
    cleaned.pop("CanvasContent1", None)
    cleaned.pop("ComplianceAssetId", None)
    cleaned.pop("OData__AuthorBylineId", None)
    cleaned.pop("OData__UIVersionString", None)
    cleaned.pop("OData__ColorTag", None)
    cleaned.pop("OData__CopySource", None)
    cleaned.pop("_AuthorBylineStringId", None)
    cleaned.pop("FileSystemObjectType", None)
    cleaned.pop("EditorId", None)
    cleaned.pop("AuthorId", None)
    cleaned.pop("ContentTypeId", None)
    cleaned.pop("CheckoutUserId", None)
    cleaned.pop("Id", None)
    cleaned.pop("ID", None)
    cleaned.pop("GUID", None)
    cleaned.pop("ServerRedirectedEmbedUri", None)
    cleaned.pop("ServerRedirectedEmbedUrl", None)

    # Try to find choice fields and convert them to special MetadataMultiValueContainer object
    _normalize_sharepoint_choice_fields(cleaned)

    return cleaned


async def fetch_sharepoint_file_list_item_fields(
    ctx: ClientContext, *, server_relative_url: str
) -> dict[str, Any]:
    """Fetch list item fields/properties for a SharePoint file by server-relative URL."""
    if not server_relative_url:
        raise ClientException(
            "Missing SharePoint server_relative_url for file metadata fetch"
        )

    return await asyncio.to_thread(
        _fetch_file_list_item_fields_sync, ctx, server_relative_url=server_relative_url
    )


async def fetch_sharepoint_page_content(
    ctx: ClientContext, *, server_relative_url: str
) -> str | None:
    """Fetch CanvasContent1 (HTML content) for a SharePoint .aspx page."""
    if not server_relative_url:
        return None

    def _fetch_sync() -> str | None:
        f = ctx.web.get_file_by_server_relative_url(server_relative_url)
        list_item = (
            getattr(f, "listItemAllFields", None)
            or getattr(f, "list_item_all_fields", None)
            or None
        )
        if not list_item:
            return None

        list_item.select(["CanvasContent1"]).get().execute_query()
        props = getattr(list_item, "properties", None) or {}
        if not isinstance(props, dict):
            return None

        return props.get("CanvasContent1")

    return await asyncio.to_thread(_fetch_sync)

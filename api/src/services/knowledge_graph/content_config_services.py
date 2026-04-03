import fnmatch
import logging
from copy import deepcopy
from typing import Any
from uuid import UUID

from litestar.exceptions import ClientException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.db.models.knowledge_graph import KnowledgeGraph

from .models import (
    ChunkContentType,
    ChunkerStrategy,
    ContentConfig,
    ContentReaderName,
    SourceType,
)

logger = logging.getLogger(__name__)

ALL_SOURCES_KEY = "__ALL__"
NONE_SELECTED_KEY = "__NONE__"
GROUP_KEY_PREFIX = "__GROUP__"
VIRTUAL_LAST_RESORT_PROFILE_NAME = "<default>"
VIRTUAL_LAST_RESORT_PROFILE_KEY = "_virtual_profile"
VIRTUAL_LAST_RESORT_PROFILE_VALUE = "fallback_plain_text"
FLUID_TOPICS_STRUCTURED_PROFILE_NAME = "Fluid Topics Native Format"
FLUID_TOPICS_STRUCTURED_AUTO_MANAGED_KEY = "_auto_managed_profile"
FLUID_TOPICS_STRUCTURED_AUTO_MANAGED_VALUE = str(
    ContentReaderName.FLUID_TOPICS_STRUCTURED_DOCUMENTS
)
FLUID_TOPICS_SOURCE_SELECTOR = f"{GROUP_KEY_PREFIX}{SourceType.FLUID_TOPICS}"
SHAREPOINT_PAGES_PROFILE_NAME = "SharePoint Pages (LLM Chunking)"
SHAREPOINT_VIDEO_TRANSCRIPTION_PROFILE_NAME = "SharePoint Video Transcription"
SHAREPOINT_SOURCE_SELECTOR = f"{GROUP_KEY_PREFIX}{SourceType.SHAREPOINT}"
SHAREPOINT_PAGE_PROMPT_TEMPLATE_SYSTEM_NAME = "SHAREPOINT_PAGE_CHUNKING"
FLUID_TOPICS_STRUCTURED_EDITABLE_CHUNKER_OPTION_KEYS = (
    "document_title_pattern",
    "chunk_title_pattern",
    "chunk_max_size",
    "chunk_content_type",
)


def clone_graph_settings(settings: dict[str, Any] | None) -> dict[str, Any]:
    """Return a deep-copied graph settings payload safe for JSON reassignment."""

    if not isinstance(settings, dict):
        return {}
    return deepcopy(settings)


def _parse_group_selector(selector: str) -> str | None:
    if selector.startswith(GROUP_KEY_PREFIX):
        return selector[len(GROUP_KEY_PREFIX) :]
    return None


def _matches_source_selector(
    selectors: list[str], source_id: str | None, source_type: str | None
) -> bool:
    """Return whether a stored selector list matches the current source.

    Selectors can contain:
    - concrete source ids
    - ``__GROUP__<type>`` virtual group selectors
    - ``__ALL__`` wildcard selector
    - ``__NONE__`` explicit match-nothing selector
    """

    if not selectors:
        return True

    normalized_selectors = {str(selector) for selector in selectors if selector}
    if not normalized_selectors:
        return True

    if NONE_SELECTED_KEY in normalized_selectors:
        return False

    if ALL_SOURCES_KEY in normalized_selectors:
        return True

    normalized_source_id = str(source_id) if source_id else None
    if normalized_source_id and normalized_source_id in normalized_selectors:
        return True

    normalized_source_type = str(source_type) if source_type else None
    if not normalized_source_type:
        return False

    return any(
        _parse_group_selector(selector) == normalized_source_type
        for selector in normalized_selectors
    )


def _get_reader_name(config: ContentConfig) -> str:
    if not config.reader:
        return ""

    reader_name = config.reader.get("name")
    return str(reader_name).strip().lower() if reader_name is not None else ""


def _is_structured_content_reader(config: ContentConfig) -> bool:
    return _get_reader_name(config) == str(
        ContentReaderName.FLUID_TOPICS_STRUCTURED_DOCUMENTS
    )


def _matches_config_source(
    config: ContentConfig, *, source_id: str | None, source_type: str | None
) -> bool:
    if config.source_ids and len(config.source_ids) > 0:
        return _matches_source_selector(
            config.source_ids, source_id=source_id, source_type=source_type
        )

    if config.source_types and len(config.source_types) > 0:
        return bool(source_type) and str(source_type) in config.source_types

    return True


def _get_content_settings(settings: dict[str, Any]) -> list[dict[str, Any]]:
    chunking = settings.get("chunking")
    if not isinstance(chunking, dict):
        chunking = {}
        settings["chunking"] = chunking

    content_settings = chunking.get("content_settings")
    if not isinstance(content_settings, list):
        content_settings = []
        chunking["content_settings"] = content_settings

    return content_settings


def _get_raw_reader_name(config_dict: dict[str, Any]) -> str:
    if not isinstance(config_dict, dict):
        return ""

    reader = config_dict.get("reader")
    if not isinstance(reader, dict):
        return ""

    reader_name = reader.get("name")
    return str(reader_name).strip().lower() if reader_name is not None else ""


def _get_raw_profile_name(config_dict: dict[str, Any]) -> str:
    if not isinstance(config_dict, dict):
        return ""

    profile_name = config_dict.get("name")
    return str(profile_name).strip() if profile_name is not None else ""


def _get_raw_glob_pattern(config_dict: dict[str, Any]) -> str:
    if not isinstance(config_dict, dict):
        return ""

    glob_pattern = config_dict.get("glob_pattern")
    return str(glob_pattern).strip().lower() if glob_pattern is not None else ""


def _get_raw_source_ids(config_dict: dict[str, Any]) -> list[str]:
    if not isinstance(config_dict, dict):
        return []

    source_ids = config_dict.get("source_ids")
    if not isinstance(source_ids, list):
        return []

    return [str(source_id) for source_id in source_ids if source_id]


def _get_raw_source_types(config_dict: dict[str, Any]) -> list[str]:
    if not isinstance(config_dict, dict):
        return []

    source_types = config_dict.get("source_types")
    if not isinstance(source_types, list):
        return []

    return [str(source_type) for source_type in source_types if source_type]


def _has_reserved_fluid_topics_structured_profile_name(
    profile_name: str | None,
) -> bool:
    normalized_name = str(profile_name).strip().lower() if profile_name else ""
    return normalized_name == FLUID_TOPICS_STRUCTURED_PROFILE_NAME.strip().lower()


def _has_reserved_virtual_last_resort_profile_name(profile_name: str | None) -> bool:
    normalized_name = str(profile_name).strip().lower() if profile_name else ""
    return normalized_name == VIRTUAL_LAST_RESORT_PROFILE_NAME.strip().lower()


def _normalize_content_profile_name(profile_name: str | None) -> str:
    return str(profile_name).strip().lower() if profile_name else ""


def validate_unique_content_profile_names(settings: dict[str, Any]) -> None:
    content_settings = _get_content_settings(settings)
    seen_names: dict[str, str] = {}
    duplicate_names: list[str] = []

    for config_dict in content_settings:
        if not isinstance(config_dict, dict):
            continue

        raw_name = _get_raw_profile_name(config_dict)
        normalized_name = _normalize_content_profile_name(raw_name)
        if not normalized_name:
            continue

        existing_name = seen_names.get(normalized_name)
        if existing_name is None:
            seen_names[normalized_name] = raw_name
            continue

        if existing_name not in duplicate_names:
            duplicate_names.append(existing_name)

    if not duplicate_names:
        return

    duplicate_names_list = ", ".join(
        sorted(duplicate_names, key=lambda name: name.lower())
    )
    suffix = "s" if len(duplicate_names) > 1 else ""
    raise ClientException(
        f"Content profile name{suffix} must be unique. Duplicate name{suffix}: {duplicate_names_list}."
    )


def build_virtual_last_resort_content_config() -> ContentConfig:
    return ContentConfig(
        name=VIRTUAL_LAST_RESORT_PROFILE_NAME,
        enabled=True,
        glob_pattern="",
        reader={"name": ContentReaderName.PLAIN_TEXT, "options": {}},
        chunker={
            "strategy": ChunkerStrategy.NONE,
            "options": {
                "llm_batch_size": 15000,
                "llm_batch_overlap": 0.1,
                "llm_last_segment_increase": 0.0,
                "recursive_chunk_overlap": 0.1,
                "chunk_max_size": 15000,
                "splitters": ["\n\n", "\n", " ", ""],
                "prompt_template_system_name": "",
                "document_title_pattern": "",
                "chunk_title_pattern": "",
                "chunk_content_type": ChunkContentType.PLAIN_TEXT,
            },
        },
    )


def build_virtual_last_resort_content_config_dict() -> dict[str, Any]:
    config_dict = build_virtual_last_resort_content_config().model_dump()
    config_dict[VIRTUAL_LAST_RESORT_PROFILE_KEY] = VIRTUAL_LAST_RESORT_PROFILE_VALUE
    return config_dict


def is_virtual_last_resort_profile_candidate(config_dict: dict[str, Any]) -> bool:
    if not isinstance(config_dict, dict):
        return False

    if (
        config_dict.get(VIRTUAL_LAST_RESORT_PROFILE_KEY)
        == VIRTUAL_LAST_RESORT_PROFILE_VALUE
    ):
        return True

    return _has_reserved_virtual_last_resort_profile_name(
        _get_raw_profile_name(config_dict)
    )


def is_fluid_topics_structured_profile_candidate(config_dict: dict[str, Any]) -> bool:
    if not isinstance(config_dict, dict):
        return False

    return _get_raw_reader_name(config_dict) == str(
        ContentReaderName.FLUID_TOPICS_STRUCTURED_DOCUMENTS
    ) or _has_reserved_fluid_topics_structured_profile_name(
        _get_raw_profile_name(config_dict)
    )


def has_fluid_topics_structured_profile(
    content_settings: list[dict[str, Any]],
) -> bool:
    return any(
        is_fluid_topics_structured_profile_candidate(config_dict)
        for config_dict in content_settings
        if isinstance(config_dict, dict)
    )


def is_auto_managed_fluid_topics_structured_profile(
    config_dict: dict[str, Any],
) -> bool:
    if _get_raw_reader_name(config_dict) != str(
        ContentReaderName.FLUID_TOPICS_STRUCTURED_DOCUMENTS
    ):
        return False

    reader = config_dict.get("reader")
    options = reader.get("options") if isinstance(reader, dict) else None
    return (
        isinstance(options, dict)
        and options.get(FLUID_TOPICS_STRUCTURED_AUTO_MANAGED_KEY)
        == FLUID_TOPICS_STRUCTURED_AUTO_MANAGED_VALUE
    )


def is_sharepoint_pages_profile_candidate(config_dict: dict[str, Any]) -> bool:
    if not isinstance(config_dict, dict):
        return False

    if (
        _normalize_content_profile_name(_get_raw_profile_name(config_dict))
        == SHAREPOINT_PAGES_PROFILE_NAME.strip().lower()
    ):
        return True

    if _get_raw_glob_pattern(config_dict) != "*.aspx":
        return False

    source_ids = set(_get_raw_source_ids(config_dict))
    if SHAREPOINT_SOURCE_SELECTOR in source_ids:
        return True

    source_types = set(_get_raw_source_types(config_dict))
    if str(SourceType.SHAREPOINT) in source_types:
        return True

    return not source_ids and not source_types


def _is_plain_text_catchall_profile(config_dict: dict[str, Any]) -> bool:
    return (
        _get_raw_reader_name(config_dict) == str(ContentReaderName.PLAIN_TEXT)
        and not _get_raw_glob_pattern(config_dict)
        and not _get_raw_source_ids(config_dict)
        and not _get_raw_source_types(config_dict)
    )


def build_fluid_topics_structured_content_config() -> ContentConfig:
    return ContentConfig(
        name=FLUID_TOPICS_STRUCTURED_PROFILE_NAME,
        enabled=True,
        glob_pattern="",
        source_ids=[FLUID_TOPICS_SOURCE_SELECTOR],
        reader={
            "name": ContentReaderName.FLUID_TOPICS_STRUCTURED_DOCUMENTS,
            "options": {
                FLUID_TOPICS_STRUCTURED_AUTO_MANAGED_KEY: FLUID_TOPICS_STRUCTURED_AUTO_MANAGED_VALUE,
            },
        },
        chunker={
            "strategy": ChunkerStrategy.NONE,
            "options": {
                "llm_batch_size": 18000,
                "llm_batch_overlap": 0.1,
                "llm_last_segment_increase": 0.0,
                "recursive_chunk_overlap": 0.1,
                "chunk_max_size": 18000,
                "splitters": ["\n\n", "\n", " ", ""],
                "prompt_template_system_name": "",
                "document_title_pattern": "",
                "chunk_title_pattern": "",
                "chunk_content_type": ChunkContentType.HTML,
            },
        },
    )


def build_sharepoint_pages_content_config() -> ContentConfig:
    return ContentConfig(
        name=SHAREPOINT_PAGES_PROFILE_NAME,
        enabled=True,
        glob_pattern="*.aspx",
        source_ids=[SHAREPOINT_SOURCE_SELECTOR],
        reader={"name": ContentReaderName.SHAREPOINT_PAGE, "options": {}},
        chunker={
            "strategy": ChunkerStrategy.LLM,
            "options": {
                "llm_batch_size": 18000,
                "llm_batch_overlap": 0.1,
                "llm_last_segment_increase": 0.0,
                "recursive_chunk_overlap": 0.1,
                "chunk_max_size": 18000,
                "splitters": ["\n\n", "\n", " ", ""],
                "prompt_template_system_name": SHAREPOINT_PAGE_PROMPT_TEMPLATE_SYSTEM_NAME,
                "document_title_pattern": "",
                "chunk_title_pattern": "",
                "chunk_content_type": ChunkContentType.HTML,
            },
        },
    )


def ensure_sharepoint_pages_profile_backfill(
    content_settings: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    if any(
        is_sharepoint_pages_profile_candidate(config_dict)
        for config_dict in content_settings
        if isinstance(config_dict, dict)
    ):
        return content_settings

    canonical_profile = build_sharepoint_pages_content_config().model_dump()
    next_content_settings: list[dict[str, Any]] = []
    inserted = False

    for config_dict in content_settings:
        if (
            not inserted
            and isinstance(config_dict, dict)
            and _is_plain_text_catchall_profile(config_dict)
        ):
            next_content_settings.append(deepcopy(canonical_profile))
            inserted = True

        if isinstance(config_dict, dict):
            next_content_settings.append(deepcopy(config_dict))

    if not inserted:
        next_content_settings.append(deepcopy(canonical_profile))

    return next_content_settings


def _get_chunker_options_dict(config_dict: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(config_dict, dict):
        return {}

    chunker = config_dict.get("chunker")
    if not isinstance(chunker, dict):
        return {}

    options = chunker.get("options")
    return options if isinstance(options, dict) else {}


def _get_preserved_fluid_topics_structured_chunker_options(
    candidates: list[dict[str, Any]],
) -> dict[str, Any]:
    preserved_options: dict[str, Any] = {}

    for option_key in FLUID_TOPICS_STRUCTURED_EDITABLE_CHUNKER_OPTION_KEYS:
        for candidate in candidates:
            options = _get_chunker_options_dict(candidate)
            if option_key not in options:
                continue

            value = options.get(option_key)
            if isinstance(value, str):
                if value.strip():
                    preserved_options[option_key] = value
                    break
                continue

            if value is not None:
                preserved_options[option_key] = value
                break

    return preserved_options


def reconcile_fluid_topics_structured_profile(
    settings: dict[str, Any], *, ensure_present: bool
) -> bool:
    """Canonicalize the reserved Fluid Topics native profile in graph settings.

    When present, the profile is collapsed to a single canonical configuration that
    always targets all Fluid Topics sources and preserves only the user-editable
    document/chunk title settings plus chunk truncation size.
    """

    content_settings = _get_content_settings(settings)
    structured_candidates = [
        config_dict
        for config_dict in content_settings
        if isinstance(config_dict, dict)
        and is_fluid_topics_structured_profile_candidate(config_dict)
    ]
    other_profiles = [
        config_dict
        for config_dict in content_settings
        if not (
            isinstance(config_dict, dict)
            and is_fluid_topics_structured_profile_candidate(config_dict)
        )
    ]

    next_content_settings: list[dict[str, Any]] = []
    if ensure_present:
        canonical_profile = build_fluid_topics_structured_content_config().model_dump()
        canonical_chunker = canonical_profile.get("chunker")
        canonical_options = (
            canonical_chunker.setdefault("options", {})
            if isinstance(canonical_chunker, dict)
            else None
        )
        if isinstance(canonical_options, dict):
            canonical_options.update(
                _get_preserved_fluid_topics_structured_chunker_options(
                    structured_candidates
                )
            )
        inserted = False
        for config_dict in content_settings:
            is_candidate = isinstance(
                config_dict, dict
            ) and is_fluid_topics_structured_profile_candidate(config_dict)
            if is_candidate:
                if not inserted:
                    next_content_settings.append(canonical_profile)
                    inserted = True
                continue

            next_content_settings.append(config_dict)

        if not inserted:
            next_content_settings.insert(0, canonical_profile)
    else:
        next_content_settings = list(other_profiles)

    if next_content_settings == content_settings:
        return False

    settings["chunking"]["content_settings"] = next_content_settings
    return True


def ensure_fluid_topics_structured_profile(settings: dict[str, Any]) -> bool:
    return reconcile_fluid_topics_structured_profile(settings, ensure_present=True)


def remove_auto_managed_fluid_topics_structured_profiles(
    settings: dict[str, Any],
) -> bool:
    return reconcile_fluid_topics_structured_profile(settings, ensure_present=False)


def get_persisted_content_config_dicts(
    settings: dict[str, Any] | None,
) -> list[dict[str, Any]]:
    default_configs = [cfg.model_dump() for cfg in get_default_content_configs()]
    if not isinstance(settings, dict):
        return default_configs

    chunking = settings.get("chunking")
    if not isinstance(chunking, dict):
        return default_configs

    if "content_settings" not in chunking:
        return default_configs

    content_settings = chunking.get("content_settings")
    if not isinstance(content_settings, list):
        return default_configs

    persisted_configs = [
        deepcopy(config_dict)
        for config_dict in content_settings
        if isinstance(config_dict, dict)
        and not is_virtual_last_resort_profile_candidate(config_dict)
    ]
    return ensure_sharepoint_pages_profile_backfill(persisted_configs)


def build_graph_settings_with_virtual_last_resort_profile(
    settings: dict[str, Any] | None,
) -> dict[str, Any]:
    response_settings = clone_graph_settings(settings)
    chunking = response_settings.get("chunking")
    if not isinstance(chunking, dict):
        chunking = {}
        response_settings["chunking"] = chunking

    chunking["content_settings"] = [
        *get_persisted_content_config_dicts(settings),
        build_virtual_last_resort_content_config_dict(),
    ]
    return response_settings


def sanitize_graph_settings_content_profiles(settings: dict[str, Any]) -> bool:
    content_settings = _get_content_settings(settings)
    sanitized_content_settings = [
        deepcopy(config_dict)
        for config_dict in content_settings
        if isinstance(config_dict, dict)
        and not is_virtual_last_resort_profile_candidate(config_dict)
    ]

    if sanitized_content_settings == content_settings:
        return False

    settings["chunking"]["content_settings"] = sanitized_content_settings
    return True


def get_default_content_configs() -> list[ContentConfig]:
    return [
        ContentConfig(
            name="PDF (LLM Chunking)",
            enabled=True,
            glob_pattern="*.pdf",
            reader={"name": ContentReaderName.LITEPARSE, "options": {}},
            chunker={
                "strategy": ChunkerStrategy.LLM,
                "options": {
                    "llm_batch_size": 18000,
                    "llm_batch_overlap": 0.1,
                    "llm_last_segment_increase": 0.0,
                    "recursive_chunk_overlap": 0.1,
                    "chunk_max_size": 18000,
                    "splitters": ["\n\n", "\n", " ", ""],
                    "prompt_template_system_name": "PDF_DOCUMENT_CHUNKING",
                    "document_title_pattern": "",
                    "chunk_title_pattern": "",
                    "chunk_content_type": ChunkContentType.MARKDOWN,
                },
            },
        ),
        ContentConfig(
            name="PDF (Recursive Splitting)",
            enabled=True,
            glob_pattern="*.pdf",
            reader={"name": ContentReaderName.LITEPARSE, "options": {}},
            chunker={
                "strategy": ChunkerStrategy.RECURSIVE,
                "options": {
                    # LLM and recursive have separate semantics
                    "llm_batch_size": 18000,
                    "llm_batch_overlap": 0.1,
                    "llm_last_segment_increase": 0.0,
                    "recursive_chunk_overlap": 0.1,
                    "chunk_max_size": 18000,
                    "splitters": ["\n\n", "\n", " ", ""],
                    "prompt_template_system_name": "",
                    "document_title_pattern": "",
                    "chunk_title_pattern": "",
                    "chunk_content_type": ChunkContentType.PLAIN_TEXT,
                },
            },
        ),
        build_sharepoint_pages_content_config(),
        ContentConfig(
            name="LiteParse",
            enabled=True,
            glob_pattern="*.pdf,*.docx,*.pptx,*.xlsx,*.odt,*.ods,*.odp,*.png,*.jpg,*.jpeg,*.tiff",
            reader={"name": ContentReaderName.LITEPARSE, "options": {}},
            chunker={
                "strategy": ChunkerStrategy.RECURSIVE,
                "options": {
                    "llm_batch_size": 18000,
                    "llm_batch_overlap": 0.1,
                    "llm_last_segment_increase": 0.0,
                    "recursive_chunk_overlap": 0.1,
                    "chunk_max_size": 18000,
                    "splitters": ["\n\n", "\n", " ", ""],
                    "prompt_template_system_name": "",
                    "document_title_pattern": "",
                    "chunk_title_pattern": "",
                    "chunk_content_type": ChunkContentType.PLAIN_TEXT,
                },
            },
        ),
        ContentConfig(
            name="Kreuzberg",
            enabled=True,
            glob_pattern="*.pdf,*.docx,*.pptx,*.xlsx,*.html,*.png,*.jpg,*.jpeg,*.gif,*.webp,*.bmp,*.tiff,*.eml,*.msg",
            reader={"name": ContentReaderName.KREUZBERG, "options": {"ocr": True}},
            chunker={
                "strategy": ChunkerStrategy.KREUZBERG,
                "options": {
                    "llm_batch_size": 18000,
                    "llm_batch_overlap": 0.1,
                    "llm_last_segment_increase": 0.0,
                    "recursive_chunk_overlap": 0.1,
                    "chunk_max_size": 18000,
                    "splitters": ["\n\n", "\n", " ", ""],
                    "prompt_template_system_name": "",
                    "chunk_title_pattern": "",
                    "chunk_content_type": ChunkContentType.MARKDOWN,
                },
            },
        ),
        ContentConfig(
            name=SHAREPOINT_VIDEO_TRANSCRIPTION_PROFILE_NAME,
            enabled=True,
            glob_pattern="*.mp4,*.avi,*.mov,*.wmv,*.mkv,*.webm",
            source_ids=[SHAREPOINT_SOURCE_SELECTOR],
            reader={
                "name": ContentReaderName.SOURCE_METADATA,
                "options": {"field_name": "VideoDescription"},
            },
            chunker={
                "strategy": ChunkerStrategy.RECURSIVE,
                "options": {
                    "llm_batch_size": 18000,
                    "llm_batch_overlap": 0.1,
                    "llm_last_segment_increase": 0.0,
                    "recursive_chunk_overlap": 0.1,
                    "chunk_max_size": 18000,
                    "splitters": ["\n\n", "\n", " ", ""],
                    "prompt_template_system_name": "",
                    "document_title_pattern": "",
                    "chunk_title_pattern": "",
                    "chunk_content_type": ChunkContentType.PLAIN_TEXT,
                },
            },
        ),
        ContentConfig(
            name="Plain Text",
            enabled=True,
            glob_pattern="",
            reader={"name": ContentReaderName.PLAIN_TEXT, "options": {}},
            chunker={
                "strategy": ChunkerStrategy.RECURSIVE,
                "options": {
                    "llm_batch_size": 15000,
                    "llm_batch_overlap": 0.1,
                    "llm_last_segment_increase": 0.0,
                    "recursive_chunk_overlap": 0.1,
                    "chunk_max_size": 15000,
                    "splitters": ["\n\n", "\n", " ", ""],
                    "prompt_template_system_name": "",
                    "document_title_pattern": "",
                    "chunk_title_pattern": "",
                    "chunk_content_type": ChunkContentType.PLAIN_TEXT,
                },
            },
        ),
    ]


async def get_graph_settings(
    db_session: AsyncSession, graph_id: UUID
) -> dict[str, Any]:
    """Get graph settings."""
    result = await db_session.execute(
        select(KnowledgeGraph).where(KnowledgeGraph.id == graph_id)
    )
    graph = result.scalar_one_or_none()

    if not graph or not graph.settings:
        return {}

    return graph.settings


async def get_graph_embedding_model(
    db_session: AsyncSession, graph_id: UUID
) -> str | None:
    """Get embedding model configured for the graph."""
    settings = await get_graph_settings(db_session, graph_id)
    indexing_cfg = settings.get("indexing") or {}
    model = indexing_cfg.get("embedding_model")
    return model.strip() if isinstance(model, str) and model.strip() else None


async def _get_all_configs(
    db_session: AsyncSession, graph_id: UUID
) -> list[ContentConfig]:
    settings = await get_graph_settings(db_session, graph_id)
    content_settings = get_persisted_content_config_dicts(settings)

    # Parse content settings into ContentConfig objects
    configs = []
    for config_dict in content_settings:
        try:
            configs.append(ContentConfig(**config_dict))
        except Exception as e:
            logger.error(f"Failed to parse content config: {e}")
            continue

    return configs


async def get_content_config(
    db_session: AsyncSession,
    graph_id: UUID,
    filename: str,
    source_id: str | None = None,
    source_type: str | None = None,
) -> ContentConfig | None:
    """Get content config matching filename and optionally source_id/source_type.

    Matching uses AND logic:
    - glob_pattern must match (if specified)
    - source_ids/selectors must match (if specified), otherwise falls back to deprecated source_types (if specified)
    If neither source_ids nor source_types are set, it matches all sources.
    """
    configs = await _get_all_configs(db_session, graph_id)

    normalized_filename = (filename or "").strip().lower()

    for config in configs:
        if not config.enabled:
            continue

        if _is_structured_content_reader(config):
            continue

        # Check glob pattern match (supports comma-separated patterns)
        glob_pattern = (config.glob_pattern or "").strip()
        if glob_pattern:
            patterns = [p.strip() for p in glob_pattern.split(",") if p.strip()]
            if patterns and not any(
                fnmatch.fnmatch(normalized_filename, p.lower()) for p in patterns
            ):
                continue

        # Check source match (AND logic)
        # - Prefer matching by explicit source_ids
        # - Fall back to legacy source_types if source_ids is not set
        # - If neither is set, match all sources
        if not _matches_config_source(
            config, source_id=source_id, source_type=source_type
        ):
            continue

        return config

    return build_virtual_last_resort_content_config()


async def get_structured_content_config(
    db_session: AsyncSession,
    graph_id: UUID,
    *,
    source_id: str | None = None,
    source_type: str | None = None,
) -> ContentConfig | None:
    """Get a structured-content config for pre-chunked Fluid Topics content.

    Structured configs are matched only by source selectors. Filename globbing is
    intentionally ignored because MAP/TOPIC ingestion is not file-based.
    """

    normalized_source_type = str(source_type) if source_type else None
    if normalized_source_type and normalized_source_type != str(
        SourceType.FLUID_TOPICS
    ):
        return None

    configs = await _get_all_configs(db_session, graph_id)

    for config in configs:
        if not config.enabled:
            continue

        if not _is_structured_content_reader(config):
            continue

        if not _matches_config_source(
            config, source_id=source_id, source_type=source_type
        ):
            continue

        return config

    return None

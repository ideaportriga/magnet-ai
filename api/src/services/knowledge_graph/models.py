from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any, Iterable, Iterator, Literal, Optional, TypedDict
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from core.db.models.knowledge_graph import KnowledgeGraphChunk
from utils.datetime_utils import utc_now


class SourceType(StrEnum):
    """Source types for knowledge graph documents."""

    UPLOAD = "upload"
    API_INGEST = "api_ingest"
    API_FETCH = "api_fetch"
    SHAREPOINT = "sharepoint"
    SHAREPOINT_PAGES = "sharepoint_pages"
    CONFLUENCE = "confluence"
    FILE = "file"
    SALESFORCE = "salesforce"
    RIGHTNOW = "rightnow"
    ORACLE_KNOWLEDGE = "oracle_knowledge"
    HUBSPOT = "hubspot"
    FLUID_TOPICS = "fluid_topics"


class ContentReaderName(StrEnum):
    """Content reader types for knowledge graph ingestion."""

    PDF = "pdf"
    PLAIN_TEXT = "plain_text"


class ChunkerStrategy(StrEnum):
    """Chunker strategies for knowledge graph ingestion."""

    NONE = "none"
    LLM = "llm"
    RECURSIVE = "recursive_character_text_splitting"


class DocumentMetadata(BaseModel):
    """Document-level metadata extracted during chunking."""

    title: Optional[str] = Field(None, description="Document title")
    summary: Optional[str] = Field(None, description="Document summary")
    toc: Optional[str] = Field(None, description="Table of contents in markdown format")


class ChunkerResult(BaseModel):
    """Result returned by chunker implementations."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    chunks: list[KnowledgeGraphChunk] = Field(
        ..., description="List of processed chunks"
    )
    document_metadata: Optional[DocumentMetadata] = Field(
        None, description="Document-level metadata (title, summary, TOC)"
    )


class ContentConfig(BaseModel):
    """Configuration for a specific content type."""

    name: str = Field(..., description="Content type name (e.g., PDF or Plain Text)")
    enabled: bool = Field(True, description="Whether this content type is enabled")
    glob_pattern: str = Field(
        ..., description="Glob pattern to match files (e.g., *.pdf)"
    )
    source_types: list[str] = Field(
        default_factory=list,
        description="List of source types to match. If specified, both glob_pattern AND source_types must match (AND logic).",
    )
    reader: dict[str, Any] = Field(
        default_factory=lambda: {"name": ContentReaderName.PLAIN_TEXT, "options": {}},
        description="Reader configuration",
    )
    chunker: dict[str, Any] = Field(
        default_factory=lambda: {
            "strategy": ChunkerStrategy.RECURSIVE,
            "options": {
                # LLM segmenting settings (upstream splitting before LLM-based chunking)
                "llm_batch_size": 18000,
                "llm_batch_overlap": 0.1,
                "llm_last_segment_increase": 0.0,
                # Recursive splitter settings (direct deterministic chunking)
                "recursive_chunk_size": 18000,
                "recursive_chunk_overlap": 0.1,
                # Chunk-level constraints (applies to all strategies)
                "chunk_max_size": 18000,
                "splitters": ["\n\n", "\n", " ", ""],
                # Optional prompt template for LLM-based chunking
                "prompt_template_system_name": "",
                # Optional pattern for chunk title generation
                "chunk_title_pattern": "",
            },
        },
        description="Chunker configuration with strategy and options",
    )


class LoadedContent(TypedDict):
    """Result of loading content from raw bytes."""

    text: str
    metadata: dict[str, Any]


@dataclass(frozen=True)
class SyncPipelineConfig:
    """Generic 3-stage pipeline configuration.

    Stages / queues:
    - **listing**: fetch lists of documents (often paginated)
    - **content_fetch**: fetch document content (topics/files)
    - **document_processing**: run long ingestion (typically `process_document`)
    """

    # Human-readable name for logs
    name: str = "sync_pipeline"

    # Queue backpressure
    listing_queue_max: int = 2
    content_fetch_queue_max: int = 100
    document_processing_queue_max: int = 50

    # Worker counts
    listing_workers: int = 1
    content_fetch_workers: int = 4
    document_processing_workers: int = 1

    # Named semaphores created for workers to use
    semaphores: dict[str, int] = field(default_factory=dict)

    def validate(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("name must be a non-empty string")

        def _pos_int(name: str, v: int) -> None:
            if not isinstance(v, int) or v < 0:
                raise ValueError(f"{name} must be a non-negative int")

        _pos_int("listing_queue_max", self.listing_queue_max)
        _pos_int("content_fetch_queue_max", self.content_fetch_queue_max)
        _pos_int("document_processing_queue_max", self.document_processing_queue_max)
        _pos_int("listing_workers", self.listing_workers)
        _pos_int("content_fetch_workers", self.content_fetch_workers)
        _pos_int("document_processing_workers", self.document_processing_workers)

        if (
            self.listing_workers == 0
            or self.content_fetch_workers == 0
            or self.document_processing_workers == 0
        ):
            raise ValueError("All stage worker counts must be >= 1")

        for k, v in (self.semaphores or {}).items():
            if not isinstance(k, str) or not k.strip():
                raise ValueError("Semaphore names must be non-empty strings")
            if not isinstance(v, int) or v <= 0:
                raise ValueError(f"Semaphore '{k}' concurrency must be a positive int")


@dataclass
class SyncCounters:
    """Common counters for a knowledge-graph sync run."""

    synced: int = 0
    failed: int = 0
    skipped: int = 0
    total_found: int = 0


@dataclass(frozen=True, slots=True)
class MetadataMultiValueContainer:
    """Explicit wrapper for metadata fields that logically contain multiple values.

    Some ingestion sources (e.g., SharePoint multi-choice fields) return values in
    shapes that are easy to mis-handle downstream (lists, dicts with `results`, or
    custom collection objects). Wrapping the extracted values into this container
    makes it easy for downstream services to detect and expand them.
    """

    values: tuple[Any, ...]

    @classmethod
    def from_iterable(cls, values: Iterable[Any]) -> "MetadataMultiValueContainer":
        return cls(tuple(values))

    def __iter__(self) -> Iterator[Any]:
        return iter(self.values)

    def __len__(self) -> int:
        return len(self.values)


class KnowledgeGraphRetrievalSource(BaseModel):
    """Lightweight source item for UI (document title and excerpt)."""

    document_id: Optional[str] = None
    document_name: Optional[str] = None
    document_title: Optional[str] = None
    chunk_title: Optional[str] = None
    chunk_content: Optional[str] = None


class KnowledgeGraphRetrievalWorkflowStep(BaseModel):
    """Workflow step describing a single tool call execution."""

    iteration: int
    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    call_summary: dict[str, Any] = Field(default_factory=dict)


class KnowledgeGraphAgentRunResult(BaseModel):
    """Internal result model returned by Knowledge Graph agent runs."""

    content: str
    sources: list[KnowledgeGraphRetrievalSource] = Field(default_factory=list)
    workflow: list[KnowledgeGraphRetrievalWorkflowStep] = Field(default_factory=list)
    conversation_id: str | None = Field(
        default=None, description="Conversation id associated with this agent run"
    )
    trace_id: str | None = Field(
        default=None,
        description="OpenTelemetry trace id associated with this agent run.",
    )


class KnowledgeGraphConversationMessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class KnowledgeGraphConversationMessageBase(BaseModel):
    """Minimal agent-conversation message schema for Knowledge Graph conversations.

    Notes:
    - `extra="allow"` is important: we must preserve any additional fields written
      by other services (e.g., feedback / copied flags) when we round-trip
      messages through `model_dump()` in start/continue flows.
    """

    model_config = ConfigDict(extra="allow")

    id: UUID
    created_at: datetime = Field(default_factory=utc_now)
    role: KnowledgeGraphConversationMessageRole
    content: str | None = None


class KnowledgeGraphConversationMessageUser(KnowledgeGraphConversationMessageBase):
    role: Literal[KnowledgeGraphConversationMessageRole.USER] = (
        KnowledgeGraphConversationMessageRole.USER
    )


class KnowledgeGraphConversationMessageAssistant(KnowledgeGraphConversationMessageBase):
    role: Literal[KnowledgeGraphConversationMessageRole.ASSISTANT] = (
        KnowledgeGraphConversationMessageRole.ASSISTANT
    )


KnowledgeGraphConversationMessage = (
    KnowledgeGraphConversationMessageUser | KnowledgeGraphConversationMessageAssistant
)


class KnowledgeGraphConversationData(BaseModel):
    """Minimal agent-conversation schema for Knowledge Graph conversations."""

    model_config = ConfigDict(extra="allow")

    id: UUID | None = None
    agent: str
    created_at: datetime
    last_user_message_at: datetime
    client_id: str | None = None
    trace_id: str | None = None
    analytics_id: str | None = None
    variables: dict[str, str] | None = None


class KnowledgeGraphConversationDataWithMessages(KnowledgeGraphConversationData):
    messages: list[KnowledgeGraphConversationMessage]

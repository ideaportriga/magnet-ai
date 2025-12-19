"""
Pydantic schemas for Knowledge Graph domain.
"""

from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, ConfigDict, Field

from scheduler.types import CronConfig


class KnowledgeGraphSourceScheduleExternalSchema(BaseModel):
    """Schedule information for a knowledge graph source."""

    name: Optional[str] = None
    interval: Optional[str] = None
    cron: Optional[CronConfig] = None
    timezone: Optional[str] = None


class KnowledgeGraphExternalSchema(BaseModel):
    """Item model for knowledge graph list endpoint."""

    id: str
    name: str
    system_name: Optional[str]
    description: Optional[str]
    documents_count: int = 0
    chunks_count: int = 0
    created_at: Optional[str]
    updated_at: Optional[str]
    settings: Optional[dict[str, Any]] = None


class KnowledgeGraphCreateRequest(BaseModel):
    """Request model for creating a knowledge graph."""

    name: str = Field(..., description="Display name of the knowledge graph")
    system_name: Optional[str] = Field(
        None, description="Optional system name; derived from name if omitted"
    )
    description: Optional[str] = Field(None, description="Optional description")


class KnowledgeGraphCreateResponse(BaseModel):
    """Response model for create_graph route."""

    id: str


class KnowledgeGraphUpdateRequest(BaseModel):
    """Request model for updating a knowledge graph."""

    name: Optional[str] = Field(None, description="New display name")
    description: Optional[str] = Field(None, description="New description")
    settings: Optional[dict[str, Any]] = Field(
        None, description="Graph settings object to fully replace"
    )
    content_configs: Optional[list[dict[str, Any]]] = Field(
        None, description="Override for chunking.content_settings in settings"
    )


class KnowledgeGraphUpdateResponse(BaseModel):
    """Response model for update_graph route."""

    id: str
    name: str
    system_name: Optional[str]
    description: Optional[str]


class KnowledgeGraphUploadUrlRequest(BaseModel):
    """Request model for uploading a document to a knowledge graph from a URL.

    The URL is treated as transient input for ingestion and is not persisted on the source.
    """

    url: str = Field(..., description="Direct http(s) URL to a file")


class KnowledgeGraphSourceExternalSchema(BaseModel):
    """Item model for knowledge graph source list endpoint."""

    id: str
    name: str
    type: str
    config: Optional[dict[str, Any]] = None
    status: Optional[str] = None
    documents_count: int = 0
    last_sync_at: Optional[str] = None
    created_at: Optional[str] = None
    schedule: Optional[KnowledgeGraphSourceScheduleExternalSchema] = None


class KnowledgeGraphSourceCreateRequest(BaseModel):
    """Request model for creating a knowledge graph source (generic)."""

    type: str = Field(..., description="Source type, e.g., 'sharepoint', 'file'")
    name: Optional[str] = Field(None, description="Optional display name")
    config: Optional[dict[str, Any]] = Field(
        None, description="Source-specific configuration payload"
    )


class KnowledgeGraphSourceUpdateRequest(BaseModel):
    """Request model for updating a knowledge graph source."""

    name: Optional[str] = Field(None, description="Optional new display name")
    config: Optional[dict[str, Any]] = Field(
        None, description="Partial config to merge into existing config"
    )
    status: Optional[str] = Field(None, description="Optional status override")


class KnowledgeGraphSourceScheduleSyncRequest(BaseModel):
    """Request model for scheduling recurring sync for a knowledge graph source.

    Note: run_configuration and job_type are enforced server-side.
    """

    model_config = ConfigDict(extra="ignore")

    name: Optional[str] = Field(None, description="Optional schedule display name")
    interval: Optional[str] = Field(
        None, description="Schedule interval label (e.g., hourly, daily, weekly)"
    )
    cron: Optional[CronConfig] = Field(
        None, description="Cron configuration for recurring sync"
    )
    timezone: Optional[str] = Field(
        None, description="Timezone for cron evaluation (defaults to UTC)"
    )


class SharePointSourceCreateRequest(BaseModel):
    """Request model for creating a SharePoint source."""

    graph_id: str = Field(..., description="Target knowledge graph id")
    name: Optional[str] = Field(None, description="Optional display name")
    site_url: str = Field(..., description="SharePoint site URL")
    folder_path: Optional[str] = Field(None, description="Optional folder path")
    client_id: Optional[str] = Field(None, description="OAuth client id")
    tenant_id: Optional[str] = Field(None, description="Azure tenant id")
    provider_system_name: Optional[str] = Field(
        None, description="Auth provider system name"
    )
    file_extensions: Optional[list[str]] = Field(
        None, description="Allowed file extensions"
    )
    client_secret: Optional[str] = Field(
        None, description="Client secret (not persisted); used to mark credentials"
    )


class KnowledgeGraphSourceCreateResponse(BaseModel):
    """Response model for creating a knowledge graph source."""

    id: str
    name: str
    type: str


class KnowledgeGraphDocumentExternalSchema(BaseModel):
    """Item model for knowledge graph document list endpoint."""

    id: str
    name: str
    type: Optional[str] = None
    content_profile: Optional[str] = None
    status: Optional[str] = None
    status_message: Optional[str] = None
    title: Optional[str] = None
    total_pages: Optional[int] = None
    processing_time: Optional[float] = None
    chunks_count: int = 0
    source_name: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class KnowledgeGraphDocumentDetailSchema(BaseModel):
    """Detail model for a single knowledge graph document."""

    id: str
    name: str
    type: Optional[str] = None
    content_profile: Optional[str] = None
    title: Optional[str] = None
    summary: Optional[str] = None
    toc: Optional[list[dict[str, Any]]] = None
    status: Optional[str] = None
    status_message: Optional[str] = None
    total_pages: Optional[int] = None
    processing_time: Optional[float] = None
    source_id: Optional[str] = None
    chunks_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class KnowledgeGraphChunkExternalSchema(BaseModel):
    """Item model for chunks in list endpoints."""

    id: str
    document_id: str
    document_name: str
    name: Optional[str] = None
    title: Optional[str] = None
    toc_reference: Optional[str] = None
    page: Optional[int] = None
    chunk_type: Optional[str] = None
    text: Optional[str] = None
    created_at: Optional[str] = None


class KnowledgeGraphChunkListResponse(BaseModel):
    """Response model for graph chunks listing (paginated)."""

    chunks: list[KnowledgeGraphChunkExternalSchema]
    total: int
    limit: int
    offset: int


class KnowledgeGraphRetrievalPreviewRequest(BaseModel):
    """Request model for running agentic retrieval preview."""

    query: str = Field(..., description="User question or query for retrieval")
    conversation_id: Optional[str] = Field(
        default=None, description="Existing conversation id to continue"
    )


class KnowledgeGraphRetrievalSource(BaseModel):
    """Lightweight source item for UI (document title and excerpt)."""

    title: Optional[str] = None
    content: Optional[str] = None


class KnowledgeGraphRetrievalWorkflowStep(BaseModel):
    """Workflow step describing a single tool call execution."""

    iteration: int
    tool: str
    arguments: dict[str, Any] = Field(default_factory=dict)
    call_summary: dict[str, Any] = Field(default_factory=dict)


class KnowledgeGraphRetrievalPreviewResponse(BaseModel):
    """Response model for retrieval preview run."""

    content: str
    sources: list[KnowledgeGraphRetrievalSource] = Field(default_factory=list)
    workflow: list[KnowledgeGraphRetrievalWorkflowStep] = Field(default_factory=list)
    conversation_id: Optional[str] = Field(
        default=None, description="Conversation id associated with this preview run"
    )

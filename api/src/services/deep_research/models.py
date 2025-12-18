"""Deep Research service models and types."""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


class RelevantResult(BaseModel):
    """A single relevant search result with reasoning."""
    url: str = Field(description="The URL of the relevant result")
    reasoning: str = Field(description="Explanation of why this result is relevant")


class SearchResultsAnalysis(BaseModel):
    """Analysis of search results for relevance."""
    relevant_results: list[RelevantResult] = Field(
        default_factory=list,
        description="List of relevant results with URL and reasoning"
    )


class DeepResearchStatus(str, Enum):
    """Status of a deep research run."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


class WebhookConfig(BaseModel):
    """Webhook configuration for deep research completion callbacks."""
    enabled: bool = Field(
        default=True,
        description="Enable webhook calls on completion"
    )
    api_server: str = Field(
        max_length=255,
        description="API server system name for webhook"
    )
    api_tool: str = Field(
        max_length=255,
        description="Tool system name for webhook"
    )
    payload_template: dict[str, Any] | None = Field(
        default=None,
        description=(
            "Optional payload template with path references relative to run object. "
            "Examples: 'run_id', 'client_id', 'input.query', 'result.summary', 'result.data'"
        )
    )


class DeepResearchConfig(BaseModel):
    """Configuration for deep research execution."""
    reasoning_prompt: str = Field(
        default="DEFAULT_DEEP_RESEARCH_REASONING",
        max_length=255,
        description="Prompt template for agent reasoning/planning and tool calling"
    )
    analyze_search_results_prompt: str = Field(
        default="DEFAULT_DEEP_RESEARCH_ANALYZE_SEARCH_RESULTS",
        max_length=255,
        description="Prompt template for analyzing/filtering search results for relevance"
    )
    process_search_result_prompt: str = Field(
        default="DEFAULT_DEEP_RESEARCH_PROCESS_SEARCH_RESULT",
        max_length=255,
        description="Prompt template for processing individual page content from search results"
    )
    max_iterations: int = Field(
        default=10,
        ge=1,
        le=30,
        description="Maximum number of research iterations"
    )
    max_results: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum number of search results to return per query"
    )
    parallel_tool_calls: bool = Field(
        default=False,
        description="Enable parallel tool calls for reasoning step (OpenAI only)"
    )

    # Webhook configuration (optional)
    webhook: WebhookConfig | None = Field(
        default=None,
        description="Optional webhook configuration for completion callbacks"
    )


class DeepResearchConfigEntity(DeepResearchConfig):
    """Deep research config with metadata (name and system_name)."""
    name: str = Field(max_length=255, description="Human-readable name")
    system_name: str = Field(max_length=255, description="System identifier (unique)")


class StepType(str, Enum):
    """Types of research steps."""
    REASONING = "reasoning"
    SEARCH = "search"
    ANALYZE_RESULTS = "analyze_results"
    PROCESS_PAGE = "process_page"


class ReasoningStepDetails(BaseModel):
    """Details for a reasoning step."""
    decided_action: str = Field(description="What action was decided (e.g., 'search', 'final_report')")


class SearchStepDetails(BaseModel):
    """Details for a search step."""
    query: str = Field(description="The search query executed")
    results_count: int = Field(description="Total number of results returned")
    new_results_count: int = Field(description="Number of new results (not previously analyzed)")


class AnalyzeResultsStepDetails(BaseModel):
    """Details for an analyze results step."""
    analyzed_count: int = Field(description="Number of results analyzed")
    relevant_count: int = Field(description="Number of results deemed relevant")
    relevant_urls: list[str] = Field(
        default_factory=list,
        description="URLs of relevant results"
    )


class ProcessPageStepDetails(BaseModel):
    """Details for a process page step."""
    url: str = Field(description="URL of the page processed")
    page_title: str = Field(description="Title of the page")
    summary: str = Field(description="Summary of extracted information")


class DeepResearchStep(BaseModel):
    """A single human-readable step in the research process."""
    type: StepType = Field(description="Type of research step")
    title: str = Field(description="Human-readable title of what's happening")

    # Step-specific data (strict typing based on step type)
    details: (
        ReasoningStepDetails |
        SearchStepDetails |
        AnalyzeResultsStepDetails |
        ProcessPageStepDetails
    ) = Field(description="Step-specific details with strict typing based on step type")

    error: str | None = Field(default=None, description="Error message if step failed")
    
    # Performance metrics
    cost: float | None = Field(default=None, description="Cost of this step in USD")
    latency: float | None = Field(default=None, description="Latency of this step in milliseconds")
    usage: dict[str, Any] | None = Field(default=None, description="Token usage for this step")
    
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class DeepResearchIteration(BaseModel):
    """One iteration of the research loop containing multiple steps."""
    steps: list[DeepResearchStep] = Field(
        default_factory=list,
        description="Steps executed in this iteration"
    )
    summary: str | None = Field(
        default=None,
        description="Optional summary of what was accomplished in this iteration"
    )


class DeepResearchMemory(BaseModel):
    """Memory structure for deep research run."""
    search_queries: list[str] = Field(default_factory=list)

    # URL tracking with full context including raw content
    url_analysis: dict[str, dict[str, Any]] = Field(
        default_factory=dict,
        description=(
            "Full analysis results for each URL. "
            "Keys are URLs, values contain: title, snippet, raw_content, search_query, "
            "is_relevant (bool), relevance_reasoning (str), "
            "processed (bool), processing_summary (str)"
        )
    )

    # Quick lookup sets (derived from url_analysis)
    analyzed_urls: set[str] = Field(
        default_factory=set,
        description="URLs that have been analyzed for relevance (includes both relevant and irrelevant)"
    )
    processed_urls: set[str] = Field(
        default_factory=set,
        description="URLs that were relevant and have been processed for content extraction"
    )

    # Generic extracted information storage (replaces task-specific "findings")
    extracted_info: list[str] = Field(
        default_factory=list,
        description="Generic list of extracted information/insights from processed pages"
    )

    # Internal conversation history for LLM (not for display)
    conversation_history: list[dict[str, Any]] = Field(default_factory=list)


class WebhookCallDetails(BaseModel):
    """Details of a webhook call attempt."""
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    api_server: str = Field(description="API server system name")
    api_tool: str = Field(description="Tool system name")
    request_payload: dict[str, Any] | None = Field(default=None, description="Request payload sent")
    response_status: int | None = Field(default=None, description="HTTP response status code")
    response_body: dict[str, Any] | None = Field(default=None, description="Response body received")
    success: bool = Field(description="Whether the webhook call succeeded")
    error_message: str | None = Field(default=None, description="Error message if failed")


class DeepResearchRun(BaseModel):
    """Deep research run data."""
    run_id: str = Field(max_length=255)
    config_id: str | None = Field(
        default=None,
        max_length=255,
        description="Optional config ID if run was created from a saved config"
    )
    config_system_name: str | None = Field(
        default=None,
        max_length=255,
        description="System name of the config used for this run",
    )
    client_id: str | None = Field(
        default=None,
        max_length=255,
        description="Optional client-side identifier for the run"
    )
    status: DeepResearchStatus
    config: DeepResearchConfig
    input: dict[str, Any]  # Input variables for prompt templates
    memory: DeepResearchMemory = Field(default_factory=DeepResearchMemory)

    # Research flow organized by iterations
    iterations: list[DeepResearchIteration] = Field(
        default_factory=list,
        description="Research process organized by iterations, each containing multiple steps"
    )

    result: dict[str, Any] | None = None  # Result as dict from completion tool
    error: str | None = None
    
    # Webhook call details
    webhook_call: WebhookCallDetails | None = Field(
        default=None,
        description="Details of webhook call attempt (if webhook was configured and called)"
    )
    
    # Cost and performance tracking
    total_cost: float | None = Field(
        default=None,
        description="Total cost of all LLM calls in USD"
    )
    total_latency: float | None = Field(
        default=None,
        description="Total latency of all LLM calls in milliseconds"
    )
    total_usage: dict[str, Any] | None = Field(
        default=None,
        description="Aggregated token usage across all LLM calls"
    )
    
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)


class CreateDeepResearchRunRequest(BaseModel):
    """Request to create a new deep research run."""
    input: dict[str, Any] = Field(
        ...,
        description="Input variables for the research (e.g., {'query': 'research question', 'context': '...'})"
    )
    config: DeepResearchConfig | None = Field(
        default=None,
        description="Optional configuration override"
    )
    client_id: str | None = Field(
        default=None,
        max_length=255,
        description="Optional client-side identifier for the run"
    )


class DeepResearchRunResponse(BaseModel):
    """Response with run information."""
    run_id: str
    status: DeepResearchStatus
    created_at: datetime

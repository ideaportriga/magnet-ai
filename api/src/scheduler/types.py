from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, model_validator


class JobStatus(str, Enum):
    CONFIGURATION = "Configuration"
    WAITING = "Waiting"
    STARTED = "Started"
    PROCESSING = "Processing"
    COMPLETED = "Completed"
    ERROR = "Error"
    CANCELED = "Canceled"


class RunConfigurationType(str, Enum):
    CUSTOM = "custom"
    SYNC_COLLECTION = "sync_collection"
    POST_PROCESS_CONVERSATION = "post_processing_conversations"
    EVALUATION = "evaluation"
    SYNC_KNOWLEDGE_GRAPH_SOURCE = "sync_knowledge_graph_source"
    CLEANUP_LOGS = "cleanup_logs"


class JobType(str, Enum):  # Changed from Enum to str, Enum
    ONE_TIME_IMMEDIATE = "one_time_immediate"
    ONE_TIME_SCHEDULED = "one_time_scheduled"
    RECURRING = "recurring"


class RunConfiguration(BaseModel):
    type: RunConfigurationType = Field(
        ...,
        description="type of the function to execute",
    )
    params: dict[str, Any] = Field(..., description="Input parameters for the function")


class CronConfig(BaseModel):
    """Cron schedule configuration.

    Supports two modes:

    1. **Individual fields** – ``minute``, ``hour``, ``day``, ``month``,
       ``day_of_week``  (each defaults to ``*``).
    2. **Raw cron expression** – ``cron_expression`` as a single 5-field
       string (e.g. ``"0 */2 * * 1-5"``).

    If ``cron_expression`` is provided it takes precedence over the
    individual fields.
    """

    cron_expression: str | None = Field(
        None,
        description="Full 5-field cron expression (e.g. '0 */2 * * 1-5'). "
        "Takes precedence over individual fields when set.",
    )
    month: int | str | None = Field(None, description="month (1-12)")
    day: int | str | None = Field(None, description="day of month (1-31)")
    day_of_week: int | str | None = Field(
        None,
        description="number or name of weekday (0-6 or mon,tue,wed,thu,fri,sat,sun)",
    )
    hour: int | str | None = Field(None, description="hour (0-23)")
    minute: int | str | None = Field(None, description="minute (0-59)")

    @model_validator(mode="after")
    def validate_cron_config(self) -> "CronConfig":
        """Validate that at least one scheduling field is provided."""
        has_individual = any(
            v is not None
            for v in (self.minute, self.hour, self.day, self.month, self.day_of_week)
        )
        if not self.cron_expression and not has_individual:
            raise ValueError(
                "Either 'cron_expression' or at least one of "
                "'minute', 'hour', 'day', 'month', 'day_of_week' must be provided."
            )
        return self


class JobDefinition(BaseModel):
    job_id: str | None = Field(None, description="Unique identifier for the job")
    name: str = Field(..., description="Name of the job")
    interval: str | None = Field(
        None,
        description="Interval name for recurring jobs",
    )
    job_type: JobType = Field(
        ...,
        description="Type of the job (immediate, scheduled, or recurring)",
    )
    notification_email: str | None = Field(
        None,
        description="Email to send notifications to",
    )
    cron: CronConfig | None = Field(
        None,
        description="Cron configuration for recurring jobs",
    )
    scheduled_start_time: datetime | None = Field(
        None,
        description="Start time for scheduled or recurring jobs",
    )
    status: JobStatus | None = Field(
        JobStatus.CONFIGURATION,
        description="Current status of the job",
    )
    run_configuration: RunConfiguration = Field(
        ...,
        description="Configuration of the function to execute",
    )
    timezone: str | None = Field(
        "UTC",
        description="Timezone for scheduled start time",
    )

    @model_validator(mode="after")
    def validate_job_configuration(self) -> "JobDefinition":
        # Ensure timezone has a default value if None is provided
        if self.timezone is None:
            self.timezone = "UTC"

        if self.job_type == JobType.ONE_TIME_IMMEDIATE:
            if self.scheduled_start_time or self.cron:
                raise ValueError(
                    "For one_time_immediate jobs, scheduled_start_time and cron must be None",
                )

        elif self.job_type == JobType.ONE_TIME_SCHEDULED:
            if not self.scheduled_start_time:
                raise ValueError(
                    "scheduled_start_time must be provided for one_time_scheduled jobs",
                )
            if self.cron:
                raise ValueError(
                    "cron must not be provided for one_time_scheduled jobs",
                )

        elif self.job_type == JobType.RECURRING:
            if not self.cron:
                raise ValueError(
                    "cron configuration must be provided for recurring jobs",
                )
            if not self.scheduled_start_time:
                from datetime import timezone as tz

                self.scheduled_start_time = datetime.now(
                    tz.utc
                )  # Default to current time in UTC if not provided

        return self


class JobLog(BaseModel):
    start_time: datetime | None = Field(
        None,
        description="Actual start time of the job",
    )
    end_time: datetime | None = Field(None, description="Actual end time of the job")
    execution_time: float | None = Field(
        None,
        description="Execution duration in seconds",
    )
    status: JobStatus | None = Field(None, description="Current status of the job")
    comment: str | None = Field(
        None,
        description="Additional comments about the job",
    )
    error: bool | None = Field(
        None,
        description="Indicates whether an error occurred",
    )
    error_msg: str | None = Field(
        None,
        description="Detailed error message if applicable",
    )


class JobIdInput(BaseModel):
    job_id: str

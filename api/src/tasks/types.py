"""Pydantic types for jobs. Moved from legacy src/scheduler/types.py."""

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


class JobType(str, Enum):
    ONE_TIME_IMMEDIATE = "one_time_immediate"
    ONE_TIME_SCHEDULED = "one_time_scheduled"
    RECURRING = "recurring"


class RunConfiguration(BaseModel):
    type: RunConfigurationType = Field(
        ..., description="type of the function to execute"
    )
    params: dict[str, Any] = Field(..., description="Input parameters for the function")


class CronConfig(BaseModel):
    year: int | str | None = None
    month: int | str | None = None
    day: int | str | None = None
    week: int | str | None = None
    day_of_week: int | str | None = None
    hour: int | str | None = None
    minute: int | str | None = None
    second: int | str | None = None
    start_date: datetime | str | None = None
    end_date: datetime | str | None = None
    jitter: int | None = Field(
        None,
        description=(
            "Legacy APScheduler field: delays execution by up to N seconds. "
            "Not natively supported by AsyncpgScheduleSource; if used, emulated "
            "by @with_job_status (see docs/TASKIQ_MIGRATION_PLAN.md §8.4)."
        ),
    )


class JobDefinition(BaseModel):
    job_id: str | None = None
    name: str = Field(..., description="Name of the job")
    interval: str | None = None
    job_type: JobType = Field(..., description="Type of the job")
    notification_email: str | None = None
    cron: CronConfig | None = None
    scheduled_start_time: datetime | None = None
    status: JobStatus | None = JobStatus.CONFIGURATION
    run_configuration: RunConfiguration = Field(..., description="What to execute")
    timezone: str | None = "UTC"

    @model_validator(mode="after")
    def validate_job_configuration(self) -> "JobDefinition":
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
                    "cron must not be provided for one_time_scheduled jobs"
                )
        elif self.job_type == JobType.RECURRING:
            if not self.cron:
                raise ValueError(
                    "cron configuration must be provided for recurring jobs"
                )
            if not self.scheduled_start_time:
                from datetime import timezone as tz

                self.scheduled_start_time = datetime.now(tz.utc)

        return self


class JobIdInput(BaseModel):
    job_id: str

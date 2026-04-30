"""Pydantic schemas for the `note_taker_settings.config` JSONB column.

Single source of truth for the shape of a Note Taker settings record. The
ORM model in `core/db/models/teams/note_taker_settings.py` stores `config`
as opaque JSONB; this file declares what's actually inside.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

# Bump whenever the shape of `NoteTakerSettingsSchema` (or any nested schema)
# changes. New rows are stamped with this number; back-fill migrations should
# target rows with `settings_revision < CURRENT_SETTINGS_REVISION`.
CURRENT_SETTINGS_REVISION = 1


class PromptSettingSchema(BaseModel):
    enabled: bool = False
    prompt_template: str = ""


class IntegrationConfluenceSchema(BaseModel):
    """Confluence integration sub-config.

    `extra="allow"` so legacy fields stored in `note_taker_settings.config`
    survive a round-trip even if they aren't declared here.
    """

    model_config = ConfigDict(extra="allow")

    enabled: bool = False
    confluence_api_server: str = ""
    confluence_create_page_tool: str = ""
    space_key: str = ""
    parent_id: str = ""
    title_template: str = "Meeting notes: {meeting_title} ({date})"

    @model_validator(mode="after")
    def _enabled_requires_credentials(self) -> "IntegrationConfluenceSchema":
        if not self.enabled:
            return self
        if not self.space_key:
            raise ValueError(
                "Confluence space_id is required when confluence is enabled "
                "(enter numeric spaceId from Confluence REST v2)."
            )
        if not self.confluence_api_server or not self.confluence_create_page_tool:
            raise ValueError(
                "Confluence API server and create-page tool are required when "
                "confluence is enabled."
            )
        return self


class IntegrationSalesforceSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    send_transcript_to_salesforce: bool = False
    salesforce_api_server: str = ""
    salesforce_stt_recording_tool: str = ""

    @model_validator(mode="after")
    def _send_requires_credentials(self) -> "IntegrationSalesforceSchema":
        if not self.send_transcript_to_salesforce:
            return self
        if not self.salesforce_api_server or not self.salesforce_stt_recording_tool:
            raise ValueError(
                "Salesforce API server and STT recording tool are required when "
                "send_transcript_to_salesforce is enabled."
            )
        return self


class IntegrationsSchema(BaseModel):
    model_config = ConfigDict(extra="allow")

    confluence: IntegrationConfluenceSchema = Field(
        default_factory=IntegrationConfluenceSchema
    )
    salesforce: IntegrationSalesforceSchema = Field(
        default_factory=IntegrationSalesforceSchema
    )


class NoteTakerSettingsSchema(BaseModel):
    model_config = ConfigDict(extra="ignore")

    subscription_recordings_ready: bool = False
    # pipeline_id stores the stt_model_system_name (e.g. "ELEVENLABS2_SCRIBE_V1").
    # Empty string means the transcription service will use its own default provider.
    pipeline_id: str = ""
    send_number_of_speakers: bool = False
    accept_commands_from_non_organizer: bool = False
    create_knowledge_graph_embedding: bool = False
    knowledge_graph_system_name: str = ""
    keyterms: str = ""
    integration: IntegrationsSchema = Field(default_factory=IntegrationsSchema)
    chapters: PromptSettingSchema = Field(default_factory=PromptSettingSchema)
    summary: PromptSettingSchema = Field(default_factory=PromptSettingSchema)
    insights: PromptSettingSchema = Field(default_factory=PromptSettingSchema)
    post_transcription: PromptSettingSchema = Field(default_factory=PromptSettingSchema)

    @model_validator(mode="after")
    def _post_transcription_template_required(self) -> "NoteTakerSettingsSchema":
        if not self.post_transcription.enabled:
            return self
        if not str(self.post_transcription.prompt_template or "").strip():
            raise ValueError(
                "Prompt template is required when post-transcription processing "
                "is enabled."
            )
        return self


class NoteTakerSettingsRecordCreateSchema(BaseModel):
    name: str
    system_name: str
    description: str = ""
    config: NoteTakerSettingsSchema = Field(default_factory=NoteTakerSettingsSchema)
    provider_system_name: Optional[str] = None
    superuser_id: Optional[str] = None


class NoteTakerSettingsRecordUpdateSchema(BaseModel):
    name: Optional[str] = None
    system_name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[NoteTakerSettingsSchema] = None
    provider_system_name: Optional[str] = None
    superuser_id: Optional[str] = None

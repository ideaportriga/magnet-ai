from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from litestar import Controller, get, post, put
from litestar.params import Body
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from core.db.models.teams.note_taker_settings import NoteTakerSettings
from core.db.session import async_session_maker


NOTE_TAKER_SETTINGS_SYSTEM_NAME = "NOTE_TAKER_SETTINGS"


class PromptSettingSchema(BaseModel):
    enabled: bool = False
    prompt_template: str = ""


class NoteTakerSettingsSchema(BaseModel):
    model_config = ConfigDict(extra="allow")  # TODO: remove it

    subscription_recordings_ready: bool = False
    pipeline_id: str = "elevenlabs"
    send_number_of_speakers: bool = False
    create_knowledge_graph_embedding: bool = False
    knowledge_graph_system_name: str = ""
    keyterms: str = ""
    integration: dict[str, Any] = Field(
        default_factory=lambda: {
            "confluence": {
                "enabled": False,
                "confluence_api_server": "",
                "confluence_create_page_tool": "",
                "space_key": "",
                "parent_id": "",
                "title_template": "Meeting notes: {meeting_title} ({date})",
            },
            "salesforce": {
                "send_transcript_to_salesforce": False,
                "salesforce_api_server": "",
                "salesforce_stt_recording_tool": "",
            },
        }
    )
    chapters: PromptSettingSchema = Field(default_factory=PromptSettingSchema)
    summary: PromptSettingSchema = Field(default_factory=PromptSettingSchema)
    insights: PromptSettingSchema = Field(default_factory=PromptSettingSchema)
    post_transcription: PromptSettingSchema = Field(default_factory=PromptSettingSchema)


class NoteTakerSettingsRecordCreateSchema(BaseModel):
    name: str
    system_name: str
    description: str = ""
    config: NoteTakerSettingsSchema = Field(default_factory=NoteTakerSettingsSchema)


class NoteTakerSettingsRecordUpdateSchema(BaseModel):
    name: Optional[str] = None
    system_name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[NoteTakerSettingsSchema] = None


def _default_settings_payload() -> dict[str, Any]:
    return NoteTakerSettingsSchema().model_dump()


def _settings_to_payload(settings: NoteTakerSettings) -> dict[str, Any]:
    return {
        "id": str(settings.id),
        "name": settings.name,
        "system_name": settings.system_name,
        "description": settings.description,
        "config": settings.config or _default_settings_payload(),
        "created_at": settings.created_at,
        "updated_at": settings.updated_at,
    }


def _validate_salesforce_settings(data: NoteTakerSettingsSchema) -> None:
    salesforce_settings = (data.integration or {}).get("salesforce") or {}
    if salesforce_settings.get("send_transcript_to_salesforce") and (
        not salesforce_settings.get("salesforce_api_server")
        or not salesforce_settings.get("salesforce_stt_recording_tool")
    ):
        raise ValueError(
            "Salesforce API server and STT recording tool are required when "
            "send_transcript_to_salesforce is enabled."
        )


def _validate_confluence_settings(data: NoteTakerSettingsSchema) -> None:
    confluence_settings = (data.integration or {}).get("confluence") or {}
    if not confluence_settings.get("enabled"):
        return

    if not confluence_settings.get("space_key"):
        raise ValueError(
            "Confluence space_id is required when confluence is enabled (enter numeric spaceId from Confluence REST v2)."
        )

    server = (
        confluence_settings.get("confluence_api_server")
        # or confluence_settings.get("api_server_system_name")
    )
    tool = (
        confluence_settings.get("confluence_create_page_tool")
        # or confluence_settings.get("api_tool_system_name")
        # or confluence_settings.get("tool_system_name")
    )
    if not server or not tool:
        raise ValueError(
            "Confluence API server and create-page tool are required when confluence is enabled."
        )


def _validate_post_transcription_settings(data: NoteTakerSettingsSchema) -> None:
    section = data.post_transcription
    if not section.enabled:
        return
    if not str(section.prompt_template or "").strip():
        raise ValueError(
            "Prompt template is required when post-transcription processing is enabled."
        )


async def _get_settings_by_id_or_system_name(
    session, settings_id: str
) -> NoteTakerSettings | None:
    try:
        parsed_id = UUID(settings_id)
    except (TypeError, ValueError):
        parsed_id = None

    if parsed_id is not None:
        stmt = select(NoteTakerSettings).where(NoteTakerSettings.id == parsed_id)
    else:
        stmt = select(NoteTakerSettings).where(
            NoteTakerSettings.system_name == settings_id
        )
    result = await session.execute(stmt)
    return result.scalars().first()


class NoteTakerSettingsController(Controller):
    path = "/note-taker/settings"
    tags = ["Admin / Note Taker"]

    @get()
    async def list_settings(self) -> list[dict[str, Any]]:
        async with async_session_maker() as session:
            stmt = select(NoteTakerSettings).order_by(
                NoteTakerSettings.created_at.asc()
            )
            result = await session.execute(stmt)
            settings = result.scalars().all()
            return [_settings_to_payload(item) for item in settings]

    @get("/{settings_id:str}")
    async def get_settings(self, settings_id: str) -> dict[str, Any]:
        async with async_session_maker() as session:
            settings = await _get_settings_by_id_or_system_name(session, settings_id)
            if settings is None:
                return {}
            return _settings_to_payload(settings)

    @post()
    async def create_settings(
        self,
        data: NoteTakerSettingsRecordCreateSchema = Body(),
    ) -> dict[str, Any]:
        _validate_salesforce_settings(data.config)
        _validate_confluence_settings(data.config)
        _validate_post_transcription_settings(data.config)
        async with async_session_maker() as session:
            settings = NoteTakerSettings(
                name=data.name,
                system_name=data.system_name,
                description=data.description,
                config=data.config.model_dump(),
            )
            session.add(settings)
            await session.commit()
            await session.refresh(settings)
            return _settings_to_payload(settings)

    @put()
    async def update_settings(
        self,
        data: NoteTakerSettingsSchema = Body(),
    ) -> dict[str, Any]:
        _validate_salesforce_settings(data)
        _validate_confluence_settings(data)
        _validate_post_transcription_settings(data)
        async with async_session_maker() as session:
            stmt = select(NoteTakerSettings).where(
                NoteTakerSettings.system_name == NOTE_TAKER_SETTINGS_SYSTEM_NAME
            )
            result = await session.execute(stmt)
            settings = result.scalars().first()

            if settings is None:
                settings = NoteTakerSettings(
                    name="Note Taker Settings",
                    system_name=NOTE_TAKER_SETTINGS_SYSTEM_NAME,
                    description="Settings for the Teams note taker bot.",
                    config=_default_settings_payload(),
                )
                session.add(settings)

            settings.config = data.model_dump()
            await session.commit()
            await session.refresh(settings)
            return _settings_to_payload(settings)

    @put("/{settings_id:str}")
    async def update_settings_by_id(
        self,
        settings_id: str,
        data: NoteTakerSettingsRecordUpdateSchema = Body(),
    ) -> dict[str, Any]:
        async with async_session_maker() as session:
            settings = await _get_settings_by_id_or_system_name(session, settings_id)
            if settings is None:
                raise ValueError("Note taker settings not found.")

            if data.config is not None:
                _validate_salesforce_settings(data.config)
                _validate_confluence_settings(data.config)
                _validate_post_transcription_settings(data.config)
                settings.config = data.config.model_dump()
            if data.name is not None:
                settings.name = data.name
            if data.system_name is not None:
                settings.system_name = data.system_name
            if data.description is not None:
                settings.description = data.description

            await session.commit()
            await session.refresh(settings)
            return _settings_to_payload(settings)

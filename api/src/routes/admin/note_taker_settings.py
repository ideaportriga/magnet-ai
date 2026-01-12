from __future__ import annotations

from typing import Any

from litestar import Controller, get, put
from litestar.params import Body
from pydantic import BaseModel, Field
from sqlalchemy import select

from core.db.models.settings import Settings
from core.db.session import async_session_maker


NOTE_TAKER_SETTINGS_SYSTEM_NAME = "NOTE_TAKER_SETTINGS"


class PromptSettingSchema(BaseModel):
    enabled: bool = False
    prompt_template: str = ""


class NoteTakerSettingsSchema(BaseModel):
    subscription_recordings_ready: bool = False
    create_knowledge_graph_embedding: bool = False
    knowledge_graph_system_name: str = ""
    integration: dict[str, Any] = Field(
        default_factory=lambda: {
            "salesforce": {
                "send_transcript_to_salesforce": False,
                "salesforce_api_server": "",
                "salesforce_stt_recording_tool": "",
            }
        }
    )
    chapters: PromptSettingSchema = Field(default_factory=PromptSettingSchema)
    summary: PromptSettingSchema = Field(default_factory=PromptSettingSchema)
    insights: PromptSettingSchema = Field(default_factory=PromptSettingSchema)


def _default_settings_payload() -> dict[str, Any]:
    return NoteTakerSettingsSchema().model_dump()


async def _get_or_create_settings() -> Settings:
    async with async_session_maker() as session:
        stmt = select(Settings).where(
            Settings.system_name == NOTE_TAKER_SETTINGS_SYSTEM_NAME
        )
        result = await session.execute(stmt)
        settings = result.scalars().first()

        if settings:
            return settings

        settings = Settings(
            name="Note Taker Settings",
            system_name=NOTE_TAKER_SETTINGS_SYSTEM_NAME,
            description="Settings for the Teams note taker bot.",
            config=_default_settings_payload(),
        )
        session.add(settings)
        await session.commit()
        await session.refresh(settings)
        return settings


class NoteTakerSettingsController(Controller):
    path = "/note-taker/settings"
    tags = ["Admin / Note Taker"]

    @get()
    async def get_settings(self) -> dict[str, Any]:
        settings = await _get_or_create_settings()
        return settings.config or _default_settings_payload()

    @put()
    async def update_settings(
        self,
        data: NoteTakerSettingsSchema = Body(),
    ) -> dict[str, Any]:
        salesforce_settings = (data.integration or {}).get("salesforce") or {}
        if salesforce_settings.get("send_transcript_to_salesforce") and (
            not salesforce_settings.get("salesforce_api_server")
            or not salesforce_settings.get("salesforce_stt_recording_tool")
        ):
            raise ValueError(
                "Salesforce API server and STT recording tool are required when "
                "send_transcript_to_salesforce is enabled."
            )
        async with async_session_maker() as session:
            stmt = select(Settings).where(
                Settings.system_name == NOTE_TAKER_SETTINGS_SYSTEM_NAME
            )
            result = await session.execute(stmt)
            settings = result.scalars().first()

            if settings is None:
                settings = Settings(
                    name="Note Taker Settings",
                    system_name=NOTE_TAKER_SETTINGS_SYSTEM_NAME,
                    description="Settings for the Teams note taker bot.",
                    config=_default_settings_payload(),
                )
                session.add(settings)

            settings.config = data.model_dump()
            await session.commit()
            await session.refresh(settings)
            return settings.config or _default_settings_payload()

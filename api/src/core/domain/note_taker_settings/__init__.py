"""Note Taker settings domain.

Owns the Pydantic schema for `note_taker_settings.config` and the advanced-
alchemy service for the table itself. The runtime/handlers still live in
`services/agents/teams/` for now — see `NOTE_TAKER_ARCHITECTURE_REVIEW.md`
Phase 3/4 for the planned split. New callers should import from this package
rather than from `services.agents.teams.note_taker_settings` so the shim
there can shrink in subsequent slices.
"""

from .schemas import (
    CURRENT_SETTINGS_REVISION,
    IntegrationConfluenceSchema,
    IntegrationSalesforceSchema,
    IntegrationsSchema,
    NoteTakerSettingsRecordCreateSchema,
    NoteTakerSettingsRecordUpdateSchema,
    NoteTakerSettingsSchema,
    PromptSettingSchema,
)
from .service import NoteTakerSettingsService

__all__ = [
    "CURRENT_SETTINGS_REVISION",
    "IntegrationConfluenceSchema",
    "IntegrationSalesforceSchema",
    "IntegrationsSchema",
    "NoteTakerSettingsRecordCreateSchema",
    "NoteTakerSettingsRecordUpdateSchema",
    "NoteTakerSettingsSchema",
    "NoteTakerSettingsService",
    "PromptSettingSchema",
]

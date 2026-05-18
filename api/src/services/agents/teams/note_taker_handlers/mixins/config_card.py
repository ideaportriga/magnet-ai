"""Config-picker adaptive-card methods for NoteTakerHandlerState.

Split out of `state.py` — see NOTE_TAKER_REVISION_PLAN.md §3.2 P1-a.
Covers everything that touches the `/config` picker card:

* loading + listing available `note_taker_settings` rows
* rendering the picker card (initial + refresh-after-action)
* saving a config selection onto the `teams_meeting` row
* saving keyterms onto a config
* Salesforce account name → account_id resolution and binding

Relies on ``self.deps`` and ``self._logger`` from the concrete class.
"""

from __future__ import annotations

import datetime as dt
import json

from sqlalchemy import func, select, update

from microsoft_agents.activity import Activity, Attachment
from microsoft_agents.hosting.core import TurnContext

from core.db.models.teams import TeamsMeeting
from core.db.models.teams.note_taker_settings import (
    NoteTakerSettings as NoteTakerSettingsModel,
)
from core.db.session import async_session_maker
from services.integrations.salesforce.note_taker import (
    account_lookup,
    config_requires_salesforce as sf_config_requires_salesforce,
    get_salesforce_api_server,
    pick_first_account_id_and_name,
    update_meeting_salesforce_account,
)

from ... import note_taker_store
from ...note_taker_cards import create_note_taker_config_picker_card
from ...note_taker_people import personal_config_store
from ...teams_user_store import normalize_bot_id


class ConfigCardMixin:
    """Adaptive-card "/config" picker workflow."""

    async def _load_config_picker_metadata(
        self, config_system_name: str | None
    ) -> tuple[bool, str]:
        """
        Resolve optional flags for the /config card (salesforce-enabled + keyterms).
        """
        system_name = str(config_system_name or "").strip()
        if not system_name:
            return False, ""
        try:
            settings = await self.deps.load_settings_by_system_name(system_name)
            salesforce_enabled = sf_config_requires_salesforce(settings)
            keyterms = str(settings.get("keyterms") or "")
            return salesforce_enabled, keyterms
        except Exception:
            return False, ""

    async def _handle_note_taker_config_set_picker(self, context: TurnContext) -> None:
        await self.deps.send_typing(context)

        meeting_context = self.deps.resolve_meeting_details(context)
        meeting_id = meeting_context.get("id")
        (
            _account_id,
            current_account_name,
            current_system_name,
        ) = await note_taker_store.get_meeting_account_info(context, meeting_id)

        salesforce_enabled, current_keyterms = await self._load_config_picker_metadata(
            current_system_name
        )

        try:
            async with async_session_maker() as session:
                stmt = select(
                    NoteTakerSettingsModel.id,
                    NoteTakerSettingsModel.name,
                    NoteTakerSettingsModel.system_name,
                    NoteTakerSettingsModel.description,
                ).order_by(NoteTakerSettingsModel.created_at.asc())
                # Filter to configs belonging to this bot's provider when known
                if self.deps.provider_system_name:
                    stmt = stmt.where(
                        NoteTakerSettingsModel.provider_system_name
                        == self.deps.provider_system_name
                    )
                result = await session.execute(stmt)
                rows = result.all()
        except Exception as err:
            self._logger.exception("Failed to list note taker configs for picker")
            await context.send_activity(
                f"Failed to list note taker configs: {getattr(err, 'message', str(err))}"
            )
            return

        if not rows:
            await context.send_activity(
                "No note taker configs found. Create one in the admin UI first."
            )
            return

        card = create_note_taker_config_picker_card(
            rows,
            current_system_name=current_system_name,
            current_account_name=current_account_name,
            current_keyterms=current_keyterms,
            salesforce_enabled=salesforce_enabled,
        )
        attachment = Attachment(
            content_type="application/vnd.microsoft.card.adaptive",
            content=card,
        )
        activity = Activity(type="message", attachments=[attachment])
        await context.send_activity(activity)

    async def _refresh_note_taker_config_picker_card(
        self,
        context: TurnContext,
        *,
        selected_system_name: str,
    ) -> None:
        try:
            async with async_session_maker() as session:
                stmt = select(
                    NoteTakerSettingsModel.id,
                    NoteTakerSettingsModel.name,
                    NoteTakerSettingsModel.system_name,
                    NoteTakerSettingsModel.description,
                ).order_by(NoteTakerSettingsModel.created_at.asc())
                if self.deps.provider_system_name:
                    stmt = stmt.where(
                        NoteTakerSettingsModel.provider_system_name
                        == self.deps.provider_system_name
                    )
                result = await session.execute(stmt)
                rows = result.all()
        except Exception as err:
            self._logger.debug(
                "Failed to refresh note taker config picker card: %s", err
            )
            return

        if not rows:
            return

        meeting_context = self.deps.resolve_meeting_details(context)
        meeting_id = meeting_context.get("id")
        (
            _account_id,
            current_account_name,
            _current_system_name,
        ) = await note_taker_store.get_meeting_account_info(context, meeting_id)

        salesforce_enabled, current_keyterms = await self._load_config_picker_metadata(
            selected_system_name
        )

        card = create_note_taker_config_picker_card(
            rows,
            current_system_name=selected_system_name,
            current_account_name=current_account_name,
            current_keyterms=current_keyterms,
            salesforce_enabled=salesforce_enabled,
        )
        attachment = Attachment(
            content_type="application/vnd.microsoft.card.adaptive",
            content=card,
        )
        outgoing = Activity(type="message", attachments=[attachment])

        activity = getattr(context, "activity", None)
        reply_to_id = getattr(activity, "reply_to_id", None)
        if reply_to_id:
            outgoing.id = reply_to_id
            try:
                updater = getattr(context, "update_activity", None)
                if callable(updater):
                    await updater(outgoing)
                    return
            except Exception as err:
                self._logger.debug(
                    "Failed to update config picker card activity %s: %s",
                    reply_to_id,
                    err,
                )

        try:
            await context.send_activity(outgoing)
        except Exception as err:
            self._logger.debug("Failed to send refreshed config picker card: %s", err)

    async def _handle_note_taker_config_set(
        self, context: TurnContext, config_system_name: str, *, show_typing: bool = True
    ) -> bool:
        await self._maybe_send_typing(context, show_typing)

        try:
            from core.domain.note_taker_settings.service import (
                NoteTakerSettingsService,
            )

            async with async_session_maker() as session:
                service = NoteTakerSettingsService(session=session)
                config_row = await service.get_one_or_none(
                    system_name=config_system_name
                )
        except Exception as err:
            self._logger.exception(
                "Failed to resolve note taker config %s", config_system_name
            )
            await context.send_activity(
                f"Failed to resolve note taker config: {getattr(err, 'message', str(err))}"
            )
            return False

        if config_row is None:
            await context.send_activity("Note taker config not found.")
            return False

        # In personal chats, store the config in the in-process store.
        if self.deps.is_personal_conversation(context):
            personal_config_store.set(context, config_row.system_name)
            return True

        meeting_context = self.deps.resolve_meeting_details(context)
        chat_id = meeting_context.get("conversationId")
        recipient = getattr(getattr(context, "activity", None), "recipient", None)
        bot_id = normalize_bot_id(getattr(recipient, "id", None))
        if not chat_id or not bot_id:
            await context.send_activity(
                "Could not resolve chat or bot id for this conversation."
            )
            return False

        now = dt.datetime.now(dt.timezone.utc)
        stmt = (
            update(TeamsMeeting)
            .where(TeamsMeeting.chat_id == chat_id, TeamsMeeting.bot_id == bot_id)
            .values(
                note_taker_settings_system_name=config_row.system_name,
                last_seen_at=now,
                updated_at=func.now(),
            )
        )

        try:
            async with async_session_maker() as session:
                try:
                    result = await session.execute(stmt)
                    await session.commit()
                except Exception:
                    await session.rollback()
                    raise
        except Exception as err:
            self._logger.exception(
                "Failed to update Teams meeting for note taker config set (chat_id=%s, bot_id=%s)",
                chat_id,
                bot_id,
            )
            await context.send_activity(
                f"Failed to save note taker config for this meeting: {getattr(err, 'message', str(err))}"
            )
            return False

        if getattr(result, "rowcount", 0) == 0:
            await context.send_activity("I couldn't find a meeting record to update.")
            return False

        return True

    async def _handle_note_taker_keyterms_set(
        self,
        context: TurnContext,
        *,
        config_system_name: str,
        keyterms: str,
        show_typing: bool = True,
        notify_user: bool = True,
    ) -> None:
        config_system_name = str(config_system_name or "").strip()
        if not config_system_name:
            await context.send_activity("Please pick a valid config.")
            return

        await self._maybe_send_typing(context, show_typing)

        try:
            from core.domain.note_taker_settings.service import (
                NoteTakerSettingsService,
            )

            async with async_session_maker() as session:
                service = NoteTakerSettingsService(session=session)
                config_row = await service.get_one_or_none(
                    system_name=config_system_name
                )
                if config_row is None:
                    await context.send_activity("Note taker config not found.")
                    return

                raw_config = config_row.config
                if isinstance(raw_config, str):
                    try:
                        raw_config = json.loads(raw_config)
                    except Exception:
                        raw_config = None

                config = dict(raw_config) if isinstance(raw_config, dict) else {}
                config["keyterms"] = str(keyterms or "").strip()
                config_row.config = config
                await session.commit()
        except Exception as err:
            self._logger.exception(
                "Failed to update keyterms for note taker config %s",
                config_system_name,
            )
            await context.send_activity(
                f"Failed to save keyterms: {getattr(err, 'message', str(err))}"
            )
            return

        if notify_user:
            await context.send_activity("Keyterms saved.")

    async def _handle_sf_account_set(
        self, context: TurnContext, account_name: str, *, show_typing: bool = True
    ) -> None:
        if not account_name:
            await context.send_activity("Usage: /sf-account-set ACCOUNT_NAME")
            return

        if not self.deps.is_meeting_conversation(context):
            await context.send_activity("This command works only in meeting chats.")
            return

        await self._maybe_send_typing(context, show_typing)

        try:
            settings = await self.deps.load_settings_for_context(context)
            salesforce_api_server = get_salesforce_api_server(settings)
            result = await account_lookup(account_name, server=salesforce_api_server)
        except Exception as err:
            self._logger.exception(
                "Salesforce account lookup failed for %s", account_name
            )
            await context.send_activity(
                f"Salesforce account lookup failed: {getattr(err, 'message', str(err))}"
            )
            return

        if not isinstance(result, list) or not result:
            await context.send_activity("No Salesforce accounts found to set.")
            return

        account_id, account_name_value = pick_first_account_id_and_name(
            result, fallback_account_name=account_name
        )
        if not account_id:
            await context.send_activity(
                "Salesforce account lookup did not return an accountId."
            )
            return

        meeting_context = self.deps.resolve_meeting_details(context)
        meeting_id = meeting_context.get("id")
        chat_id = meeting_context.get("conversationId")
        recipient = getattr(getattr(context, "activity", None), "recipient", None)
        bot_id = normalize_bot_id(getattr(recipient, "id", None))
        if not meeting_id or not chat_id or not bot_id:
            await context.send_activity(
                "Could not resolve meeting, chat, or bot id for this conversation."
            )
            return

        try:
            rowcount = await update_meeting_salesforce_account(
                chat_id=chat_id,
                bot_id=bot_id,
                account_id=account_id,
                account_name=account_name_value,
            )
        except Exception as err:
            self._logger.exception(
                "Failed to update Teams meeting for account set (meeting_id=%s, bot_id=%s)",
                meeting_id,
                bot_id,
            )
            await context.send_activity(
                f"Failed to save account for this meeting: {getattr(err, 'message', str(err))}"
            )
            return

        if rowcount == 0:
            await context.send_activity("I couldn't find a meeting record to update.")
            return

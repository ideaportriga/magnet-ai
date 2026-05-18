"""Auth / delegated-token / organizer-check methods for NoteTakerHandlerState.

Split out of the original `state.py` god-class — see
`NOTE_TAKER_REVISION_PLAN.md` §3.2 P1-a. The mixin relies on
``self.deps`` (:class:`NoteTakerHandlerDeps`) and ``self._logger``
from the concrete class; no instance state of its own.
"""

from __future__ import annotations

from microsoft_agents.activity import Activity, ConversationReference
from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.hosting.teams import TeamsInfo

from ... import note_taker_store


class AuthMixin:
    """Token + organizer-identity helpers for the Teams note-taker bot."""

    async def _has_existing_token(self, context: TurnContext, handler_id: str) -> bool:
        try:
            handler = self.deps.app.auth._resolve_handler(handler_id)
            flow, _ = await handler._load_flow(context)
            token_response = await flow.get_user_token()
            return bool(getattr(token_response, "token", None))
        except Exception as err:
            self._logger.debug(
                "Token precheck failed (handler=%s): %s",
                handler_id,
                getattr(err, "message", str(err)),
            )
            return False

    async def _get_delegated_token(
        self,
        context: TurnContext,
        handler_id: str,
        failure_message: str,
    ) -> str | None:
        try:
            handler = self.deps.app.auth._resolve_handler(handler_id)
            flow, _ = await handler._load_flow(context)
            token_response = await flow.get_user_token()
            return getattr(token_response, "token", None)
        except Exception as err:
            self._logger.error(
                "Auth failed handler_id=%s message=%s",
                handler_id,
                getattr(err, "message", str(err)),
            )
        await context.send_activity(failure_message)
        return None

    async def _is_meeting_organizer(self, context: TurnContext) -> bool:
        user = self.deps.resolve_user_info(context)
        organizer = await self._get_meeting_organizer_identity(context)
        organizer_id = organizer.get("id")
        organizer_aad = organizer.get("aad_object_id")

        user_id = user.get("id")
        user_aad = user.get("aad_object_id")

        if user_id and organizer_id and user_id == organizer_id:
            return True
        if user_aad and organizer_aad and user_aad == organizer_aad:
            return True
        return False

    async def _ensure_meeting_organizer_and_signed_in(
        self, context: TurnContext, handler_id: str
    ) -> bool:
        try:
            is_organizer = await self._is_meeting_organizer(context)
        except Exception as err:
            self._logger.warning(
                "Unable to verify meeting organizer: %s",
                getattr(err, "message", str(err)),
            )
            await context.send_activity(
                "I couldn't verify that you're the meeting organizer. Please try again or message me directly."
            )
            return False

        if not is_organizer:
            await context.send_activity(
                "Meeting commands are accepted only from the meeting organizer."
            )
            return False

        signed_in = await self._has_existing_token(context, handler_id)
        if not signed_in:
            await context.send_activity(
                "Please authenticate with me in our cozy 1:1 chat before using meeting commands."
            )
            return False

        return True

    async def _get_token_proactively(
        self,
        *,
        conv_ref,
        handler_id: str,
        aad_object_id: str | None = None,
        user_id: str | None = None,
        azure_tenant_id: str | None = None,
        notify_if_missing: bool = True,
    ) -> str | None:
        continuation = Activity.create_event_activity()
        continuation.name = "proactiveTokenCheck"

        normalized_ref = ConversationReference.model_validate(conv_ref)
        continuation.apply_conversation_reference(normalized_ref, is_incoming=True)

        if aad_object_id and getattr(continuation, "from_property", None):
            continuation.from_property.aad_object_id = aad_object_id
        if user_id and getattr(continuation, "from_property", None):
            continuation.from_property.id = user_id

        if azure_tenant_id:
            # Bot Framework payload keys stay on the wire: channel_data has
            # `tenant.id`, ConversationReference exposes `tenant_id` as an SDK
            # attribute. Only the Python parameter name was renamed.
            continuation.channel_data = continuation.channel_data or {}
            continuation.channel_data.setdefault("tenant", {"id": azure_tenant_id})

            conv = getattr(continuation, "conversation", None)
            if conv is not None and getattr(conv, "tenant_id", None) in (None, ""):
                try:
                    conv.tenant_id = azure_tenant_id
                except Exception:
                    pass

        token_holder: dict[str, str | None] = {"token": None}

        async def callback(proactive_context: TurnContext):
            try:
                handler = self.deps.app.auth._resolve_handler(handler_id)
                flow, _ = await handler._load_flow(proactive_context)
                token_response = await flow.get_user_token()
                token_holder["token"] = getattr(token_response, "token", None)
            except Exception as err:
                message = getattr(err, "message", None) or str(err)
                self._logger.warning(
                    "Proactive token check failed (handler=%s): %s",
                    handler_id,
                    message,
                )
                return

            if not token_holder["token"] and notify_if_missing:
                await proactive_context.send_activity(
                    "I need your delegated token to proceed. "
                    "Please use **/sign-in** in our 1:1 chat to authenticate."
                )

        try:
            await self.deps.adapter.continue_conversation(
                self.deps.bot_app_id, continuation, callback
            )
        except Exception as err:
            self._logger.warning(
                "Proactive token check conversation failed (handler=%s): %s",
                handler_id,
                getattr(err, "message", None) or str(err),
            )

        return token_holder["token"]

    async def _get_meeting_organizer_identity(
        self,
        context: TurnContext,
    ) -> dict[str, str | None]:
        meeting_info = await TeamsInfo.get_meeting_info(context)
        organizer_obj = getattr(meeting_info, "organizer", None) or {}
        return {
            "id": getattr(organizer_obj, "id", None),
            "aad_object_id": getattr(organizer_obj, "aadObjectId", None),
        }

    async def _get_organizer_delegated_token_from_cache(
        self,
        context: TurnContext,
    ) -> str | None:
        if not self.deps.is_meeting_conversation(context):
            return None

        try:
            organizer = await self._get_meeting_organizer_identity(context)
        except Exception as err:
            self._logger.warning(
                "Unable to resolve meeting organizer for subscription: %s",
                getattr(err, "message", str(err)),
            )
            return None

        organizer_aad = organizer.get("aad_object_id")
        organizer_id = organizer.get("id")
        if not organizer_aad and not organizer_id:
            self._logger.info(
                "Organizer identity missing; skipping delegated token fetch for subscription."
            )
            return None

        conv_ref = await note_taker_store.fetch_organizer_conversation_reference(
            organizer_aad=organizer_aad, bot_app_id=self.deps.bot_app_id
        )
        if not conv_ref:
            self._logger.info(
                "No organizer personal conversation reference available for subscription token fetch."
            )
            return None

        return await self._get_token_proactively(
            conv_ref=conv_ref,
            handler_id=self.deps.auth_handler_id,
            aad_object_id=organizer_aad,
            user_id=organizer_id,
            azure_tenant_id=self.deps.bot_azure_tenant_id,
            notify_if_missing=False,
        )

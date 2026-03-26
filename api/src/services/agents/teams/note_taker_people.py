from __future__ import annotations

import re
from typing import Any

from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.hosting.teams import TeamsInfo


class PersonalConfigStore:
    """
    In-memory store for the active note-taker config in personal/direct chats.

    In personal chats there is no meeting record, so the user's config choice
    is stored in-process per conversation.  Keyed by conversation_id.
    """

    def __init__(self) -> None:
        self._store: dict[str, str] = {}  # conv_id → settings system_name

    def _conv_id(self, context: TurnContext) -> str:
        activity = getattr(context, "activity", None)
        conversation = getattr(activity, "conversation", None)
        return str(getattr(conversation, "id", None) or "default")

    def set(self, context: TurnContext, system_name: str) -> None:
        self._store[self._conv_id(context)] = system_name

    def get(self, context: TurnContext) -> str | None:
        return self._store.get(self._conv_id(context))

    def clear(self, context: TurnContext) -> None:
        self._store.pop(self._conv_id(context), None)


class ManualParticipantStore:
    """
    In-memory store for manually entered participants in personal/direct chat.

    Used when there is no Teams meeting context to pull members from.
    Stored per-conversation (keyed by conversation_id from TurnContext).
    """

    def __init__(self) -> None:
        self._store: dict[str, list[dict[str, str]]] = {}

    def _conv_id(self, context: TurnContext) -> str:
        activity = getattr(context, "activity", None)
        conversation = getattr(activity, "conversation", None)
        return str(getattr(conversation, "id", None) or "default")

    def add(self, context: TurnContext, raw_name: str) -> dict[str, str] | None:
        """
        Parse 'First Last' or 'First Last <email@example.com>' and add to the store.
        Returns the parsed person dict, or None if the name is blank.
        """
        name = raw_name.strip()
        if not name:
            return None

        email = ""
        email_match = re.search(r"<([^>]+@[^>]+)>", name)
        if email_match:
            email = email_match.group(1).strip()
            name = name[: email_match.start()].strip()

        parts = name.split(maxsplit=1)
        first_name = parts[0] if parts else name
        last_name = parts[1] if len(parts) > 1 else ""

        person = {"first_name": first_name, "last_name": last_name, "email": email}
        conv_id = self._conv_id(context)
        participants = self._store.setdefault(conv_id, [])
        # Avoid duplicates by display name
        display = (first_name + " " + last_name).strip().lower()
        if not any(
            (p.get("first_name", "") + " " + p.get("last_name", "")).strip().lower()
            == display
            for p in participants
        ):
            participants.append(person)
        return person

    def list(self, context: TurnContext) -> list[dict[str, str]]:
        conv_id = self._conv_id(context)
        return list(self._store.get(conv_id, []))

    def clear(self, context: TurnContext) -> int:
        conv_id = self._conv_id(context)
        count = len(self._store.pop(conv_id, []))
        return count


async def get_invited_people(context: TurnContext) -> list[dict[str, str]]:
    invited: list[dict[str, str]] = []
    seen: set[str] = set()
    continuation_token: str | None = None

    while True:
        paged = await TeamsInfo.get_paged_members(
            context, page_size=100, continuation_token=continuation_token
        )
        members = getattr(paged, "members", None) or []
        for member in members:
            given = (
                getattr(member, "given_name", None)
                or getattr(member, "givenName", None)
                or ""
            )
            surname = (
                getattr(member, "surname", None)
                or getattr(member, "last_name", None)
                or getattr(member, "lastName", None)
                or ""
            )
            email = (
                getattr(member, "email", None)
                or getattr(member, "user_principal_name", None)
                or getattr(member, "userPrincipalName", None)
                or ""
            )

            given = str(given or "").strip()
            surname = str(surname or "").strip()
            email = str(email or "").strip()

            if not given and not surname:
                display_name = str(getattr(member, "name", "") or "").strip()
                if display_name:
                    pieces = display_name.split()
                    if pieces:
                        given = pieces[0]
                        if len(pieces) > 1:
                            surname = " ".join(pieces[1:])

            dedupe_key = (email or str(getattr(member, "id", "") or "")).strip()
            if not dedupe_key or dedupe_key in seen:
                continue
            seen.add(dedupe_key)

            invited.append(
                {
                    "first_name": given,
                    "last_name": surname,
                    "email": email,
                }
            )

        continuation_token = getattr(paged, "continuation_token", None)
        if not continuation_token:
            break

    invited.sort(
        key=lambda p: (
            (p.get("last_name") or "").lower(),
            (p.get("first_name") or "").lower(),
            (p.get("email") or "").lower(),
        )
    )
    return invited


def invited_people_to_names(invited_people: list[dict[str, Any]] | None) -> list[str]:
    names: list[str] = []
    for person in invited_people or []:
        first_name = str(person.get("first_name") or "").strip()
        last_name = str(person.get("last_name") or "").strip()
        display_name = " ".join([p for p in (first_name, last_name) if p]).strip()
        if display_name:
            names.append(display_name)
    return names


def invited_people_to_first_names(
    invited_people: list[dict[str, Any]] | None,
) -> list[str]:
    names: list[str] = []
    for person in invited_people or []:
        first_name = str(person.get("first_name") or "").strip()
        if first_name:
            names.append(first_name)
            continue

        last_name = str(person.get("last_name") or "").strip()
        if last_name:
            names.append(last_name)
    return names


# Module-level singleton — shared between note_taker.py and state.py handlers.
personal_config_store = PersonalConfigStore()

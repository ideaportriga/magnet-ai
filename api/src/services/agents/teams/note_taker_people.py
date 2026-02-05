from __future__ import annotations

from typing import Any

from microsoft_agents.hosting.core import TurnContext
from microsoft_agents.hosting.teams import TeamsInfo


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

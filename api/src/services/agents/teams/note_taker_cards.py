from __future__ import annotations

import datetime as dt
from typing import Any


_MEETING_COMMANDS = [
    "**/welcome** - Show this help",
    "**/sign-in** - Sign in to allow access to meeting recordings (1:1 chat).",
    "**/sign-out** - Sign out and revoke access.",
    "**/whoami** - Show your Teams identity and sign-in status.",
    "**/config** - Pick a note taker config for this meeting.",
    "**/recordings-list** - List meeting recordings.",
    "**/process-transcript-job TRANSCRIPTION_JOB_ID** - Process an existing transcription job.",
    "**/process-recording RECORDING_ID** - Download and transcribe a specific recording.",
    "**/process-file LINK** - Download and transcribe an audio/video file.",
    "**/meeting-info** - Show current meeting details.",
]

_PERSONAL_COMMANDS = [
    "**/welcome** - Show this help",
    "**/sign-in** - Sign in to allow access to meeting recordings.",
    "**/sign-out** - Sign out and revoke access.",
    "**/whoami** - Show your Teams identity and sign-in status.",
    "**/recordings-list** - List your recent meetings with available recordings.",
    "**/my-meetings** - Show your recently processed meetings.",
    "**/process-file LINK** - Download and transcribe an audio/video file via URL.",
    "**Drop a file** - Attach an audio/video file directly to the chat to transcribe it.",
    "**/participants add Full Name** - Add a participant for speaker hints.",
    "**/participants list** - Show current participants.",
    "**/participants clear** - Remove all participants.",
    "**/process-transcript-job TRANSCRIPTION_JOB_ID** - Re-process an existing transcription job.",
]


def create_note_taker_welcome_card(
    bot_name: str | None, *, is_personal: bool = False
) -> dict[str, Any]:
    commands = _PERSONAL_COMMANDS if is_personal else _MEETING_COMMANDS

    body: list[dict[str, Any]] = [
        {
            "type": "TextBlock",
            "text": "Welcome to Magnet note taker",
            "weight": "Bolder",
            "size": "Large",
        },
    ]
    if bot_name:
        body.append(
            {
                "type": "TextBlock",
                "text": f"I am your {bot_name}.",
                "wrap": True,
                "spacing": "Small",
            }
        )
    body.extend(
        [
            {
                "type": "TextBlock",
                "text": (
                    "I capture meeting recordings and generate transcripts, summaries, chapters, and insights."
                ),
                "wrap": True,
            },
            {
                "type": "TextBlock",
                "text": "Commands",
                "weight": "Bolder",
                "spacing": "Medium",
            },
        ]
    )
    for command in commands:
        body.append(
            {
                "type": "TextBlock",
                "text": f"- {command}",
                "wrap": True,
                "spacing": "Small",
            }
        )

    return {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.5",
        "body": body,
        "msteams": {"width": "Full"},
    }


def create_speaker_mapping_card(
    pending_id: str,
    speaker_mapping: dict[str, str],
    suggested_keyterms: list[str],
    *,
    settings_keyterms: str | None = None,
) -> dict[str, Any]:
    """Adaptive Card shown after transcription to let the user confirm/edit speaker names."""

    body: list[dict[str, Any]] = [
        {
            "type": "TextBlock",
            "text": "Review Speaker Names",
            "weight": "Bolder",
            "size": "Large",
        },
        {
            "type": "TextBlock",
            "text": (
                "The AI identified the following speakers. "
                "Edit the names if needed, then click **Confirm** to continue."
            ),
            "wrap": True,
            "spacing": "Small",
        },
    ]

    # One TextInput per speaker
    for speaker_key in sorted(speaker_mapping.keys()):
        suggested_name = speaker_mapping.get(speaker_key, "")
        body.append(
            {
                "type": "TextBlock",
                "text": speaker_key,
                "weight": "Bolder",
                "spacing": "Medium",
            }
        )
        body.append(
            {
                "type": "Input.Text",
                "id": f"speaker__{speaker_key}",
                "value": suggested_name,
                "placeholder": "Full name",
                "spacing": "Small",
            }
        )

    # Keyterms section — pre-fill with AI suggestions merged with config keyterms
    all_keyterms: list[str] = list(suggested_keyterms)
    if settings_keyterms:
        import re as _re

        for t in _re.split(r"[,;\n]+", settings_keyterms):
            t = t.strip()
            if t and t not in all_keyterms:
                all_keyterms.append(t)
    keyterms_value = ", ".join(all_keyterms)

    body.extend(
        [
            {
                "type": "TextBlock",
                "text": "Key Terms",
                "weight": "Bolder",
                "spacing": "Medium",
            },
            {
                "type": "TextBlock",
                "text": "Comma-separated terms to highlight in the transcript.",
                "wrap": True,
                "spacing": "Small",
                "isSubtle": True,
            },
            {
                "type": "Input.Text",
                "id": "keyterms",
                "value": keyterms_value,
                "placeholder": "e.g. pricing, renewal, roadmap",
                "isMultiline": False,
                "spacing": "Small",
            },
            {
                "type": "TextBlock",
                "text": "Meeting Notes (optional)",
                "weight": "Bolder",
                "spacing": "Medium",
            },
            {
                "type": "TextBlock",
                "text": "Add any context or corrections for the summary and chapters.",
                "wrap": True,
                "spacing": "Small",
                "isSubtle": True,
            },
            {
                "type": "Input.Text",
                "id": "meeting_notes",
                "placeholder": "e.g. action items, decisions, corrections...",
                "isMultiline": True,
                "spacing": "Small",
            },
            {
                "type": "ActionSet",
                "spacing": "Medium",
                "actions": [
                    {
                        "type": "Action.Submit",
                        "title": "Confirm",
                        "style": "positive",
                        "data": {
                            "magnet_action": "confirm_speaker_mapping",
                            "pending_id": pending_id,
                        },
                    },
                    {
                        "type": "Action.Submit",
                        "title": "Skip",
                        "data": {
                            "magnet_action": "confirm_speaker_mapping",
                            "pending_id": pending_id,
                            "skip": True,
                        },
                    },
                ],
            },
        ]
    )

    return {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.5",
        "body": body,
        "msteams": {"width": "Full"},
    }


def create_note_taker_config_picker_card(
    rows: list[tuple[Any, Any, Any, Any]],
    *,
    current_system_name: str | None = None,
    current_account_name: str | None = None,
    current_keyterms: str | None = None,
    salesforce_enabled: bool = False,
    limit: int = 15,
) -> dict[str, Any]:
    shown = rows[:limit]
    header = "Pick a note taker config"
    current = current_system_name or "None"

    choices: list[dict[str, Any]] = []
    for row in shown:
        config_id, name, system_name, description = row
        if not system_name:
            continue
        title = (name or system_name or str(config_id) or "").strip()
        desc = (description or "").strip()
        if desc:
            compact_desc = " ".join(desc.split())
            if len(compact_desc) > 90:
                compact_desc = f"{compact_desc[:87]}..."
            title = f"{title} - {compact_desc}"
        choices.append({"title": title, "value": system_name})

    body: list[dict[str, Any]] = [
        {
            "type": "TextBlock",
            "text": header,
            "weight": "Bolder",
            "size": "Large",
        },
        {
            "type": "TextBlock",
            "text": f"Current config: {current}",
            "wrap": True,
            "spacing": "Small",
        },
        {
            "type": "TextBlock",
            "text": "Select a config and click Apply to set it for this meeting.",
            "wrap": True,
            "spacing": "Small",
        },
    ]

    if salesforce_enabled:
        body.extend(
            [
                {
                    "type": "TextBlock",
                    "text": "Salesforce account",
                    "weight": "Bolder",
                    "spacing": "Medium",
                },
                {
                    "type": "TextBlock",
                    "text": (
                        "This config sends transcripts to Salesforce. "
                        "Enter the account name and click Apply."
                    ),
                    "wrap": True,
                    "spacing": "Small",
                    "isSubtle": True,
                },
                {
                    "type": "Input.Text",
                    "id": "account_name",
                    "value": (current_account_name or "").strip(),
                    "placeholder": "Account name (e.g. AccountTest11)",
                    "spacing": "Small",
                },
            ]
        )

    body.extend(
        [
            {
                "type": "TextBlock",
                "text": "Keyterms",
                "weight": "Bolder",
                "spacing": "Medium",
            },
            {
                "type": "TextBlock",
                "text": "Comma / semicolon / newline separated.",
                "wrap": True,
                "spacing": "Small",
                "isSubtle": True,
            },
            {
                "type": "Input.Text",
                "id": "keyterms",
                "value": (current_keyterms or "").strip(),
                "placeholder": "e.g. pricing, renewal, roadmap",
                "isMultiline": True,
                "spacing": "Small",
            },
        ]
    )

    body.extend(
        [
            {
                "type": "Input.ChoiceSet",
                "id": "config_system_name",
                "style": "expanded",
                "isMultiSelect": False,
                "value": current_system_name or "",
                "choices": choices,
            },
            {
                "type": "ActionSet",
                "spacing": "Medium",
                "actions": [
                    {
                        "type": "Action.Submit",
                        "title": "Apply",
                        "data": {"magnet_action": "note_taker_config_set"},
                    },
                    {
                        "type": "Action.Submit",
                        "title": "Save keyterms",
                        "data": {"magnet_action": "note_taker_keyterms_set"},
                    },
                ],
            },
        ]
    )

    if len(rows) > limit:
        body.append(
            {
                "type": "TextBlock",
                "text": f"Showing first {limit} of {len(rows)} configs.",
                "wrap": True,
                "spacing": "Medium",
                "isSubtle": True,
            }
        )

    return {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.5",
        "body": body,
        "msteams": {"width": "Full"},
    }


def create_my_meetings_card(meetings: list[dict[str, Any]]) -> dict[str, Any]:
    """Adaptive Card listing recently processed meetings for the current user."""

    body: list[dict[str, Any]] = [
        {
            "type": "TextBlock",
            "text": "Your Recent Meetings",
            "weight": "Bolder",
            "size": "Large",
        },
        {
            "type": "TextBlock",
            "text": f"Showing {len(meetings)} most recent processed meeting(s).",
            "wrap": True,
            "spacing": "Small",
            "isSubtle": True,
        },
    ]

    for meeting in meetings:
        file_id: str = meeting.get("file_id") or ""
        filename: str | None = meeting.get("filename")
        status: str = meeting.get("status") or "unknown"
        duration_seconds: float | None = meeting.get("duration_seconds")
        created_at: dt.datetime | None = meeting.get("created_at")

        # Title: use filename stripped of extension, fallback to file_id
        if filename:
            title = filename.rsplit(".", 1)[0] if "." in filename else filename
        else:
            title = file_id[:24] + "…" if len(file_id) > 24 else file_id

        # Format date
        if created_at:
            try:
                date_str = created_at.strftime("%d %b %Y, %H:%M")
            except Exception:
                date_str = str(created_at)[:16]
        else:
            date_str = "Unknown date"

        # Format duration
        if duration_seconds:
            mins = int(duration_seconds) // 60
            secs = int(duration_seconds) % 60
            duration_str = f"{mins}m {secs}s"
        else:
            duration_str = "—"

        # Status icon
        status_icon = {"completed": "✅", "failed": "❌", "started": "⏳"}.get(
            status, "🔄"
        )

        body.append(
            {
                "type": "Container",
                "spacing": "Medium",
                "separator": True,
                "items": [
                    {
                        "type": "TextBlock",
                        "text": title,
                        "weight": "Bolder",
                        "wrap": True,
                    },
                    {
                        "type": "FactSet",
                        "facts": [
                            {"title": "Date", "value": date_str},
                            {"title": "Duration", "value": duration_str},
                            {"title": "Status", "value": f"{status_icon} {status}"},
                            {"title": "Job ID", "value": file_id},
                        ],
                        "spacing": "Small",
                    },
                    {
                        "type": "ActionSet",
                        "actions": [
                            {
                                "type": "Action.Submit",
                                "title": "View transcript",
                                "data": {
                                    "magnet_action": "view_transcript",
                                    "job_id": file_id,
                                },
                            },
                            {
                                "type": "Action.Submit",
                                "title": "Re-process",
                                "data": {
                                    "magnet_action": "reprocess_meeting",
                                    "job_id": file_id,
                                },
                            },
                        ],
                        "spacing": "Small",
                    },
                ],
            }
        )

    return {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.5",
        "body": body,
        "msteams": {"width": "Full"},
    }


def _format_meeting_datetime(iso_str: str | None) -> str:
    if not iso_str:
        return "Unknown date"
    try:
        parsed = dt.datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
        return parsed.strftime("%d %b %Y, %H:%M UTC")
    except Exception:
        return str(iso_str)[:16]


def _format_rec_duration(seconds: float | int | None) -> str:
    if seconds is None:
        return "—"
    total = int(seconds)
    mins, secs = divmod(total, 60)
    hours, mins = divmod(mins, 60)
    if hours:
        return f"{hours}h {mins}m {secs}s"
    return f"{mins}m {secs}s"


def _format_size(size_bytes: int | float | None) -> str:
    if size_bytes is None:
        return "—"
    size = float(size_bytes)
    if size >= 1_073_741_824:
        return f"{size / 1_073_741_824:.1f} GB"
    if size >= 1_048_576:
        return f"{size / 1_048_576:.1f} MB"
    if size >= 1024:
        return f"{size / 1024:.1f} KB"
    return f"{int(size)} B"


def create_user_recordings_card(
    meetings_with_recordings: list[dict[str, Any]],
) -> dict[str, Any]:
    """Adaptive Card listing the user's recent meetings that have recordings.

    ``meetings_with_recordings`` is a list produced by
    :func:`list_user_meetings_with_recordings` in ``graph.py``.
    """

    body: list[dict[str, Any]] = [
        {
            "type": "TextBlock",
            "text": "Your Recent Recordings",
            "weight": "Bolder",
            "size": "Large",
        },
        {
            "type": "TextBlock",
            "text": f"Found {len(meetings_with_recordings)} meeting(s) with recordings.",
            "wrap": True,
            "spacing": "Small",
            "isSubtle": True,
        },
    ]

    for meeting in meetings_with_recordings:
        subject = meeting.get("subject") or "Untitled meeting"
        start_str = _format_meeting_datetime(meeting.get("startDateTime"))
        recordings: list[dict[str, Any]] = meeting.get("recordings") or []

        meeting_items: list[dict[str, Any]] = [
            {
                "type": "TextBlock",
                "text": subject,
                "weight": "Bolder",
                "wrap": True,
            },
            {
                "type": "TextBlock",
                "text": f"📅 {start_str}   |   📹 {len(recordings)} recording(s)",
                "wrap": True,
                "spacing": "Small",
                "isSubtle": True,
            },
        ]

        for rec in recordings:
            rec_id = rec.get("id") or "n/a"
            duration = rec.get("duration")
            size = rec.get("size")
            created = _format_meeting_datetime(rec.get("createdDateTime"))

            facts = [
                {"title": "Recorded", "value": created},
                {"title": "Duration", "value": _format_rec_duration(duration)},
            ]
            if size is not None:
                facts.append({"title": "Size", "value": _format_size(size)})

            meeting_items.append(
                {
                    "type": "FactSet",
                    "facts": facts,
                    "spacing": "Small",
                }
            )
            meeting_items.append(
                {
                    "type": "ActionSet",
                    "actions": [
                        {
                            "type": "Action.Submit",
                            "title": "Process this recording",
                            "data": {
                                "magnet_action": "process_recording_from_list",
                                "meeting_id": meeting.get("meeting_id"),
                                "recording_id": rec_id,
                            },
                        }
                    ],
                    "spacing": "Small",
                }
            )

        body.append(
            {
                "type": "Container",
                "spacing": "Medium",
                "separator": True,
                "items": meeting_items,
            }
        )

    if not meetings_with_recordings:
        body.append(
            {
                "type": "TextBlock",
                "text": "No meetings with recordings found in the last 30 days.",
                "wrap": True,
                "spacing": "Medium",
            }
        )

    return {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.5",
        "body": body,
        "msteams": {"width": "Full"},
    }

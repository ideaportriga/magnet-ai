from typing import Any


def create_note_taker_welcome_card(bot_name: str | None) -> dict[str, Any]:
    commands = [
        "**/welcome** - Show this help",
        "**/sign-in** - Sign in to allow access to meeting recordings (1:1 chat).",
        "**/sign-out** - Sign out and revoke access.",
        "**/whoami** - (to be removed) Show your Teams identity and sign-in status.",
        "**/config** - Pick a note taker config for this meeting.",
        "**/recordings-list** - List meeting recordings.",
        "**/recordings-find** - (to be removed) List meeting recordings and transcribe the latest.",
        "**/process-transcript-job TRANSCRIPTION_JOB_ID** - Process an existing transcription job.",
        "**/process-recording RECORDING_ID** - Download and transcribe a specific recording.",
        "**/process-file LINK** - (to be removed) Download and transcribe an audio/video file.",
        "**/meeting-info** - Show current meeting details.",
    ]

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


def create_note_taker_config_picker_card(
    rows: list[tuple[Any, Any, Any, Any]],
    *,
    current_system_name: str | None = None,
    current_account_name: str | None = None,
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
                    }
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

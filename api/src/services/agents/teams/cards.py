import os


dislike_reason_titles = {
    "other": "Other",
    "not_relevant": "Not relevant",
    "inaccurate": "Inaccurate",
    "outdated": "Outdated",
}


def create_welcome_card(bot_name, agent_system_name):
    return {
        "type": "AdaptiveCard",
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "version": "1.5",
        "body": [
            {
                "type": "TextBlock",
                "text": "👋 Welcome aboard!",
                "weight": "Bolder",
                "size": "Large",
            },
            {
                "type": "TextBlock",
                "text": f"I'm your **{bot_name}**.",
                "wrap": True,
                "spacing": "Small",
            },
            {
                "type": "FactSet",
                "facts": [
                    {
                        "title": "📝 Ask",
                        "value": f"me a question, I will send it to the **{agent_system_name}** Magnet AI Agent, and send its response back to you.",
                    },
                ],
            },
        ],
        "actions": [
            {
                "type": "Action.OpenUrl",
                "title": "Learn More",
                "url": "https://pro.ideaportriga.com/magnet-ai",
            },
        ],
        "msteams": {"width": "Full"},
    }


def create_magnet_response_card(magnet_response):
    conversation_id = magnet_response.get("conversation_id")
    message_id = magnet_response.get("message_id")
    text = magnet_response.get("content")

    dislike_reasons = list(dislike_reason_titles.keys())

    columns = [
        {
            "type": "Column",
            "width": "auto",
            "items": [
                {
                    "type": "ActionSet",
                    "actions": [
                        {
                            "type": "Action.Execute",
                            "verb": "like",
                            "title": "👍",
                            "data": {"message_id": message_id, "conversation_id": conversation_id, "text": text},
                            "associatedInputs": "none",
                            "isPrimary": True,
                        }
                    ],
                }
            ],
        },
        {
            "type": "Column",
            "width": "auto",
            "items": [
                {
                    "type": "ActionSet",
                    "actions": [
                        {
                            "type": "Action.ToggleVisibility",
                            "title": "👎",
                            "targetElements": [
                                {"elementId": "dislike_fields", "isVisible": True},
                                {"elementId": "action_buttons", "isVisible": False}
                            ],
                            "associatedInputs": "none",
                        }
                    ],
                }
            ],
        },
        {"type": "Column", "width": "stretch", "items": []},
    ]


    return {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": [
            {"type": "TextBlock", "text": "AI Assistant Response", "weight": "Bolder", "size": "Large"},
            {"type": "TextBlock", "text": text, "wrap": True},
            {
                "type": "Container",
                "id": "dislike_fields",
                "isVisible": False,
                "items": [
                    {
                        "type": "Input.ChoiceSet",
                        "id": "dislike_reason",
                        "label": "Reason",
                        "style": "compact",
                        "value": "other",
                        "choices": [
                            {"title": dislike_reason_titles[reason], "value": reason}
                            for reason in dislike_reasons
                        ],
                    },
                    {
                        "type": "Input.Text",
                        "id": "dislike_comment",
                        "label": "Comment (optional)",
                        "placeholder": "Tell us more...",
                        "isMultiline": False,
                        "maxLength": 50,
                    },
                    {
                        "type": "ActionSet",
                        "actions": [
                            {
                                "type": "Action.Execute",
                                "title": "✅ Confirm",
                                "verb": "dislike",
                                "data": {"message_id": message_id, "conversation_id": conversation_id, "text": text},
                                "associatedInputs": "auto",
                            },
                            {
                                "type": "Action.ToggleVisibility",
                                "title": "✖️ Cancel",
                                "targetElements": [
                                    {"elementId": "dislike_fields", "isVisible": False},
                                    {"elementId": "action_buttons", "isVisible": True}
                                ],
                                "associatedInputs": "none",
                            },
                        ],
                    },
                ],
            },
            {"type": "ColumnSet", "id": "action_buttons", "spacing": "Medium", "columns": columns},
        ],
        "msteams": {"width": "Full"},
    }


def create_feedback_result_card(payload):
    text = payload.get("text")
    reaction = payload.get("reaction")
    reason = payload.get("reason")
    comment = payload.get("comment")

    liked = reaction == "like"
    header = "AI Assistant Response"
    ack = "You liked it 👍" if liked else "You disliked it 👎"

    body = [
        {"type": "TextBlock", "text": header, "weight": "Bolder", "size": "Large"},
        {"type": "TextBlock", "text": text, "wrap": True},
        {"type": "TextBlock", "text": ack, "isSubtle": True, "wrap": True},
        {"type": "TextBlock", "text": f"Reason: {reason}", "isSubtle": True, "wrap": True} if reason else None,
        {"type": "TextBlock", "text": f"Comment: {comment}", "isSubtle": True, "wrap": True} if comment else None,
    ]

    body = [item for item in body if item is not None]

    return {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": body,
        "msteams": {"width": "Full"},
    }


__all__ = [
    "create_welcome_card",
    "create_magnet_response_card",
    "create_feedback_result_card",
]



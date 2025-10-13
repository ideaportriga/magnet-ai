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
                            "title": "👍 I like it",
                            "style": "positive",
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
                            "title": "👎 I do not like it",
                            "style": "destructive",
                            "targetElements": [{"elementId": "dislikeFields", "isVisible": True}],
                            "associatedInputs": "none",
                        }
                    ],
                }
            ],
        },
        {"type": "Column", "width": "stretch", "items": []},
    ]

    frontendUrl = os.getenv("MAGNET_FRONTEND_URL")
    if frontendUrl:
        columns.append(
            {
                "type": "Column",
                "width": "auto",
                "items": [
                    {
                        "type": "ActionSet",
                        "actions": [
                            {
                                "type": "Action.OpenUrl",
                                "title": "🔗 Open conversation",
                                "url": f"{frontendUrl}/#/conversation/{conversation_id}",
                            }
                        ],
                    }
                ],
            }
        )

    return {
        "$schema": "http://adaptivecards.io/schemas/adaptive-card.json",
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": [
            {"type": "TextBlock", "text": "AI Assistant Response", "weight": "Bolder", "size": "Large"},
            {"type": "TextBlock", "text": text, "wrap": True},
            {
                "type": "Container",
                "id": "dislikeFields",
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
                                "style": "positive",
                            },
                            {
                                "type": "Action.ToggleVisibility",
                                "title": "✖️ Cancel",
                                "targetElements": [{"elementId": "dislikeFields", "isVisible": False}],
                                "style": "destructive",
                                "associatedInputs": "none",
                            },
                        ],
                    },
                ],
            },
            {"type": "ColumnSet", "spacing": "Medium", "columns": columns},
        ],
        "msteams": {"width": "Full"},
    }


def create_feedback_result_card(payload):
    text = payload.get("text")
    reaction = payload.get("reaction")
    reason = payload.get("reason")
    comment = payload.get("comment")
    conversation_id = payload.get("conversation_id")

    liked = reaction == "like"
    header = "AI Assistant Response"
    ack = "You liked it 👍" if liked else "You disliked it 👎"

    maybe_conversation_link = None
    frontend_url = os.getenv("MAGNET_FRONTEND_URL")
    if conversation_id and frontend_url:
        maybe_conversation_link = {
            "type": "ActionSet",
            "actions": [
                {
                    "type": "Action.OpenUrl",
                    "title": "🔗 Open conversation",
                    "url": f"{frontend_url}/#/conversation/{conversation_id}",
                }
            ],
        }

    body = [
        {"type": "TextBlock", "text": header, "weight": "Bolder", "size": "Large"},
        {"type": "TextBlock", "text": text, "wrap": True},
        maybe_conversation_link,
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



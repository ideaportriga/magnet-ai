from enum import StrEnum

from litestar.openapi.spec import Tag


class TagNames(StrEnum):
    UserExecute = "user/execute"
    UserAgentConversations = "user/agent_conversations"
    UserAiApps = "user/ai_apps"
    UserTelemetry = "user/telemetry"
    UserUtils = "user/utils"


def get_tags() -> list[Tag]:
    tags = [
        Tag(
            name=TagNames.UserExecute,
            description="User API endpoints related to executing predefined tools, like prompt templates, retrieval tools, and RAG tools.",
        ),
        Tag(
            name=TagNames.UserAgentConversations,
            description="User API endpoints related to managing conversations between users and agents.",
        ),
        Tag(
            name=TagNames.UserAiApps,
            description="User API endpoints related to retrieving AI app configurations.",
        ),
        Tag(
            name=TagNames.UserTelemetry,
            description="User API endpoints related to tracking and recording user telemetry data, such as feedback and interactions.",
        ),
        Tag(
            name=TagNames.UserUtils,
            description="User API endpoints related to utility operations.",
        ),
    ]

    return tags

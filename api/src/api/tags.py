from enum import StrEnum

from litestar.openapi.spec import Tag


class TagNames(StrEnum):
    UserExecute = "User / Execute"
    UserAgentConversations = "User / Agent Conversations"
    UserAiApps = "User / AI Apps"
    UserTelemetry = "User / Telemetry"
    UserUtils = "User / Utils"
    UserAgentsMessages = "User / Agents Messages"


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
        Tag(
            name=TagNames.UserAgentsMessages,
            description="User API endpoints for Teams/Slack integrations.",
        ),
    ]

    return tags

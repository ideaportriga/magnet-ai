import re
from datetime import datetime
from enum import StrEnum
from typing import Generic, Literal, TypeVar, Union
from uuid import UUID, uuid4

from openai.types.chat.chat_completion_message_tool_call import (
    Function,
)
from pydantic import BaseModel, ConfigDict, Field, TypeAdapter, root_validator

from services.common.models import ConversationMessageFeedback, LlmResponseFeedback
from services.entities.types import BaseEntityMultiVariant
from utils.datetime_utils import utc_now


class AgentActionType(StrEnum):
    API = "api"
    RAG = "rag"
    RETRIEVAL = "retrieval"
    PROMPT_TEMPLATE = "prompt_template"
    MCP_TOOL = "mcp_tool"


class Metadata(BaseModel):
    modified_at: datetime
    created_at: datetime


class AgentAction(BaseModel):
    """Represents an action that an agent can perform within a topic.
    Each action maps to a specific tool and includes
    name and description which is used for LLM tool calling.
    """

    name: str
    system_name: str
    description: str | None = None
    type: AgentActionType
    display_name: str
    display_description: str | None = None
    tool_system_name: str
    tool_provider: str | None = None
    function_name: str
    function_description: str | None = None
    metadata: Metadata | None = None
    requires_confirmation: bool | None = False
    use_response_as_assistant_message: bool | None = False
    action_message_llm_description: str | None = None


class AgentTopic(BaseModel):
    """Represents a topic that an agent can handle,
    with its own system prompt part and specific tools
    """

    name: str
    system_name: str
    description: str
    instructions: str | None = None
    actions: list[AgentAction]
    metadata: Metadata | None = None


class AgentPromptTemplates(BaseModel):
    classification: str
    topic_processing: str


class PostProcessing(BaseModel):
    enabled: bool = False
    template: str | None = None


class SampleQuestions(BaseModel):
    enabled: bool = Field(default=False)
    questions: dict[str, str] = Field(default_factory=dict)

    @root_validator(pre=True)
    def check_questions(cls, values):
        questions = values.get("questions", {})
        if len(questions) > 10:
            raise ValueError("No more than 10 questions are allowed.")
        for key in questions.keys():
            if not re.match(r"^question\d+$", key):
                raise ValueError(
                    f"Invalid question name: {key}. Must be in the format 'question' followed by a number.",
                )
        return values


class AgentSettings(BaseModel):
    """Represents settings for an agent, including welcome message,
    conversation closure interval, and sample questions.
    """

    welcome_message: str | None = None
    conversation_closure_interval: str | None = None
    sample_questions: SampleQuestions = Field(default_factory=SampleQuestions)
    user_feedback: bool | None = None


class AgentVariantValue(BaseModel):
    """Editable part of Agent entity."""

    topics: list[AgentTopic]
    prompt_templates: AgentPromptTemplates
    post_processing: PostProcessing | None = None
    settings: AgentSettings | None = None

    # Temporary, since schema might be changed
    model_config = ConfigDict(extra="allow")


class Agent(BaseEntityMultiVariant[AgentVariantValue]):
    pass


class ConversationIntent(StrEnum):
    GREETING = "greeting"
    FAREWELL = "farewell"
    REQUEST_NOT_CLEAR = "request_not_clear"
    TOPIC = "topic"
    OFF_TOPIC = "off_topic"
    OTHER = "other"


# TODO - check that not used and remove
class ExecuteAgentActionResult(BaseModel):
    content: str | dict
    verbose_details: dict | None = None


class AgentActionCall(BaseModel):
    """Result of action call within a topic"""

    action: AgentAction
    request: Function
    response: ExecuteAgentActionResult


class AgentConversationRunStepType(StrEnum):
    CLASSIFICATION = "classification"
    TOPIC_COMPLETION = "topic_completion"
    TOPIC_ACTION_CALL = "topic_action_call"
    TOPIC_ACTION_CALL_USER_CONFIRMATION = "topic_action_call_user_confirmation"


class AgentConversationSelectedTopic(BaseModel):
    name: str
    system_name: str
    description: str


class AgentConversationClassification(BaseModel):
    intent: ConversationIntent
    reason: str
    assistant_message: str | None = None
    topic: str | None = None


class AgentActionCallRequest(BaseModel):
    id: str
    function_name: str
    arguments: dict
    action_type: AgentActionType
    action_system_name: str
    action_tool_system_name: str
    action_tool_provider: str | None = None
    action_display_name: str
    action_display_description: str | None = None
    requires_confirmation: bool | None = False
    use_response_as_assistant_message: bool | None = False
    action_message: str | None = None
    variables: dict[str, str] | None = None


class AgentActionCallRequestPublic(BaseModel):
    id: str
    action_message: str


class AgentActionCallConfirmation(BaseModel):
    request_id: str
    confirmed: bool
    comment: str | None = None


class AgentConversationTopicCompletion(BaseModel):
    topic: AgentConversationSelectedTopic
    assistant_message: str | None = None
    action_call_requests: list[AgentActionCallRequest] | None = None


class AgentConversationTopicAction(BaseModel):
    name: str
    system_name: str
    description: str
    type: AgentActionType
    display_name: str
    display_description: str
    tool_system_name: str
    function_name: str


class AgentActionCallResponse(BaseModel):
    content: str
    verbose_details: dict | None = None


class AgentTopicActionCall(BaseModel):
    request: AgentActionCallRequest
    response: AgentActionCallResponse


class AgentTopicActionCallConfirmationDetails(BaseModel):
    confirmations: list[AgentActionCallConfirmation]


AgentConversationRunStepDetailsType = TypeVar(
    "AgentConversationRunStepDetailsType",
    bound=BaseModel,
)


class AgentConversationRunStepBase(
    BaseModel,
    Generic[AgentConversationRunStepDetailsType],
):
    started_at: datetime
    completed_at: datetime = Field(default_factory=utc_now)
    type: AgentConversationRunStepType
    details: AgentConversationRunStepDetailsType


class AgentConversationRunStepClassification(
    AgentConversationRunStepBase[AgentConversationClassification],
):
    type: Literal[AgentConversationRunStepType.CLASSIFICATION] = (
        AgentConversationRunStepType.CLASSIFICATION
    )


class AgentConversationRunStepTopicCompletion(
    AgentConversationRunStepBase[AgentConversationTopicCompletion],
):
    type: Literal[AgentConversationRunStepType.TOPIC_COMPLETION] = (
        AgentConversationRunStepType.TOPIC_COMPLETION
    )


class AgentConversationRunStepTopicActionCall(
    AgentConversationRunStepBase[AgentTopicActionCall],
):
    type: Literal[AgentConversationRunStepType.TOPIC_ACTION_CALL] = (
        AgentConversationRunStepType.TOPIC_ACTION_CALL
    )


class AgentConversationRunStepTopicActionCallUserConfirmation(
    AgentConversationRunStepBase[AgentTopicActionCallConfirmationDetails],
):
    type: Literal[AgentConversationRunStepType.TOPIC_ACTION_CALL_USER_CONFIRMATION] = (
        AgentConversationRunStepType.TOPIC_ACTION_CALL_USER_CONFIRMATION
    )


AgentConversationRunStep = Union[
    AgentConversationRunStepClassification,
    AgentConversationRunStepTopicCompletion,
    AgentConversationRunStepTopicActionCall,
    AgentConversationRunStepTopicActionCallUserConfirmation,
]

AgentConversationRunSteps = list[AgentConversationRunStep]


AgentConversationRunStepTypeAdapter = TypeAdapter(AgentConversationRunSteps)


class AgentConversationExecuteTopicResult(BaseModel):
    content: str | None = None
    action_call_requests: list[AgentActionCallRequestPublic] | None = None
    steps: AgentConversationRunSteps


class AgentConversationMessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"


class AgentConversationMessageBase(BaseModel):
    id: UUID
    created_at: datetime = Field(default_factory=utc_now)
    role: AgentConversationMessageRole
    content: str | None = None


class AgentConversationMessageUser(AgentConversationMessageBase):
    role: Literal[AgentConversationMessageRole.USER] = AgentConversationMessageRole.USER
    action_call_confirmations: list[AgentActionCallConfirmation] | None = None


class AgentConversationRun(BaseModel):
    steps: AgentConversationRunSteps


class AgentConversationMessageAssistant(AgentConversationMessageBase):
    role: Literal[AgentConversationMessageRole.ASSISTANT] = (
        AgentConversationMessageRole.ASSISTANT
    )
    action_call_requests: list[AgentActionCallRequestPublic] | None = None
    run: AgentConversationRun | None = None
    feedback: LlmResponseFeedback | None = None
    topic: str | None = None
    copied: bool | None = False
    custom_feedback: ConversationMessageFeedback | None = None


AgentConversationMessage = Union[
    AgentConversationMessageUser,
    AgentConversationMessageAssistant,
]


class AgentTest(BaseModel):
    name: str | None = None
    agent_config: AgentVariantValue
    messages: list[AgentConversationMessage]
    variables: dict[str, str] | None = Field(
        None,
        description="Additional conversational variables that could be used for api tool invocation.",
        examples=[{"user_id": "SADMIN"}],
    )


class AgentExecute(BaseModel):
    agent_system_name: str
    messages: list[AgentConversationMessage]
    variables: dict[str, str] | None = Field(
        None,
        description="Additional conversational variables that could be used for api tool invocation.",
        examples=[{"user_id": "SADMIN"}],
    )


class AgentConversationData(BaseModel):
    id: UUID | None = None
    agent: str
    created_at: datetime
    last_user_message_at: datetime
    client_id: str | None = None
    trace_id: str | None = None
    analytics_id: str | None = None
    variables: dict[str, str] | None = None


class AgentConversationDataWithMessages(AgentConversationData):
    messages: list[AgentConversationMessage]


AgentConversationMessageFeedbackRequest = LlmResponseFeedback


class AgentConversationMessagePublicBase(BaseModel):
    id: UUID
    role: AgentConversationMessageRole
    content: str | None = None
    created_at: datetime = Field(default_factory=utc_now)


class AgentConversationMessageUserPublic(AgentConversationMessagePublicBase):
    role: Literal[AgentConversationMessageRole.USER] = AgentConversationMessageRole.USER

    action_call_confirmations: list[AgentActionCallConfirmation] | None = Field(
        default=None,
        description="The list of action call confirmations. Applicable to user messages.",
        examples=[
            [
                AgentActionCallConfirmation(
                    request_id="1",
                    confirmed=True,
                ),
                AgentActionCallConfirmation(
                    request_id="2",
                    confirmed=False,
                ),
            ],
        ],
    )


class AgentConversationMessageAssistantPublic(AgentConversationMessagePublicBase):
    role: Literal[AgentConversationMessageRole.ASSISTANT] = (
        AgentConversationMessageRole.ASSISTANT
    )

    feedback: LlmResponseFeedback | None = None
    action_call_requests: list[AgentActionCallRequestPublic] | None = Field(
        default=None,
        description="The list of action call requests to be confirmed. Applicable to assistant messages.",
        examples=[
            [
                AgentActionCallRequestPublic(
                    id="1",
                    action_message="Retrieve information of contact with id '1'",
                ),
                AgentActionCallRequestPublic(
                    id="2",
                    action_message="Search the knowledge base for 'search term'",
                ),
            ],
        ],
    )


AgentConversationMessagePublic = (
    AgentConversationMessageUserPublic | AgentConversationMessageAssistantPublic
)


class AgentConversationWithMessages(BaseModel):
    id: str = Field(..., description="The unique identifier of the conversation.")
    messages: list[AgentConversationMessage] = Field(
        ...,
        description="The list of messages in the conversation.",
    )
    agent: str = Field(
        ...,
        description="The system name of the agent.",
        examples=["FAQ_ASSISTANT"],
    )
    created_at: datetime = Field(
        ...,
        description="The timestamp when the conversation was created.",
    )
    last_user_message_at: datetime = Field(
        ...,
        description="The timestamp of the last user message.",
    )
    client_id: str | None = Field(
        None,
        description="An optional client-side identifier, set when creating a new agent conversation.",
        examples=["user123_tab456_agent_789"],
    )
    status: str | None = Field(
        None,
        description="The status of the conversation.",
        examples=["active", "closed"],
    )
    trace_id: str | None = Field(
        default=None,
        description="The trace ID of the conversation.",
    )
    analytics_id: str | None = Field(
        default=None,
        description="The analytics ID of the conversation.",
    )


class AgentConversationWithMessagesPublic(BaseModel):
    id: UUID = Field(..., description="The unique identifier of the conversation.")
    messages: list[AgentConversationMessagePublic] = Field(
        ...,
        description="The list of messages in the conversation.",
        examples=[
            [
                AgentConversationMessageUserPublic(
                    id=uuid4(),
                    content="How to ...?",
                    created_at=utc_now(),
                ),
                AgentConversationMessageAssistantPublic(
                    id=uuid4(),
                    created_at=utc_now(),
                    action_call_requests=[
                        AgentActionCallRequestPublic(
                            id="1",
                            action_message="Retrieve information of contact with id '1'",
                        ),
                    ],
                ),
                AgentConversationMessageUserPublic(
                    id=uuid4(),
                    created_at=utc_now(),
                    action_call_confirmations=[
                        AgentActionCallConfirmation(
                            request_id="1",
                            confirmed=True,
                        ),
                    ],
                ),
                AgentConversationMessageAssistantPublic(
                    id=uuid4(),
                    role=AgentConversationMessageRole.ASSISTANT,
                    content="You can ...",
                    created_at=utc_now(),
                    action_call_requests=[
                        AgentActionCallRequestPublic(
                            id="2",
                            action_message="Search the knowledge base for 'search term'",
                        ),
                    ],
                ),
            ],
        ],
    )
    agent: str = Field(
        ...,
        description="The system name of the agent.",
        examples=["FAQ_ASSISTANT"],
    )

    created_at: datetime = Field(
        ...,
        description="The timestamp when the conversation was created.",
    )
    last_user_message_at: datetime = Field(
        ...,
        description="The timestamp of the last user message.",
    )
    client_id: str | None = Field(
        default=None,
        description="An optional client-side identifier, set when creating a new agent conversation.",
        examples=["user123_tab456_agent_789"],
    )
    trace_id: str | None = Field(
        default=None,
        description="The trace ID of the conversation.",
    )
    analytics_id: str | None = Field(
        default=None,
        description="The analytics ID of the conversation.",
    )

    class Config:
        title = "AgentConversationWithMessagesPublic"
        description = "Response body for retrieving a conversation with its messages."


class AgentConversationCreateRequest(BaseModel):
    agent: str = Field(..., description="The system name of the agent.")
    user_message_content: str = Field(
        ...,
        description="The content of the user's initial message.",
        examples=["How to ...?"],
    )
    client_id: str | None = Field(
        None,
        description="An optional client-side identifier (e.g., tab_id + user_id + agent_id) to retrieve active conversation without storing conversation ID in the client system.",
        examples=["user123_tab456_agent_789"],
    )
    variables: dict[str, str] | None = Field(
        None,
        description="Additional variables for conversation.",
        examples=[{"user_id": "SADMIN"}],
    )

    class Config:
        title = "AgentConversationCreateRequest"
        description = "Request body for creating a new conversation with an agent."


class AgentConversationAddUserMessageRequest(BaseModel):
    user_message_content: str | None = Field(
        None,
        description="The content of the user's message.",
        examples=["How to ...?"],
    )
    action_call_confirmations: list[AgentActionCallConfirmation] | None = Field(
        None,
        description="The list of action call confirmations. Should be provided if action call confirmation is awaited. If provided - `user_message_content` should be empty.",
        examples=[
            [
                AgentActionCallConfirmation(
                    request_id="1",
                    confirmed=True,
                ),
                AgentActionCallConfirmation(
                    request_id="2",
                    confirmed=False,
                ),
            ],
        ],
    )


class AgentConversationAddUserMessageResponse(BaseModel):
    user_message: AgentConversationMessageUserPublic | None = None
    assistant_message: AgentConversationMessageAssistantPublic
    trace_id: str | None = None
    analytics_id: str | None = None

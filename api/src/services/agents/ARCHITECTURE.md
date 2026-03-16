# Agent System — Architecture

> Description of the modular architecture of agent code after refactoring.
> Date: March 2026.

---

## Overview

The agent system processes user messages through a three-stage pipeline:

```
User Message
     │
     ▼
┌─────────────────┐
│  Classification  │  — intent detection + topic selection
└────────┬────────┘
         │ intent = "topic"
         ▼
┌─────────────────┐
│ Topic Execution  │  — LLM ↔ Actions loop (up to 5 iterations)
└────────┬────────┘
         │
         ▼
  Assistant Message
```

If intent ≠ `topic` (greeting, farewell, off_topic, request_not_clear, other), the topic processing loop is skipped and `assistant_message` from classification is returned immediately.

---

## Module Structure

```
services/agents/
├── __init__.py              # Public API: execute_agent, get_agent_by_system_name
├── services.py              # Orchestrator (241 lines)
├── classification.py        # Intent and topic classification (178 lines)
├── topic_execution.py       # Main agent loop (343 lines)
├── confirmation.py          # User confirmation handling (75 lines)
├── tool_schema.py           # ChatCompletionTool generation from actions (394 lines)
├── message_builder.py       # History → ChatCompletion messages conversion (126 lines)
├── memory.py                # Context management strategies (43 lines)
├── exceptions.py            # Custom exception hierarchy (33 lines)
├── models.py                # Pydantic data models (614 lines)
│
├── actions/
│   ├── execute.py                       # Action → executor router (86 lines)
│   ├── action_execute_api_tool.py       # API action executor
│   ├── action_execute_rag.py            # RAG action executor
│   ├── action_execute_retrieval.py      # Retrieval action executor
│   ├── action_execute_prompt_template.py# Prompt Template action executor
│   ├── action_execute_mcp_tool.py       # MCP Tool action executor
│   └── action_execute_knowledge_graph.py# Knowledge Graph action executor
│
├── conversations/           # CRUD for conversations (separate subsystem)
├── post_process/            # Response post-processing
├── slack/                   # Slack integration
├── teams/                   # Teams integration
├── whatsapp/                # WhatsApp integration
└── utils/                   # Helper utilities
```

---

## Module Descriptions

### `services.py` — Orchestrator

Entry point. Contains the `execute_agent()` function, which:

1. Loads agent configuration (from DB or `config_override`)
2. Determines the current request type:
   - **Confirmation flow** — user confirms/rejects an action call → delegates to `confirmation.py`
   - **PASS mode** — experimental: skips classification, takes the first topic
   - **Normal flow** — delegates classification to `classification.py`
3. Runs `execute_topic()` from `topic_execution.py`
4. Assembles the final `AgentConversationMessageAssistant`

Also contains `get_agent_by_system_name()` for loading an agent from the DB.

All functions from submodules are **re-exported** through `services.py` for backwards compatibility — external code can continue importing from `services.agents.services`.

### `classification.py` — Classification

The `classify_conversation()` function:

- Calls LLM via prompt template to determine intent and topic
- **3 retries** with parse error injection into retry context
- Handles LLM JSON hallucinations: trailing commas, `//` comments, markdown code fences
- Validation: if intent = "topic", checks that the topic exists
- **Graceful fallback**: returns `REQUEST_NOT_CLEAR` instead of crashing when retries are exhausted

Helper function `_extract_json_string()` — extracts JSON from arbitrary LLM responses.

### `topic_execution.py` — Main Loop

The `execute_topic()` function:

```
while iteration < MAX_ITERATIONS (5):
    1. Collect context messages (via MemoryStrategy)
    2. Call LLM with tools
    3. If there are tool calls with requires_confirmation → return for confirmation
    4. If there is an assistant_message → return result
    5. If there are tool calls → execute actions → add to steps → next iteration
```

Protective mechanisms:
- **Topic-level timeout**: `AGENT_TOPIC_TIMEOUT_SECONDS` (default 120s, via env)
- **Action-level timeout**: `AGENT_ACTION_TIMEOUT_SECONDS` (default 30s, via env)
- **Sanitized errors**: internal action errors do not leak into the user response
- **Graceful degradation**: when iterations are exhausted, returns the last available `assistant_message` instead of an exception

Also contains `create_action_call_requests()` — parses tool calls from LLM response into `AgentActionCallRequest`.

### `confirmation.py` — Action Confirmation

The `create_action_call_steps()` function:

- Accepts a list of action requests + user confirmations
- For confirmed — executes the action
- For rejected — returns a rejection message
- Execution errors are sanitized via `_sanitize_action_error()`

### `tool_schema.py` — Tool Schema Generation

Converts `AgentAction` → `ChatCompletionToolParam` for the OpenAI API:

| Action Type       | Parameter source                                 |
|-------------------|--------------------------------------------------|
| `API`             | ApiServer → tool → `parameters.input`            |
| `MCP_TOOL`        | MCPServer → tool → `inputSchema`                 |
| `RAG`             | Metadata fields from RAG tool collections        |
| `RETRIEVAL`       | Metadata fields from Retrieval tool collections  |
| `PROMPT_TEMPLATE` | Fixed schema `{userMessage: string}`             |
| `KNOWLEDGE_GRAPH` | From `get_agent_tool_specs()` or fallback schema |

For actions with `requires_confirmation` adds the `_magnetActionMessage` parameter.

### `message_builder.py` — Message Building

The `generate_completion_messages()` function:

- Converts `AgentConversationMessage[]` → `ChatCompletionMessageParam[]`
- Handles all step types: classification, topic_completion, topic_action_call
- `max_messages` parameter for context truncation

The `create_tool_calls_from_topic_completion_step()` function:

- Converts action requests from a step → `ChatCompletionMessageToolCallParam[]`

### `memory.py` — Memory Strategies

The `MemoryStrategy` protocol and `LastNMessagesStrategy` implementation:

```python
class MemoryStrategy(Protocol):
    def select_messages(self, messages: list[AgentConversationMessage]) -> list[AgentConversationMessage]: ...

class LastNMessagesStrategy:
    def __init__(self, n: int = 10): ...
```

Default `n=10` (`DEFAULT_LAST_N_MESSAGES`). Strategy is wired in `execute_topic()`.

### `exceptions.py` — Exception Hierarchy

```
AgentError (base)
├── AgentNotFoundError         — agent not found
├── AgentConfigurationError    — invalid configuration
├── ClassificationError        — classification error
├── ActionExecutionError       — action execution error
├── AgentLoopExhaustedError    — loop exhausted without result
└── AgentTimeoutError          — topic execution timeout
```

### `models.py` — Data Models

Key models:

| Model                              | Purpose                                           |
|------------------------------------|---------------------------------------------------|
| `Agent`                            | Agent configuration (multi-variant entity)        |
| `AgentTopic`                       | Topic with description and list of actions        |
| `AgentAction`                      | Action description (type, tool, function name...) |
| `ConversationIntent`               | Enum: greeting, farewell, topic, off_topic, ...   |
| `AgentConversationClassification`  | Classification result (intent + topic + reason)   |
| `AgentConversationRun`             | Set of steps from a single agent run              |
| `AgentConversationRunStep*`        | Typed steps: Classification, TopicCompletion, ActionCall |
| `AgentConversationExecuteTopicResult` | Result of execute_topic                        |
| `AgentVariantValue`                | Configuration variant: topics + prompt_templates  |
| `AgentSettings`                    | Settings: welcome_message, sample_questions, ...  |

### `actions/execute.py` — Action Router

Mapping `AgentActionType` → executor function:

```python
# Simple actions (tool_system_name + arguments)
EXECUTE_AGENT_ACTION_FUNCTION_MAP = {
    RAG:             action_execute_rag,
    RETRIEVAL:       action_execute_retrieval,
    PROMPT_TEMPLATE: action_execute_prompt_template,
}

# Actions with provider (tool_provider + tool_system_name + arguments)
EXECUTE_AGENT_PROVIDED_ACTION_FUNCTION_MAP = {
    MCP_TOOL:        action_execute_mcp_tool,
    API:             action_execute_api_tool,
    KNOWLEDGE_GRAPH: action_execute_knowledge_graph,
}
```

---

## Environment Variable Configuration

| Variable                           | Default   | Description                                     |
|------------------------------------|-----------|-------------------------------------------------|
| `AGENT_TOPIC_TIMEOUT_SECONDS`      | `120`     | Timeout for the entire execute_topic loop       |
| `AGENT_ACTION_TIMEOUT_SECONDS`     | `30`      | Timeout for a single action execution           |
| `ACTION_MESSAGE_DEFAULT_LLM_DESCRIPTION` | (built-in) | LLM instruction for `_magnetActionMessage` |

---

## Data Flows

### Main flow

```
execute_agent()                              [services.py]
  │
  ├─ get_agent_by_system_name()              [services.py]  — load from DB
  │
  ├─ classify_conversation()                 [classification.py]
  │    ├─ execute_prompt_template()           — call LLM
  │    ├─ _extract_json_string()              — parse response
  │    └─ AgentConversationClassification     — result
  │
  └─ execute_topic()                         [topic_execution.py]
       ├─ LastNMessagesStrategy.select_messages()  [memory.py]
       ├─ generate_completion_messages()            [message_builder.py]
       ├─ create_chat_completion_tools()            [tool_schema.py]
       ├─ create_chat_completion_from_prompt_template()  — call LLM
       ├─ create_action_call_requests()             [topic_execution.py]
       └─ execute_agent_action()                    [actions/execute.py]
            └─ action_execute_*()                   [actions/action_execute_*.py]
```

### Confirmation flow

```
execute_agent()                              [services.py]
  │
  └─ create_action_call_steps()              [confirmation.py]
       └─ execute_agent_action()             [actions/execute.py]
```

---

## Principles

1. **Single responsibility** — each module is responsible for one task
2. **Graceful degradation** — the system prefers to return an incomplete response rather than crash
3. **Sanitized errors** — internal errors and tracebacks do not reach the user
4. **Explicit exceptions** — custom hierarchy instead of `assert` / generic `ValueError`
5. **Pluggable memory** — context strategy is replaceable via Protocol
6. **Backwards compatibility** — all public symbols are re-exported from `services.py`

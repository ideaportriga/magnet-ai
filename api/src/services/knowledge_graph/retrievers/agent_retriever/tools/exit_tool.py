"""
Pseudo tool: `exit`.

The retrieval agent uses OpenAI tool-calls (ReAct style). This "tool" is a structured
way for the model to signal that it is done and provide the final answer payload.

There is intentionally **no generic server-side dispatcher** for `exit`.
Instead:
- The agent loop (`agent.py`) intercepts the OpenAI tool call named `"exit"`.
- The helper function `exit_tool(...)` (defined below) records a small observability
  span ("Exit from loop") and returns the answer string.
"""

from typing import Any

from services.observability import observability_context, observe

# OpenAI tool schema (sent to the LLM).
TOOL_SPEC: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "exit",
        "description": "Exit the tool call loop",
        "parameters": {
            "type": "object",
            "properties": {
                "reasoning": {
                    "type": "string",
                    "description": "Confidence assessment and why you are ready to answer.",
                },
                "answer": {
                    "type": "string",
                    "description": (
                        "The complete final answer with citations. "
                        "Format: Blockquote with source, followed by ."
                    ),
                },
            },
            "required": ["reasoning", "answer"],
        },
    },
}


@observe(name="Exit from loop")
def exit_tool(answer: str, reasoning: str) -> str:
    """
    Finalize the agentic loop.

    This is called **by server code** (not by OpenAI) after the model tool-calls `"exit"`.
    We store the model-provided reasoning as the observability span description, which
    helps debugging why the model decided it was done.
    """

    observability_context.update_current_span(description=reasoning)
    return answer

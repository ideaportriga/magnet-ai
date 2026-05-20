"""AI-assisted entity editing — see ``docs/AI_ENTITY_EDITING_PLAN.md`` Part B.

The endpoint takes a free-form instruction from the user, sends the
current entity state + a flattened JSON Schema to an LLM, and returns
the proposed new state. **Nothing is persisted to the entity table by
this service** — the UI puts the result into the editBuffer.draft and
the user saves it with a regular PATCH.
"""

from .models import (
    AIEditFailure,
    AIEditResult,
    AIEditStatus,
    AIEditUsage,
)
from .registry import (
    AIEditableDescriptor,
    get_ai_editable,
    register_ai_editable,
)
from .service import ai_edit_entity

__all__ = [
    "AIEditFailure",
    "AIEditResult",
    "AIEditStatus",
    "AIEditUsage",
    "AIEditableDescriptor",
    "ai_edit_entity",
    "get_ai_editable",
    "register_ai_editable",
]

from dataclasses import dataclass, field

from typing import Dict, Set, Tuple


@dataclass(slots=True)
class WhatsappRuntime:
    phone_number_id: str
    agent_system_name: str
    token: str
    app_secret: str
    # TODO: save it in database?
    handled_interactive_message_ids: Set[str] = field(default_factory=set)
    feedback_context: Dict[str, Tuple[str | None, str | None]] = field(default_factory=dict)

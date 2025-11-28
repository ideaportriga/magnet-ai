from dataclasses import dataclass, field

from typing import Dict, Set


@dataclass(slots=True)
class WhatsappRuntime:
    phone_number_id: str
    agent_system_name: str
    token: str
    app_secret: str
    handled_interactive_message_ids: Set[str] = field(default_factory=set)
    interactive_context: Dict[str, dict] = field(default_factory=dict)

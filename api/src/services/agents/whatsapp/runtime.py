from dataclasses import dataclass


@dataclass(slots=True)
class WhatsappRuntime:
    phone_number_id: str
    agent_system_name: str
    token: str
    app_secret: str

"""AI Model factories."""

from __future__ import annotations

import factory

from core.db.models.ai_model import AIModel

from .base import BaseFactory


class AIModelFactory(BaseFactory):
    class Meta:
        model = AIModel

    name = factory.Sequence(lambda n: f"AI Model {n}")
    system_name = factory.Sequence(lambda n: f"ai-model-{n}")
    provider_name = "openai"
    ai_model = "gpt-4o"
    display_name = factory.LazyAttribute(lambda o: o.name)
    type = "chat"
    is_active = True
    is_default = False
    json_mode = False
    json_schema = False
    tool_calling = True
    reasoning = False
    diarization = False

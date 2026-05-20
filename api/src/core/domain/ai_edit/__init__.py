"""AI entity editor domain — POST /admin/ai-edit + history endpoints."""

from .controller import AIEditController
from .registrations import register_default_ai_editables

# Side-effect: populate the AI-edit registry on package import. Keeps
# the controller decoupled from concrete model imports while still
# guaranteeing the registry is populated before the route fires.
register_default_ai_editables()

__all__ = ["AIEditController"]

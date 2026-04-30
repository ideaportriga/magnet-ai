"""Compatibility shim — Confluence integration moved to services.integrations.

The implementation lives at `services.integrations.confluence.note_taker`.
Existing callers in this package (note_taker_transcription.py) keep working
through this re-export; new callers should import from the integrations
namespace directly.
"""

from services.integrations.confluence.note_taker import *  # noqa: F401,F403
from services.integrations.confluence.note_taker import (  # noqa: F401
    maybe_publish_confluence_notes,
)

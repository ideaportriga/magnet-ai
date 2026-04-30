"""Compatibility shim — Salesforce integration moved to services.integrations.

The implementation lives at `services.integrations.salesforce.note_taker`.
Existing callers in this package (note_taker.py, note_taker_handlers/state.py)
keep working through this re-export; new callers should import from the
integrations namespace directly.
"""

from services.integrations.salesforce.note_taker import *  # noqa: F401,F403
from services.integrations.salesforce.note_taker import (  # noqa: F401
    account_lookup,
    config_requires_salesforce,
    get_salesforce_api_server,
    get_salesforce_stt_recording_tool,
    pick_first_account_id_and_name,
    post_stt_recording,
    send_stt_recording_to_salesforce,
    update_meeting_salesforce_account,
)

"""Teams agent package.

Importing this package eagerly registers Teams-specific post-consume hooks
with the generic ``account_link`` service, so the binding flow works
correctly even if no ``/link`` has been issued in this process lifetime
before the first ``POST /api/me/account-link/{code}/confirm``.
"""

# Side-effect import: registers the "teams" channel_kind post-consume hook.
from . import teams_link_post_consume  # noqa: F401

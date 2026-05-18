"""Mixin classes that compose `NoteTakerHandlerState`.

The handler class started as a single 2241-line god-class in `state.py`.
Splitting by responsibility into mixins keeps the call-sites unchanged
(Python MRO surfaces every method as if it lived on the main class)
while giving each topic its own readable file. See
`NOTE_TAKER_REVISION_PLAN.md` §3.2 P1-a.

Each mixin assumes its concrete class provides:

* ``self.deps`` — :class:`NoteTakerHandlerDeps`
* ``self._logger`` — module logger

Mixins are stateless beyond those two attributes; they MUST NOT add
__init__ or instance state of their own.
"""

from .auth import AuthMixin
from .config_card import ConfigCardMixin
from .meeting_info import MeetingInfoMixin
from .recordings import RecordingsMixin

__all__ = [
    "AuthMixin",
    "ConfigCardMixin",
    "MeetingInfoMixin",
    "RecordingsMixin",
]

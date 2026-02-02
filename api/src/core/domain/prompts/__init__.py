"""
Prompts domain package.

Important: keep this module *light*.

Some runtime components (e.g. `prompt_templates.prompt_templates`) import
`core.domain.prompts.schemas`. Importing a submodule requires importing the
package first (this file). If we eagerly import the controller here, we can
create circular imports during app startup:

`prompt_templates -> core.domain.prompts.schemas -> (imports package __init__) ->
 core.domain.prompts.controller -> prompt_templates`

To avoid that, we expose `PromptsController` via a lazy `__getattr__` hook.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .schemas import Prompt, PromptCreate, PromptUpdate
from .service import PromptsService

if TYPE_CHECKING:  # pragma: no cover
    # For type checkers only; do not import at runtime to avoid cycles.
    from .controller import PromptsController as PromptsController  # noqa: F401


def __getattr__(name: str):  # noqa: ANN001
    if name == "PromptsController":
        from .controller import PromptsController  # local import avoids cycle

        return PromptsController
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = [
    "PromptsController",
    "Prompt",
    "PromptCreate",
    "PromptUpdate",
    "PromptsService",
]

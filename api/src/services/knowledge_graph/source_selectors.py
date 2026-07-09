"""Shared source-selector semantics used by content profiles and entity extraction.

A "source selector" is a list of tokens describing which knowledge-graph sources a
piece of configuration applies to. The list may contain any mix of:

- ``__ALL__`` (or an empty list) -> any source
- ``__GROUP__<type>`` (e.g. ``__GROUP__sharepoint``) -> any source of that type
- a concrete source id -> that specific source
- ``__NONE__`` -> explicit match-nothing
"""

ALL_SOURCES_KEY = "__ALL__"
NONE_SELECTED_KEY = "__NONE__"
GROUP_KEY_PREFIX = "__GROUP__"


def _parse_group_selector(selector: str) -> str | None:
    if selector.startswith(GROUP_KEY_PREFIX):
        return selector[len(GROUP_KEY_PREFIX) :]
    return None


def matches_source_selector(
    selectors: list[str], source_id: str | None, source_type: str | None
) -> bool:
    """Return whether a stored selector list matches the current source.

    Selectors can contain:
    - concrete source ids
    - ``__GROUP__<type>`` virtual group selectors
    - ``__ALL__`` wildcard selector
    - ``__NONE__`` explicit match-nothing selector
    """

    if not selectors:
        return True

    normalized_selectors = {str(selector) for selector in selectors if selector}
    if not normalized_selectors:
        return True

    if NONE_SELECTED_KEY in normalized_selectors:
        return False

    if ALL_SOURCES_KEY in normalized_selectors:
        return True

    normalized_source_id = str(source_id) if source_id else None
    if normalized_source_id and normalized_source_id in normalized_selectors:
        return True

    normalized_source_type = str(source_type) if source_type else None
    if not normalized_source_type:
        return False

    return any(
        _parse_group_selector(selector) == normalized_source_type
        for selector in normalized_selectors
    )

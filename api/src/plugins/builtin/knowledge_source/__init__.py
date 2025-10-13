"""Built-in Knowledge Source Plugins

This package contains knowledge source plugins that are shipped with Magnet AI.
"""

# Import all plugins to trigger auto-registration
from . import (
    confluence,
    documentation,
    file,
    fluidtopics,
    hubspot,
    oracle_knowledge,
    rightnow,
    salesforce,
    sharepoint,
    sharepoint_pages,
)

__all__ = [
    "confluence",
    "documentation",
    "file",
    "fluidtopics",
    "hubspot",
    "oracle_knowledge",
    "rightnow",
    "salesforce",
    "sharepoint",
    "sharepoint_pages",
]

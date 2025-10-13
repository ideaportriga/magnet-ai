"""Built-in Knowledge Source Plugins

This package contains knowledge source plugins that are shipped with Magnet AI.
"""

# Import all plugins to trigger auto-registration
from . import (
    confluence,
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
    "file",
    "fluidtopics",
    "hubspot",
    "oracle_knowledge",
    "rightnow",
    "salesforce",
    "sharepoint",
    "sharepoint_pages",
]

"""SharePoint -> Knowledge Graph source.

This package mirrors the structure used by `fluid_topics`:
- models: dataclasses for run config and pipeline tasks
- utils: SharePoint auth + file listing + file download helpers
- sync: pipeline implementation
- source: Knowledge Graph source entrypoint
"""

from .sharepoint_source import SharePointDataSource

__all__ = [
    "SharePointDataSource",
]

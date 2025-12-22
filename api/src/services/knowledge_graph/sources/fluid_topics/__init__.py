"""Fluid Topics -> Knowledge Graph source.

This module implements synchronization of Fluid Topics into the Knowledge Graph storage model.

Fluid Topics search results can include both:
- native Fluid Topics content (TOPIC entries grouped into maps)
- file-based documents (DOCUMENT entries, often PDFs)

Key modeling decisions:
- A Fluid Topics *map* is treated as a **Knowledge Graph document**.
- A Fluid Topics *topic content* is treated as a **Knowledge Graph chunk** inside that map document.
- A Fluid Topics *DOCUMENT* entry is treated as a **Knowledge Graph document** and ingested via the
  standard file extraction + chunking pipeline.

This matches how Fluid Topics structures knowledge: many topic blocks belong to a single map,
and Fluid Topics already provides meaningful chunk boundaries for topic content (no splitting required).
"""

from .fluid_topics_source import FluidTopicsSource

__all__ = [
    "FluidTopicsSource",
]

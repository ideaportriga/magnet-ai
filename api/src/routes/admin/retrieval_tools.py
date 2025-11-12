"""
DEPRECATED: This file is deprecated and kept for backward compatibility.
Use core.domain.retrieval_tools.controller.RetrievalToolsController instead.
"""

from core.domain.retrieval_tools.controller import RetrievalToolsController as RetrievalToolsControllerBase


class RetrievalToolsController(RetrievalToolsControllerBase):
    """Retrieval Tools controller with admin-specific path for backward compatibility."""

    path = "/retrieval_tools"
    tags = ["retrieval_tools"]


class RetrievalToolsControllerDeprecated(RetrievalToolsControllerBase):
    """Deprecated retrieval path for backward compatibility."""
    
    path = "/retrieval"
    tags = ["retrieval_deprecated"]


__all__ = ["RetrievalToolsController", "RetrievalToolsControllerDeprecated"]

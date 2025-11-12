"""Plugin Types Enumeration

Defines all available plugin types in the Magnet AI system.
"""

from enum import StrEnum


class PluginType(StrEnum):
    """Available plugin types in the system"""

    # Data Source Plugins
    KNOWLEDGE_SOURCE = "knowledge_source"

    # Future plugin types (ready for expansion)
    DATA_PROCESSOR = "data_processor"
    STORAGE_BACKEND = "storage_backend"
    LLM_PROVIDER = "llm_provider"

"""External Plugins

This directory contains CLIENT-SPECIFIC plugins organized by type.
These plugins should be moved to separate private repositories before publishing to GitHub.

Structure:
- knowledge_source/ - Data source integrations (Salesforce, Oracle, etc.)
- llm_provider/ - LLM providers (future)
- authentication/ - Auth methods (future)
- etc.

External plugins can be:
1. Kept here for development (excluded from git via .gitignore)
2. Moved to separate packages: pip install magnet-plugins-<name>
3. Loaded via: MAGNET_PLUGINS=magnet_plugins.salesforce
"""

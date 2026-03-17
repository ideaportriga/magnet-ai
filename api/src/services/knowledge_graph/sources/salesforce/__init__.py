"""Salesforce Knowledge Articles -> Knowledge Graph source.

This module implements synchronization of Salesforce Knowledge Base articles
(Knowledge Article View objects) into the Knowledge Graph storage model.

Key design decisions:
- Credentials are resolved from a referenced Knowledge Source provider record
  (``source.config['ks_provider_id']``), keeping credentials out of source config.
- A single SOQL ``query_all`` call fetches all published articles; no pagination
  is needed in userland because ``simple_salesforce`` handles it internally.
- Article content is produced by rendering a user-supplied ``output_config`` template
  with the article's field values, e.g. ``"{Summary}"``.
- Partial sync is implemented via SHA-256 content hashing: unchanged articles are
  skipped, only metadata is updated.
- Deleted articles are cleaned up after each sync via orphaned-document detection.
"""

from .salesforce_source import SalesforceSource

__all__ = [
    "SalesforceSource",
]

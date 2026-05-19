"""Marker mixin for SQLAlchemy models that should be audited.

Models tagged with ``Auditable`` are picked up by the audit listener
(see ``listener.py``) which emits one row in ``entity_audit_log`` for
every create / update / delete that happens through the ORM.

Usage:

    class Agent(UUIDAuditEntityBase, Auditable):
        __audit_entity_type__ = "agent"
        __audit_secret_fields__ = {"secrets_encrypted"}  # masked in snapshots

The mixin itself adds nothing to the table — it's a marker class plus a
small contract. Subclasses MUST set ``__audit_entity_type__`` to a stable
slug used in the ``entity_type`` column.
"""

from __future__ import annotations

from typing import ClassVar


class Auditable:
    """Marks a SQLAlchemy model for automatic audit-log tracking."""

    # Stable slug stored in entity_audit_log.entity_type. MUST be set
    # by subclasses; an empty value disables audit for the subclass
    # (loud failure in the listener).
    __audit_entity_type__: ClassVar[str] = ""

    # Columns whose values must NEVER be written to the audit snapshot
    # (encrypted secrets, raw passwords, etc.). Keys are preserved with
    # empty-string values so callers can still see "field changed".
    __audit_secret_fields__: ClassVar[frozenset[str]] = frozenset()

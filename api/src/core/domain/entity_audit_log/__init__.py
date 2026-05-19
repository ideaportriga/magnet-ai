"""Entity audit log domain — history & restore endpoints."""

from .controller import EntityAuditLogController
from .registrations import register_default_auditable_entities

# Side-effect: populate the audit registry so the restore endpoint
# knows how to write back to each entity type.
register_default_auditable_entities()

__all__ = ["EntityAuditLogController"]

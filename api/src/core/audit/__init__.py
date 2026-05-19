"""Entity audit trail — see ``docs/AI_ENTITY_EDITING_PLAN.md`` Part A."""

from .context import (
    ActorType,
    AuditContext,
    AuditSource,
    audit_context_scope,
    current_audit_context,
    reset_audit_context,
    set_audit_context,
    system_audit_context,
)
from .listener import install_audit_listener
from .mixin import Auditable
from .registry import (
    EntityAuditDescriptor,
    auditable_types,
    get_descriptor,
    register_auditable,
)

__all__ = [
    "ActorType",
    "AuditContext",
    "AuditSource",
    "Auditable",
    "EntityAuditDescriptor",
    "auditable_types",
    "get_descriptor",
    "register_auditable",
    "install_audit_listener",
    "audit_context_scope",
    "current_audit_context",
    "reset_audit_context",
    "set_audit_context",
    "system_audit_context",
]

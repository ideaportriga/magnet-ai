"""Access-control service helpers (audit log writer, validation utilities)."""

from .audit import write_audit_log
from .permissions import PermissionService, record_visibility_filter
from .record_level import (
    attach_permissions,
    create_with_record_context,
    delete_with_record_access,
    enforce_action_or_403,
    enforce_view_or_404,
    force_create_fields,
    get_by_code_with_record_access,
    get_by_id_with_record_access,
    list_with_record_permissions,
    serialize_with_permissions,
    strip_identity_fields,
    tenant_system_name_filter,
    update_with_record_access,
    visibility_filter_for,
)

__all__ = [
    "PermissionService",
    "attach_permissions",
    "create_with_record_context",
    "delete_with_record_access",
    "enforce_action_or_403",
    "enforce_view_or_404",
    "force_create_fields",
    "get_by_code_with_record_access",
    "get_by_id_with_record_access",
    "list_with_record_permissions",
    "record_visibility_filter",
    "serialize_with_permissions",
    "strip_identity_fields",
    "tenant_system_name_filter",
    "update_with_record_access",
    "visibility_filter_for",
    "write_audit_log",
]

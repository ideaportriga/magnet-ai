"""
Tenant table — represents an organization-tenant (Magnet AI customer).

This is OUR multi-tenancy layer — distinct from any Azure/Microsoft tenant
ids (those are `azure_tenant_id` after PR 3). Domain tables get a
`tenant_id` FK in later PRs (PR 7–10+); roles, users and API keys get it
in this PR.
"""

from __future__ import annotations

from advanced_alchemy.base import UUIDv7AuditBase
from sqlalchemy import Boolean, String
from sqlalchemy.orm import Mapped, mapped_column


class Tenant(UUIDv7AuditBase):
    """An organization-tenant."""

    __tablename__ = "tenant"
    __table_args__ = {"comment": "Organization-tenants (our multi-tenancy boundary)"}

    slug: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        index=True,
        nullable=False,
        comment="URL-safe tenant identifier (e.g. 'default', 'acme')",
    )

    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Display name",
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
        comment="Soft-disable a tenant without deleting rows",
    )

    def __repr__(self) -> str:
        return f"<Tenant(slug='{self.slug}')>"

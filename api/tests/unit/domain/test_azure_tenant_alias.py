"""Pydantic aliases preserve the legacy `tenant_id` wire/DB format.

PR 3a of the access-control plan renames Python-side identifiers from
`tenant_id` → `azure_tenant_id` for Microsoft / Azure / Teams / SharePoint
references. The on-wire and on-disk JSON shape must stay `tenant_id` so:
  - existing `agents.channels.ms_teams.tenant_id` rows keep deserializing,
  - the admin frontend keeps submitting `{"tenant_id": "..."}`,
  - external API consumers don't break.

Imports are deferred inside the test methods because the schemas module is
in a known circular-import chain triggered by `core.config.app` →
`services.agents` → `core.domain.agents` (pre-existing).
"""

from __future__ import annotations

# Warm the import graph before the schemas module is touched.
# Loading `core.domain.agents_channels.schemas` directly hits a pre-existing
# circular chain (utils.secrets → core.config.app → services.agents → ...).
# Importing the parent app package first lets the cycle resolve normally.
import core.config.app  # noqa: F401


class TestMsTeamsChannelAlias:
    def test_deserializes_legacy_tenant_id_key(self):
        from core.domain.agents_channels.schemas import MsTeamsChannelBase

        obj = MsTeamsChannelBase.model_validate(
            {"enabled": True, "client_id": "cid", "tenant_id": "azure-uuid"}
        )
        assert obj.azure_tenant_id == "azure-uuid"

    def test_accepts_python_name_too(self):
        from core.domain.agents_channels.schemas import MsTeamsChannelBase

        obj = MsTeamsChannelBase(
            enabled=True, client_id="cid", azure_tenant_id="azure-uuid"
        )
        assert obj.azure_tenant_id == "azure-uuid"

    def test_serializes_back_to_legacy_wire_key(self):
        from core.domain.agents_channels.schemas import MsTeamsChannelBase

        obj = MsTeamsChannelBase(
            enabled=True, client_id="cid", azure_tenant_id="azure-uuid"
        )
        wire = obj.model_dump(by_alias=True)
        assert wire["tenant_id"] == "azure-uuid"
        assert "azure_tenant_id" not in wire

    def test_validator_uses_renamed_field(self):
        from core.domain.agents_channels.schemas import MsTeamsChannelUpdate

        try:
            MsTeamsChannelUpdate.model_validate(
                {
                    "enabled": True,
                    "client_id": "cid",
                    "secret_value": "s",
                    # tenant_id deliberately missing
                }
            )
        except Exception as exc:
            assert "tenant_id" in str(exc)
        else:
            raise AssertionError("expected validation error for missing tenant_id")

    def test_subclasses_inherit_populate_by_name(self):
        from core.domain.agents_channels.schemas import MsTeamsChannel

        obj = MsTeamsChannel.model_validate(
            {"enabled": True, "client_id": "cid", "tenant_id": "azure-uuid"}
        )
        assert obj.azure_tenant_id == "azure-uuid"


class TestSharePointSourceCreateRequestAlias:
    def test_deserializes_legacy_tenant_id_key(self):
        from core.domain.knowledge_graph.schemas import SharePointSourceCreateRequest

        obj = SharePointSourceCreateRequest.model_validate(
            {
                "graph_id": "g",
                "site_url": "https://example.sharepoint.com/sites/x",
                "tenant_id": "azure-uuid",
            }
        )
        assert obj.azure_tenant_id == "azure-uuid"

    def test_serializes_back_to_legacy_wire_key(self):
        from core.domain.knowledge_graph.schemas import SharePointSourceCreateRequest

        obj = SharePointSourceCreateRequest(
            graph_id="g",
            site_url="https://example.sharepoint.com/sites/x",
            azure_tenant_id="azure-uuid",
        )
        wire = obj.model_dump(by_alias=True)
        assert wire["tenant_id"] == "azure-uuid"

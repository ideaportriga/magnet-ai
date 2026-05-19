"""Bind known auditable entity types to the audit registry.

Add a line here for every model that should be restorable through
``POST /admin/audit/entity-trail/{audit_id}/restore``. Read endpoints
work for any ``entity_type`` already written to the table — registration
is only required for restore.
"""

from __future__ import annotations

from core.audit import register_auditable
from core.db.models.agent import Agent
from core.db.models.ai_app import AIApp
from core.db.models.ai_model import AIModel
from core.db.models.api_server import APIServer
from core.db.models.collection import Collection
from core.db.models.knowledge_graph import KnowledgeGraph
from core.db.models.mcp_server import MCPServer
from core.db.models.prompt import Prompt
from core.db.models.provider import Provider
from core.db.models.rag_tool import RagTool
from core.db.models.retrieval_tool import RetrievalTool
from core.db.models.evaluation_set import EvaluationSet
from guards.permissions import Permission


# Encrypted-secret columns. Listed here as well as in each model's
# ``__audit_secret_fields__`` so the restore endpoint can guard against
# pushing an empty masked value back into the live row.
_SECRETS_FORBIDDEN: frozenset[str] = frozenset({"secrets_encrypted"})


def register_default_auditable_entities() -> None:
    register_auditable(
        entity_type="agent",
        model=Agent,
        write_permission=Permission.AGENTS_WRITE,
    )
    register_auditable(
        entity_type="prompt_template",
        model=Prompt,
        write_permission=Permission.PROMPTS_WRITE,
    )
    register_auditable(
        entity_type="rag_tool",
        model=RagTool,
        write_permission=Permission.RAG_TOOLS_WRITE,
    )
    register_auditable(
        entity_type="retrieval_tool",
        model=RetrievalTool,
        write_permission=Permission.RETRIEVAL_TOOLS_WRITE,
    )
    register_auditable(
        entity_type="ai_app",
        model=AIApp,
        write_permission=Permission.AI_APPS_WRITE,
    )
    register_auditable(
        entity_type="collection",
        model=Collection,
        write_permission=Permission.COLLECTIONS_WRITE,
    )
    register_auditable(
        entity_type="mcp_server",
        model=MCPServer,
        write_permission=Permission.MCP_SERVERS_WRITE,
        # Snapshots store masked secrets — never push them back as live
        # values on restore (would wipe the real encrypted blob).
        extra_forbidden=_SECRETS_FORBIDDEN,
    )
    register_auditable(
        entity_type="api_server",
        model=APIServer,
        write_permission=Permission.API_SERVERS_WRITE,
        extra_forbidden=_SECRETS_FORBIDDEN,
    )
    register_auditable(
        entity_type="provider",
        model=Provider,
        write_permission=Permission.PROVIDERS_WRITE,
        extra_forbidden=_SECRETS_FORBIDDEN,
    )
    register_auditable(
        entity_type="ai_model",
        model=AIModel,
        write_permission=Permission.AI_MODELS_WRITE,
    )
    register_auditable(
        entity_type="knowledge_graph",
        model=KnowledgeGraph,
        write_permission=Permission.KNOWLEDGE_GRAPH_WRITE,
    )
    register_auditable(
        entity_type="evaluation_set",
        model=EvaluationSet,
        write_permission=Permission.EVALUATIONS_WRITE,
    )

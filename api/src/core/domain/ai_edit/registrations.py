"""Bind entity types to the AI-edit registry.

We register the **editable subset** of each entity — typically the
"single variant body" the user actually shapes through the UI form,
not the wire-side DB schema. The schema layout differs per entity:

* Agent: ``EntityVariant`` wrapper with a ``value`` payload of type
  ``AgentVariantValue`` → register ``AgentVariantValue``; the frontend
  merges by writing ``variants[idx].value = new_state``.
* Prompt / RagTool / RetrievalTool: variants are flat ``PromptVariantSchema``
  / ``RagToolsBase`` / ``RetrievalToolsBase`` records where the ``variant``
  key is a sibling field, not a wrapper → register the whole record; the
  frontend merges by writing ``variants[idx] = new_state``.

Stick to entities we've validated end-to-end.
"""

from __future__ import annotations

from core.db.models.agent import Agent
from core.db.models.prompt import Prompt
from core.db.models.rag_tool import RagTool
from core.db.models.retrieval_tool import RetrievalTool
from core.domain.prompts.schemas import PromptVariantSchema
from guards.permissions import Permission
from services.agents.models import AgentVariantValue
from services.ai_entity_editor import register_ai_editable
from validation.rag_tools import RagToolsBase
from validation.retrieval_tools import RetrievalToolsBase


_COMMON_CONVENTIONS = """\

Conventions you must follow:
- The ``variant`` key on a variant entry is its stable identifier. New
  variants follow the pattern ``variant_N`` where N is a positive
  integer (``variant_1``, ``variant_2``, …) — pick the next free N
  when the user asks to add a variant. NEVER rename an existing
  ``variant`` key — references elsewhere break.
- ``system_name`` follows ``SCREAMING_SNAKE_CASE`` (letters, digits,
  underscores; starts with a letter). Treat it as read-only unless the
  user explicitly asks to rename — downstream code looks entities up
  by it.
- Prefer EDITING existing entries over replacing them. When a list
  change is requested, mutate the elements you need and keep the rest
  byte-for-byte identical.
- Keys you didn't change MUST appear in the result with their current
  values (or ``null`` for originally-optional fields the user did not
  touch).
"""


_AGENT_DESCRIPTION = (
    """\
An "agent" is a conversational AI assistant defined by:
- one or more topic blocks that group a system prompt + a set of tool/action
  configurations the LLM can call. Each topic has a ``system_name``
  (SCREAMING_SNAKE_CASE), a human ``name``, an ``instructions`` block,
  and a list of ``actions`` that the agent can invoke.
- a small set of dialogue ``settings`` (welcome message, memory
  strategy, sample questions). ``sample_questions.questions`` is a
  dict where keys follow the pattern ``question1`` … ``question10``
  (max 10 entries).
- two ``prompt_templates``: one for intent classification and one for
  the per-topic completion call.

Each agent has one or more variants (A/B configurations) — ``active_variant``
is the one that real conversations use.
"""
    + _COMMON_CONVENTIONS
)


_PROMPT_DESCRIPTION = (
    """\
A "prompt template" is a single named, parameterised LLM prompt the
system can execute on demand. Each variant carries the actual prompt
``text`` plus generation parameters:
- ``temperature`` ∈ [0, 2], ``topP`` ∈ [0, 1].
- ``maxTokens`` — positive integer or null for "model default".
- ``observability_level`` — one of ``"full"``, ``"metadata-only"``,
  ``"none"``. Keep current value unless asked.
- ``system_name_for_model`` — system_name of an AI model. Do not
  invent one; keep the current value when in doubt.

Variants are A/B configurations of the same prompt; the active one is
used at runtime.
"""
    + _COMMON_CONVENTIONS
)


_RAG_DESCRIPTION = (
    """\
A "RAG tool" is a Retrieval-Augmented-Generation configuration. Each
variant has:
- ``retrieve``: which collections to query, top_k, reranking, etc.,
- ``generate``: the synthesis prompt and the model used to compose the
  final answer,
- ``post_process`` / ``ui_settings`` / ``language`` (optional polish).

Keep ``description`` short and human-readable — it shows up in UI
listings.
"""
    + _COMMON_CONVENTIONS
)


_RETRIEVAL_DESCRIPTION = (
    """\
A "retrieval tool" is a structured query over the knowledge base used
inside agents and RAG pipelines. Each variant defines the filters,
metadata selectors, and rerank behaviour applied to a query.
"""
    + _COMMON_CONVENTIONS
)


def register_default_ai_editables() -> None:
    register_ai_editable(
        entity_type="agent",
        resource_type="agents",
        model=Agent,
        editable_schema=AgentVariantValue,
        human_description=_AGENT_DESCRIPTION,
        write_permission=Permission.AGENTS_WRITE,
        variant_shape="wrapped",
    )
    register_ai_editable(
        entity_type="prompt_template",
        resource_type="prompts",
        model=Prompt,
        editable_schema=PromptVariantSchema,
        human_description=_PROMPT_DESCRIPTION,
        write_permission=Permission.PROMPTS_WRITE,
        variant_shape="flat",
    )
    register_ai_editable(
        entity_type="rag_tool",
        resource_type="rag_tools",
        model=RagTool,
        editable_schema=RagToolsBase,
        human_description=_RAG_DESCRIPTION,
        write_permission=Permission.RAG_TOOLS_WRITE,
        variant_shape="flat",
    )
    register_ai_editable(
        entity_type="retrieval_tool",
        resource_type="retrieval_tools",
        model=RetrievalTool,
        editable_schema=RetrievalToolsBase,
        human_description=_RETRIEVAL_DESCRIPTION,
        write_permission=Permission.RETRIEVAL_TOOLS_WRITE,
        variant_shape="flat",
    )

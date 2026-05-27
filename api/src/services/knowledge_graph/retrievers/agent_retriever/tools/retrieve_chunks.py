"""
Knowledge Graph retrieval tool: `retrieveChunks`.

This module contains three closely-related pieces:

1) **TOOL_SPEC**: the OpenAI "function tool" schema that is sent to the LLM.
2) **retrieveChunks(...)**: the actual server-side implementation.
3) **_reformulate_query(...)**: turns the agent's natural-language information
   need into a keyword-friendly term and a vector-friendly phrase using a
   configurable prompt template.

Keeping the schema next to the implementation makes it easy to evolve the tool
contract without hunting through a central registry file.

The agent describes *what it is looking for* (``query``) plus optional context
(``context_hint``). When the tool is configured with ``promptTemplateName`` the
intent is reformulated into two distinct search inputs: a keyword term used for
full-text / trigram matching and a natural phrase used to build the embedding.
"""

import asyncio
import logging
import time
from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from core.domain.knowledge_graph.services import KnowledgeGraphChunkService
from open_ai.utils_new import get_embeddings
from services.observability import observability_context, observe
from services.observability.models import SpanType
from services.prompt_templates.services import execute_prompt_template

logger = logging.getLogger(__name__)

# OpenAI tool schema (sent to the LLM).
# `get_available_tools()` may augment this schema at runtime based on graph config.
TOOL_SPEC: dict[str, Any] = {
    "type": "function",
    "function": {
        "name": "retrieveChunks",
        "description": "Searches the document corpus for passages relevant to an information need. You don't need to think about retrieval mechanics - just describe what you're looking for.",
        "parameters": {
            "type": "object",
            "properties": {
                "reasoning": {
                    "type": "string",
                    "description": "Why you are using this tool.",
                },
                "query": {
                    "type": "string",
                    "description": (
                        "A natural-language description of the information you need.\n"
                        "Phrase it as what a relevant passage would discuss, not as keywords.\n\n"
                        'Good: "the warranty period and conditions for the X200 thermostat"\n'
                        'Good: "how users can cancel their subscription"\n'
                        'Good: "side effects of ibuprofen in elderly patients"\n\n'
                        'Avoid: "warranty X200" (too sparse; the tool handles keyword extraction)\n'
                        'Avoid: "Tell me about warranties" (too vague; specify what about them)'
                    ),
                },
                "context_hint": {
                    "type": "string",
                    "description": (
                        "One or two sentences of surrounding context that shape what counts "
                        "as relevant. Use when the query alone is ambiguous, when the user's "
                        "broader goal affects which passages matter, or when the conversation "
                        "has established a topic the query implicitly assumes.\n\n"
                        "Skip when the query is self-contained."
                        "Example uses:\n"
                        '  query: "what does it say about exceptions"\n'
                        '  context_hint: "The user is asking about exceptions to the 30-day '
                        '    return policy discussed in the previous turn."\n\n'
                        '  query: "compare the two approaches"\n'
                        '  context_hint: "The user is evaluating microservices vs monolithic '
                        '    architectures for a small team."'
                    ),
                },
            },
            "required": ["reasoning", "query"],
        },
    },
}


def _parse_reformulation(content: str) -> tuple[list[str], list[str]]:
    """Parse the reformulation model output into variant lists.

    Expects one or more labelled lines (plain text, not JSON)::

        KEYWORDS: <one or two keywords>
        SEMANTIC: <natural-language phrase>
        KEYWORDS: <alternative keywords>
        SEMANTIC: <alternative phrase>

    Returns ``(keyword_queries, semantic_queries)`` — every non-empty
    ``KEYWORDS`` line collected into the first list and every non-empty
    ``SEMANTIC`` line into the second, in the order they appear. Label matching
    is case-insensitive and tolerates the singular ``KEYWORD:``.
    """

    keywords: list[str] = []
    semantics: list[str] = []
    for raw_line in (content or "").splitlines():
        line = raw_line.strip()
        if ":" not in line:
            continue
        label, _, value = line.partition(":")
        label = label.strip().lower()
        value = value.strip()
        if not value:
            continue
        if label.startswith("keyword"):
            keywords.append(value)
        elif label.startswith("semantic"):
            semantics.append(value)
    return keywords, semantics


def _dedupe_preserve_order(items: list[str]) -> list[str]:
    """Drop empties and case-insensitive duplicates, preserving first-seen order."""

    seen: set[str] = set()
    out: list[str] = []
    for item in items:
        key = item.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(item.strip())
    return out


async def _reformulate_query(
    query: str,
    context_hint: str | None,
    prompt_template_name: str | None,
    *,
    keyword_count: int,
    semantic_count: int,
) -> tuple[list[str], list[str]]:
    """Reformulate the agent's intent into keyword and semantic query variants.

    Uses the configured ``prompt_template_name`` to ask an LLM for up to
    ``keyword_count`` keyword-friendly terms and ``semantic_count``
    vector-friendly natural phrases. Returns ``(keyword_queries,
    semantic_queries)``; each list is deduplicated and capped to its requested
    count. If no template is configured, or anything goes wrong, falls back to
    using ``query`` as the single variant for any search type whose count > 0,
    so the tool always remains usable.
    """

    def _fallback() -> tuple[list[str], list[str]]:
        return (
            [query] if keyword_count > 0 else [],
            [query] if semantic_count > 0 else [],
        )

    if not prompt_template_name:
        return _fallback()

    try:
        response = await execute_prompt_template(
            system_name_or_config=prompt_template_name,
            template_values={
                "query": query,
                "context_hint": context_hint or "",
                "keyword_count": keyword_count,
                "semantic_count": semantic_count,
            },
            template_additional_messages=[{"role": "user", "content": query}],
        )
        keywords, semantics = _parse_reformulation(response.content)
        keyword_queries = _dedupe_preserve_order(keywords)[: max(keyword_count, 0)]
        semantic_queries = _dedupe_preserve_order(semantics)[: max(semantic_count, 0)]
        # Guarantee at least one variant for any search type the mode needs.
        if keyword_count > 0 and not keyword_queries:
            keyword_queries = [query]
        if semantic_count > 0 and not semantic_queries:
            semantic_queries = [query]
        return keyword_queries, semantic_queries
    except Exception as exc:
        logger.warning(
            "Chunk query reformulation via '%s' failed (%s); using raw query.",
            prompt_template_name,
            exc,
        )
        return _fallback()


@observe(
    name="Retrieve chunks",
    type=SpanType.TOOL,
    description=(
        "Knowledge-graph retrieval tool: reformulates the agent's intent and returns "
        "the most relevant chunks using the graph's configured search method "
        "(vector / keyword / hybrid)."
    ),
)
async def retrieveChunks(
    db_session: AsyncSession,
    graph_id: UUID,
    query: str,
    embedding_model: str,
    *,
    limit: int,
    min_score: float,
    doc_filter_ids: list[str],
    tool_cfg: dict[str, Any],
    context_hint: str | None = None,
    doc_filter_where_sql: str | None = None,
    doc_filter_where_params: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """
    Return KG chunks most relevant to the agent's information need.

    This is used in the agentic ReAct loop as the "detail retrieval" step.

    Inputs:
    - **query**: the natural-language information need (what would be a useful result).
    - **context_hint**: optional context describing why the information is needed.
    - **embedding_model**: used to produce the query embedding.
    - **limit / min_score**: hard filter after retrieval.
    - **doc_filter_ids / doc_filter_where_sql**: optional restrictions computed
      by earlier tools (e.g., metadata filtering).
    - **tool_cfg**: graph-configured tool settings; supplies ``searchMethod``
      (``vector`` | ``keyword`` | ``hybrid``), ``rrfK`` (RRF constant),
      ``candidatePoolSize`` (rows each sub-query fetches before fusion),
      ``keywordVariants`` / ``vectorVariants`` (how many query variants to
      generate per search type) and an optional ``promptTemplateName`` used to
      reformulate the query.

    When ``promptTemplateName`` is configured, ``query``/``context_hint`` are
    reformulated into up to ``keywordVariants`` keyword terms (used for
    full-text / trigram search) and up to ``vectorVariants`` semantic phrases
    (each embedded for vector search). Otherwise ``query`` is used as the single
    variant. Each variant contributes its own sub-query to the RRF fusion (or,
    in pure vector mode, a cosine search merged by max similarity per chunk).

    Output:
    - A list of JSON-serializable chunk dicts (`ChunkSearchResult.to_json()`),
      filtered to `score >= min_score`.
    """

    search_method = tool_cfg["searchMethod"]
    rrf_k = int(tool_cfg["rrfK"])
    prompt_template_name = tool_cfg.get("promptTemplateName")
    candidate_pool = max(1, int(tool_cfg.get("candidatePoolSize", 30)))
    keyword_variants = max(1, int(tool_cfg.get("keywordVariants", 1)))
    vector_variants = max(1, int(tool_cfg.get("vectorVariants", 1)))
    doc_filter_count = len(doc_filter_ids) if doc_filter_ids else 0

    # How many variants each search type needs for the active mode. Keyword mode
    # never embeds; vector mode never runs lexical sub-queries.
    if search_method == "keyword":
        keyword_count, semantic_count = keyword_variants, 0
    elif search_method == "vector":
        keyword_count, semantic_count = 0, vector_variants
    else:  # hybrid
        keyword_count, semantic_count = keyword_variants, vector_variants

    reformulate_started = time.perf_counter()
    keyword_queries, semantic_queries = await _reformulate_query(
        query,
        context_hint,
        prompt_template_name,
        keyword_count=keyword_count,
        semantic_count=semantic_count,
    )
    reformulation_ms = round((time.perf_counter() - reformulate_started) * 1000, 2)

    logger.info(
        "retrieveChunks start graph_id=%s method=%s limit=%d threshold=%.3f "
        "rrf_k=%d candidate_pool=%d doc_filter_ids=%d query=%r keywords=%s semantics=%s",
        graph_id,
        search_method,
        limit,
        min_score,
        rrf_k,
        candidate_pool,
        doc_filter_count,
        query[:120],
        [k[:80] for k in keyword_queries],
        [s[:80] for s in semantic_queries],
    )

    observability_context.update_current_span(
        input={
            "query": query,
            "context_hint": context_hint,
            "num_results": limit,
            "score_threshold": min_score,
            "search_method": search_method,
            "rrf_k": rrf_k,
            "candidate_pool": candidate_pool,
            "keyword_variants": len(keyword_queries),
            "vector_variants": len(semantic_queries),
            "doc_filter_ids_count": doc_filter_count,
            "metadata_filter_active": bool(doc_filter_where_sql),
        },
        extra_data={"tool_type": "search"},
    )

    started = time.perf_counter()
    embedding_ms: float | None = None
    vectors: list[list[float]] = []
    if semantic_queries:
        embed_started = time.perf_counter()
        vectors = list(
            await asyncio.gather(
                *[get_embeddings(s, embedding_model) for s in semantic_queries]
            )
        )
        embedding_ms = round((time.perf_counter() - embed_started) * 1000, 2)

    chunks = await KnowledgeGraphChunkService().search_chunks(
        db_session,
        graph_id=graph_id,
        search_method=search_method,
        query_vectors=vectors,
        query_texts=keyword_queries,
        rrf_k=rrf_k,
        limit=limit,
        candidate_pool=candidate_pool,
        only_doc_ids=doc_filter_ids if doc_filter_ids else None,
        doc_filter_where_sql=doc_filter_where_sql,
        doc_filter_where_params=doc_filter_where_params,
    )

    kept = [c for c in chunks if c.score is not None and c.score >= min_score]
    elapsed_ms = round((time.perf_counter() - started) * 1000, 2)
    top_scores = [round(float(c.score or 0.0), 4) for c in kept[:5]]
    dropped_by_threshold = len(chunks) - len(kept)

    # Keep the parent span's `output` as the actual retrieved chunks — that's
    # what humans want to see when they open the trace. Hybrid statistics
    # live separately in `extra_data` so they don't crowd the output panel.
    observability_context.update_current_span(output=[c.to_json() for c in kept])
    logger.info(
        "retrieveChunks done method=%s raw=%d kept=%d dropped=%d "
        "reformulation_ms=%s embedding_ms=%s total_ms=%.2f top_scores=%s",
        search_method,
        len(chunks),
        len(kept),
        dropped_by_threshold,
        reformulation_ms,
        embedding_ms,
        elapsed_ms,
        top_scores,
    )
    return [c.to_json() for c in kept]

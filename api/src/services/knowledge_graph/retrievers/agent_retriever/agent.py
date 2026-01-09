import json
import logging
from typing import Any, Sequence
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from core.domain.knowledge_graph.schemas import (
    KnowledgeGraphRetrievalPreviewResponse,
    KnowledgeGraphRetrievalWorkflowStep,
)
from open_ai.utils_new import (
    create_chat_completion_from_prompt_template,
)
from prompt_templates.prompt_templates import get_prompt_template_by_system_name_flat
from services.knowledge_graph.content_config_services import (
    get_graph_embedding_model,
    get_graph_settings,
)
from services.observability import observability_overrides, observe

from .tools import get_available_tools
from .tools.exit_tool import exit_tool
from .tools.find_chunks_by_similarity import findChunksBySimilarity
from .tools.find_documents_by_metadata import findDocumentsByMetadata
from .tools.find_documents_by_summary_similarity import findDocumentsBySummarySimilarity

logger = logging.getLogger(__name__)


def _build_example_list_str(retrieval_examples: list[dict[str, Any]]) -> str:
    """Build the example list string for the prompt."""
    example_list_parts = []
    if retrieval_examples:
        example_list_parts.append("# Answer Examples")

    for i, ex in enumerate(retrieval_examples, 1):
        title = ex.get("title", "").strip()
        input_text = ex.get("input", "").strip()
        output_text = ex.get("output", "").strip()

        header = f"## Example {i}"
        if title:
            header += f": {title}"

        if input_text and output_text:
            example_list_parts.append(
                f"{header}\n\n**User:** {input_text}\n\n**Agent:**\n\n```\n{output_text}\n```"
            )
    return "\n\n".join(example_list_parts)


def _build_exit_strategy_instr(strategy: str) -> str:
    """Build the exit strategy instructions for the prompt."""
    if strategy == "confidence":
        return (
            "- **Strategy: Confidence-based**\n"
            "  - Balance thoroughness with efficiency.\n"
            "  - Exit as soon as you have gathered enough information to answer the user's query with high confidence.\n"
            "  - Do not perform redundant searches if the answer is already clear."
        )
    elif strategy == "exhaustive":
        return (
            "- **Strategy: Exhaustive**\n"
            "  - Prioritize comprehensive coverage over speed.\n"
            "  - Continue searching until you are certain you have explored all relevant aspects of the query.\n"
            "  - Look for supplementary or contradictory information even if a direct answer is found."
        )
    elif strategy == "efficient":
        return (
            "- **Strategy: Efficient**\n"
            "  - Prioritize speed and minimal tool usage.\n"
            "  - Exit immediately once a satisfactory answer is found.\n"
            "  - Avoid optional or tangential searches."
        )
    return ""


def _build_output_instr(output_format: str) -> str:
    """Build the output instructions for the prompt."""
    if output_format == "markdown":
        return "# Output Instructions:\n- Return answer formatted as Markdown"
    elif output_format == "plain":
        return "# Output Instructions:\n- Return answer formatted as Plain Text"
    return ""


@observe(
    name="Run agentic loop",
    description="Run agentic loop to retrieve data from the knowledge graph.",
)
async def run_agentic_retrieval(
    db_session: AsyncSession,
    graph_id: UUID,
    chat_history: Sequence[dict[str, Any]],
    *,
    external_tool_inputs: dict[str, Any] | None = None,
) -> KnowledgeGraphRetrievalPreviewResponse:
    """Execute agentic retrieval against a Knowledge Graph using ReAct."""

    # Resolve Knowledge Graph settings
    settings = await get_graph_settings(db_session, graph_id)
    retrieval_variant = settings.get("retrieval_variant") or "base_variant"
    retrieval_tools_cfg: dict[str, Any] = settings.get("retrieval_tools") or {}
    retrieval_examples: list[dict[str, Any]] = settings.get("retrieval_examples") or []

    # Format examples for the prompt
    example_list_str = _build_example_list_str(retrieval_examples)

    docs_tool_cfg = (
        retrieval_tools_cfg.get("findDocumentsBySummarySimilarity", {}) or {}
    )
    meta_tool_cfg = retrieval_tools_cfg.get("findDocumentsByMetadata", {}) or {}
    chunks_tool_cfg = retrieval_tools_cfg.get("findChunksBySimilarity", {}) or {}
    exit_tool_cfg = retrieval_tools_cfg.get("exit", {}) or {}

    answer_mode = exit_tool_cfg.get("answerMode") or "answer_with_sources"
    output_format = exit_tool_cfg.get("outputFormat") or "markdown"
    strategy = exit_tool_cfg.get("strategy") or "confidence"

    chunk_limit = int(chunks_tool_cfg.get("limit", 5))
    chunk_score_threshold = float(chunks_tool_cfg.get("scoreThreshold", 0.7))
    max_iterations = int(exit_tool_cfg.get("maxIterations", 4))

    metadata_field_definitions: list[dict[str, Any]] = []
    try:
        metadata_cfg = settings.get("metadata") or {}
        raw_defs = metadata_cfg.get("field_definitions")
        if isinstance(raw_defs, list):
            metadata_field_definitions = [d for d in raw_defs if isinstance(d, dict)]
    except Exception:
        metadata_field_definitions = []

    # Resolve embedding model from graph settings
    embedding_model = await get_graph_embedding_model(db_session, graph_id)
    if not embedding_model:
        return KnowledgeGraphRetrievalPreviewResponse(
            content="Embedding model is not configured for this knowledge graph.",
            sources=[],
        )

    # Load ReAct prompt from prompt templates
    prompt_cfg = await get_prompt_template_by_system_name_flat(
        "KG_AGENT_REACT_PROMPT", retrieval_variant
    )

    # Define Exit Strategy Prompt
    exitStrategy = _build_exit_strategy_instr(strategy)

    # TODO: for preview, we should use the prompt template from the graph settings, because it might be unsaved yet
    tools = get_available_tools(
        retrieval_tools_cfg, metadata_field_definitions=metadata_field_definitions
    )

    # Normalize incoming history to role/content pairs; ignore other keys
    normalized_history: list[dict[str, Any]] = []
    for m in chat_history or []:
        role = m.get("role")
        content = m.get("content")
        if role in {"user", "assistant"} and content is not None:
            normalized_history.append({"role": role, "content": content})

    # Determine the latest user query
    last_user_query: str = ""
    for m in reversed(normalized_history):
        if m.get("role") == "user" and m.get("content"):
            last_user_query = str(m["content"])
            break

    # State for the ReAct loop starting from full chat history
    agent_messages: list[dict[str, Any]] = []
    ext_inputs = external_tool_inputs if isinstance(external_tool_inputs, dict) else {}
    # Let the model know about external constraints (if present).
    try:
        if ext_inputs:
            agent_messages.append(
                {
                    "role": "system",
                    "content": (
                        "External tool inputs are provided by the caller and may constrain retrieval.\n"
                        "Do NOT invent or assume external filters. Use the provided inputs.\n"
                        f"external_tool_inputs = {json.dumps(ext_inputs, ensure_ascii=False)}"
                    ),
                }
            )
    except Exception:
        pass
    agent_messages.extend(list(normalized_history))

    relevant_document_ids: list[str] = []
    collected_chunks: list[dict[str, Any]] = []
    successful_answer: str = ""
    erroneous_answer: str = ""
    workflow_steps: list[KnowledgeGraphRetrievalWorkflowStep] = []
    last_metadata_doc_where_sql: str | None = None
    last_metadata_doc_where_params: dict[str, Any] | None = None

    # ReAct loop
    for iteration_idx in range(1, max_iterations + 1):
        # Calculate dynamic instructions
        remaining_iterations = max_iterations - iteration_idx
        if remaining_iterations == 0:
            exit_instr = (
                f"# Exit Instructions:\n"
                f"- **CRITICAL RULE** - YOU MUST PROVIDE A FINAL ANSWER OR EXCUSE YOURSELF!\n"
                f"- This is your LAST iteration (iteration {iteration_idx} of {max_iterations}).\n"
                f"- You MUST provide a final answer or excuse yourself. Call exit tool now."
            )
        else:
            exit_instr = (
                f"# Exit Instructions:\n"
                f"- Iteration {iteration_idx} of {max_iterations}. You have {remaining_iterations} iterations left.\n"
                f"{exitStrategy}\n"
            )

        # Filter tools for the last iteration
        current_tools = tools
        if remaining_iterations == 0:
            current_tools = [
                t for t in tools if t.get("function", {}).get("name") == "exit"
            ]

        output_instr = _build_output_instr(output_format)

        chat_completion, _ = await create_chat_completion_from_prompt_template(
            prompt_template_config=prompt_cfg,
            prompt_template_values={
                "exitInstructions": exit_instr,
                "outputInstructions": output_instr,
                "exampleList": example_list_str,
            },
            additional_messages=agent_messages,
            tools=current_tools,
            tool_choice="required",
        )
        msg = chat_completion.choices[0].message
        tool_calls = msg.tool_calls

        # If model returned no tool calls, break from the loop and return an error
        if not tool_calls or len(tool_calls) == 0:
            successful_answer = msg.content
            break

        # Record the assistant's tool call message
        assistant_tool_message = {
            "role": "assistant",
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in (msg.tool_calls or [])
            ],
        }
        agent_messages.append(assistant_tool_message)

        # Execute tools and append tool results
        exit_from_loop = False
        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            try:
                args = {}
                if tool_call.function.arguments:
                    try:
                        args = json.loads(tool_call.function.arguments)
                    except Exception:
                        args = {}
                query = str(args.get("query") or last_user_query)

                if tool_name == "findDocumentsByMetadata":
                    tool_payload, loop_state, step = await findDocumentsByMetadata(
                        db_session=db_session,
                        graph_id=graph_id,
                        args=args,
                        iteration=iteration_idx,
                        tool_name=tool_name,
                        tool_cfg=meta_tool_cfg,
                        external_tool_inputs=ext_inputs,
                        field_definitions=metadata_field_definitions,
                        **observability_overrides(description=args.get("reasoning")),
                    )
                    last_metadata_doc_where_sql = loop_state.get("doc_filter_where_sql")
                    last_metadata_doc_where_params = loop_state.get(
                        "doc_filter_where_params"
                    )
                    workflow_steps.append(step)
                elif tool_name == "findDocumentsBySummarySimilarity":
                    (
                        tool_payload,
                        loop_state,
                        step,
                    ) = await findDocumentsBySummarySimilarity(
                        db_session=db_session,
                        graph_id=graph_id,
                        query=query,
                        embedding_model=embedding_model,
                        args=args,
                        iteration=iteration_idx,
                        tool_name=tool_name,
                        tool_cfg=docs_tool_cfg,
                        **observability_overrides(description=args.get("reasoning")),
                    )
                    relevant_document_ids = loop_state.get("doc_filter_ids") or []
                    workflow_steps.append(step)
                elif tool_name == "findChunksBySimilarity":
                    limit_arg = chunk_limit
                    min_score_arg = chunk_score_threshold
                    if chunks_tool_cfg.get("searchControl") == "agent":
                        limit_arg = int(args.get("limit", chunk_limit))
                        min_score_arg = float(
                            args.get("scoreThreshold", chunk_score_threshold)
                        )

                    chunks = await findChunksBySimilarity(
                        db_session=db_session,
                        graph_id=graph_id,
                        q=query,
                        embedding_model=embedding_model,
                        limit=limit_arg,
                        min_score=min_score_arg,
                        doc_filter_ids=relevant_document_ids,
                        doc_filter_where_sql=last_metadata_doc_where_sql,
                        doc_filter_where_params=last_metadata_doc_where_params,
                        **observability_overrides(description=args.get("reasoning")),
                    )
                    collected_chunks.extend(chunks)
                    tool_payload = {"chunks": chunks}
                    workflow_steps.append(
                        KnowledgeGraphRetrievalWorkflowStep(
                            iteration=iteration_idx,
                            tool=tool_name,
                            arguments={
                                "query": query,
                                "doc_filter_ids": relevant_document_ids,
                            },
                            call_summary={
                                "reasoning": args.get("reasoning"),
                                "result_count": len(chunks),
                            },
                        )
                    )
                elif tool_name == "exit":
                    successful_answer = exit_tool(
                        args.get("answer", ""), args.get("reasoning", "")
                    )
                    tool_payload = {"answer": successful_answer}
                    workflow_steps.append(
                        KnowledgeGraphRetrievalWorkflowStep(
                            iteration=iteration_idx,
                            tool=tool_name,
                            arguments={
                                "reasoning": args.get("reasoning"),
                                "answer": successful_answer,
                            },
                            call_summary={"reasoning": args.get("reasoning")},
                        )
                    )
                    exit_from_loop = True
                else:
                    erroneous_answer = f"Unknown tool call: {tool_name}. Incorrect prompt or model configuration, contact support."
                    exit_from_loop = True

                agent_messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": json.dumps(tool_payload),
                    }
                )
            except Exception as exc:
                erroneous_answer = (
                    f"Tool execution failed: {str(exc)}. Contact support."
                )
                exit_from_loop = True

        if exit_from_loop:
            break

    if erroneous_answer:
        return KnowledgeGraphRetrievalPreviewResponse(content=erroneous_answer)

    # Build sources from collected chunks (top N unique by chunk id)
    sources: list[dict[str, Any]] = []
    seen_chunk_ids: set[str] = set()
    for ch in sorted(collected_chunks, key=lambda x: x.get("score", 0.0), reverse=True)[
        :10
    ]:
        cid = str(ch.get("id"))
        if not cid or cid in seen_chunk_ids:
            continue
        seen_chunk_ids.add(cid)
        sources.append(
            {
                "title": ch.get("title"),
                "content": ch.get("content"),
            }
        )

    final_content = successful_answer or ""
    final_sources = sources

    if answer_mode == "answer_only":
        final_sources = []
    elif answer_mode == "sources_only":
        final_content = ""

    return KnowledgeGraphRetrievalPreviewResponse(
        content=final_content,
        sources=final_sources,
        workflow=workflow_steps,
    )

import json
import logging
from datetime import datetime
from typing import Any, Awaitable, Callable
from uuid import UUID

from core.config.app import alchemy
from core.domain.deep_research.schemas import DeepResearchRunUpdateSchema
from core.domain.deep_research.service import DeepResearchRunService
from services.api_servers.services import call_api_server_tool
from services.api_servers.types import ApiToolCall, ApiToolCallInputParams
from services.observability import observe, observability_context
from services.prompt_templates import execute_prompt_template

from .models import (
    AnalyzeResultsStepDetails,
    DeepResearchConfig,
    DeepResearchIteration,
    DeepResearchMemory,
    DeepResearchRun,
    DeepResearchStatus,
    DeepResearchStep,
    ProcessPageStepDetails,
    ReasoningStepDetails,
    SearchResultsAnalysis,
    SearchStepDetails,
    StepType,
    WebhookCallDetails,
)

from core.db.models.deep_research.run import DeepResearchRun as DeepResearchRunDB


logger = logging.getLogger(__name__)


def _track_usage(run: DeepResearchRun, result_data: Any) -> None:
    """
    Track usage, cost, and latency from execute_prompt_template result.
    Accumulates metrics in the run object.
    """
    if not result_data:
        return

    # Track latency
    if hasattr(result_data, "latency") and result_data.latency:
        if run.total_latency is None:
            run.total_latency = 0.0
        run.total_latency += result_data.latency

    # Track cost
    if hasattr(result_data, "cost") and result_data.cost:
        if run.total_cost is None:
            run.total_cost = 0.0
        run.total_cost += result_data.cost

    # Track usage
    if hasattr(result_data, "usage") and result_data.usage:
        if run.total_usage is None:
            run.total_usage = {
                "prompt_tokens": 0,
                "completion_tokens": 0,
                "total_tokens": 0,
            }

        usage = result_data.usage
        run.total_usage["prompt_tokens"] += usage.get("prompt_tokens", 0)
        run.total_usage["completion_tokens"] += usage.get("completion_tokens", 0)
        run.total_usage["total_tokens"] += usage.get("total_tokens", 0)


@observe(name="Deep research execution")
async def execute_deep_research(
    run: DeepResearchRun,
    persist_callback: Callable[[DeepResearchRun], Awaitable[None]] | None = None,
) -> None:
    async def persist_state() -> None:
        if not persist_callback:
            return
        try:
            await persist_callback(run)
        except Exception:
            logger.exception(
                "Failed to persist deep research run state",
                extra={"run_id": run.run_id},
            )

    try:
        run.status = DeepResearchStatus.RUNNING
        run.updated_at = datetime.utcnow()
        await persist_state()

        config = run.config
        memory = run.memory

        # Main research loop - counts reasoning iterations
        iteration_num = 0

        while iteration_num <= config.max_iterations:
            logger.info(
                "Deep research run %s, iteration %s/%s",
                run.run_id,
                iteration_num,
                config.max_iterations,
            )

            # Create new iteration
            current_iteration = DeepResearchIteration(steps=[])

            # Determine if we should still allow tool calls
            # On the last iteration, don't allow tools to force final report
            allow_tools = iteration_num < config.max_iterations

            # Step 1: Agent reasoning - decide what to do next (may call tools)
            reasoning_step = await _execute_reasoning_step(
                run=run,
                iteration=iteration_num,
                config=config,
                memory=memory,
                allow_tools=allow_tools,
            )
            current_iteration.steps.append(reasoning_step)

            if reasoning_step.error:
                logger.error("Reasoning step failed: %s", reasoning_step.error)
                run.iterations.append(current_iteration)
                run.updated_at = datetime.utcnow()
                await persist_state()
                break

            # Check if agent returned content without tool calls (final report or forced conclusion)
            # We need to get this from the conversation history since steps don't store raw output anymore
            last_message = (
                memory.conversation_history[-1] if memory.conversation_history else {}
            )
            tool_calls = last_message.get("tool_calls", [])

            if not tool_calls:
                # No tool calls - this is the final report (early exit)
                content = last_message.get("content", "")
                if content:
                    try:
                        # Try to parse JSON content as the final report
                        report_data = json.loads(content)
                        run.result = report_data
                    except json.JSONDecodeError:
                        # If not valid JSON, store as plain text
                        run.result = {"content": content}

                    run.status = DeepResearchStatus.COMPLETED
                    run.iterations.append(current_iteration)
                    run.updated_at = datetime.utcnow()
                    logger.info("Research completed with final report (early exit)")
                    await persist_state()
                    break
                else:
                    logger.warning("Reasoning returned no content and no tool calls")
                    run.status = DeepResearchStatus.FAILED
                    run.error = "Reasoning step returned no content and no tool calls"
                    run.iterations.append(current_iteration)
                    run.updated_at = datetime.utcnow()
                    await persist_state()
                    break

            # Step 2: Process tool calls from this iteration
            for tool_call in tool_calls:
                # Extract function name and arguments from tool call structure
                function_info = tool_call.get("function", {})
                function_name = function_info.get("name", "")

                if function_name == "web_search":
                    logger.info(
                        "Executing web_search tool call in iteration %s", iteration_num
                    )

                    try:
                        arguments_str = function_info.get("arguments", "{}")
                        arguments = (
                            json.loads(arguments_str)
                            if isinstance(arguments_str, str)
                            else arguments_str
                        )
                        search_query = arguments.get("query", "")
                    except json.JSONDecodeError as e:
                        # Fail fast: tool call arguments must be valid JSON
                        error_msg = (
                            "Failed to parse web_search tool call arguments: %s. Arguments: %s"
                            % (e, function_info.get("arguments"))
                        )
                        logger.error(error_msg)
                        run.status = DeepResearchStatus.FAILED
                        run.error = error_msg
                        run.iterations.append(current_iteration)
                        run.updated_at = datetime.utcnow()
                        await persist_state()
                        return

                    # Execute full web search workflow (multiple steps added to current_iteration)
                    search_summary = await _execute_web_search_workflow(
                        run=run,
                        current_iteration=current_iteration,
                        config=config,
                        memory=memory,
                        query=search_query,
                        tool_call_id=tool_call.get("id", ""),
                    )

                    # Add tool response to conversation history
                    memory.conversation_history.append(
                        {
                            "role": "tool",
                            "content": search_summary,
                            "tool_call_id": tool_call.get("id", ""),
                            "name": function_name,
                        }
                    )
                else:
                    logger.warning("Unrecognized tool call: %s", function_name)
                    memory.conversation_history.append(
                        {
                            "role": "tool",
                            "content": (
                                f"Error: Tool '{function_name}' is not supported. Only 'web_search' is available."
                            ),
                            "tool_call_id": tool_call.get("id", ""),
                            "name": function_name,
                        }
                    )

            # Add completed iteration to run
            run.iterations.append(current_iteration)
            run.updated_at = datetime.utcnow()
            await persist_state()

            # Increment iteration counter after processing all tool calls
            iteration_num += 1

        # Update timestamp (status is already COMPLETED from the loop)
        run.updated_at = datetime.utcnow()
        await persist_state()

        # Call webhook if configured
        if run.status == DeepResearchStatus.COMPLETED and config.webhook:
            if (
                config.webhook.enabled
                and config.webhook.api_server
                and config.webhook.api_tool
            ):
                await _call_webhook(run, config)
                # Save run state with webhook details
                await persist_state()

    except Exception as e:
        logger.exception("Deep research run %s failed with exception", run.run_id)
        run.status = DeepResearchStatus.FAILED
        run.error = str(e)
        run.updated_at = datetime.utcnow()
        await persist_state()


@observe(name="Web search workflow")
async def _execute_web_search_workflow(
    run: DeepResearchRun,
    current_iteration: DeepResearchIteration,
    config: DeepResearchConfig,
    memory: DeepResearchMemory,
    query: str,
    tool_call_id: str,
) -> str:
    """
    Execute complete web search workflow with multiple steps:
    1. Perform search
    2. Filter out already-analyzed URLs
    3. Analyze NEW results for relevance
    4. Process NEW relevant pages

    Returns a formatted summary for the conversation history.
    """
    # Update span with input details
    observability_context.update_current_span(
        input={
            "Query": query,
            "Already analyzed URLs": len(memory.analyzed_urls),
            "Already processed URLs": len(memory.processed_urls),
        }
    )

    # Validate query
    if not query:
        return "Error: No search query provided"

    # Step 1: Execute search
    search_step, raw_results = await _execute_search_step(
        config=config, memory=memory, query=query
    )
    current_iteration.steps.append(search_step)

    if search_step.error:
        return f"Search failed: {search_step.error}"

    if not raw_results:
        return "No search results found"

    # Step 2: Separate results into already-analyzed and new
    already_analyzed_processed = []  # Previously analyzed, found relevant, and processed
    already_analyzed_other = []  # Previously analyzed but not processed (were irrelevant)
    new_results = []  # Not yet analyzed

    for result in raw_results:
        url = result.get("url", "")
        if url in memory.analyzed_urls:
            # Already analyzed - check if it was processed (meaning it was relevant)
            if url in memory.processed_urls:
                already_analyzed_processed.append(result)
            else:
                already_analyzed_other.append(result)
        else:
            new_results.append(result)

    # Step 3: Analyze ONLY new results for relevance
    newly_relevant_results = []

    if new_results:
        relevance_step, newly_relevant_results = await _analyze_search_results(
            run=run, config=config, memory=memory, query=query, results=new_results
        )
        current_iteration.steps.append(relevance_step)

        # Mark all new results as analyzed
        for result in new_results:
            url = result.get("url", "")
            memory.analyzed_urls.add(url)

    # Step 4: Process newly relevant pages
    processed_summaries = []

    for result in newly_relevant_results:
        process_step = await _process_search_result(
            run=run, config=config, memory=memory, query=query, result=result
        )
        current_iteration.steps.append(process_step)

        # Add processed content to memory
        if not process_step.error:
            url = result.get("url", "")
            summary = ""
            if isinstance(process_step.details, ProcessPageStepDetails):
                summary = process_step.details.summary or ""

            # Mark URL as processed (meaning it was relevant)
            memory.processed_urls.add(url)

            # Store extracted info if relevant
            if summary and "no relevant" not in summary.lower():
                memory.extracted_info.append(summary)
                processed_summaries.append(
                    {
                        "title": result.get("title", "Unknown"),
                        "url": url,
                        "summary": summary,
                    }
                )

    # Step 5: Build formatted summary for conversation
    summary_parts = []

    # Header: total results breakdown
    summary_parts.append(
        f"Found {len(raw_results)} pages total. "
        f"{len(new_results)} new, {len(already_analyzed_processed) + len(already_analyzed_other)} already analyzed."
    )

    # If nothing new was found at all
    if not new_results:
        summary_parts.append(
            f"\n✓ All {len(raw_results)} results were already analyzed - no new information."
        )
        if already_analyzed_processed:
            summary_parts.append(
                f"\nAlready processed relevant pages ({len(already_analyzed_processed)}):"
            )
            for result in already_analyzed_processed:
                title = result.get("title", "Unknown")
                url = result.get("url", "")
                summary_parts.append(f"  - [{title}]({url})")
        return "\n".join(summary_parts)

    # Report newly analyzed results
    newly_relevant_count = len(newly_relevant_results)
    newly_irrelevant_count = len(new_results) - newly_relevant_count
    summary_parts.append(
        f"\nAnalyzed {len(new_results)} new results: "
        f"{newly_relevant_count} relevant, {newly_irrelevant_count} irrelevant."
    )

    # Report already processed pages (only if there are some)
    if already_analyzed_processed:
        summary_parts.append(
            f"\nAlready processed relevant pages ({len(already_analyzed_processed)}):"
        )
        for result in already_analyzed_processed:
            title = result.get("title", "Unknown")
            url = result.get("url", "")
            summary_parts.append(f"  - [{title}]({url})")

    # Report newly processed pages
    if processed_summaries:
        summary_parts.append(
            f"\nNewly processed relevant pages ({len(processed_summaries)}):"
        )
        for item in processed_summaries:
            summary_parts.append(f"  - [{item['title']}]({item['url']})")
            summary_parts.append(f"    {item['summary']}")
    elif newly_relevant_results:
        summary_parts.append(
            f"\n⚠ {len(newly_relevant_results)} relevant pages found but not processed (reached limit or error)."
        )

    final_summary = "\n".join(summary_parts)

    # Update span with output details
    observability_context.update_current_span(
        output={
            "Total results found": len(raw_results),
            "New results": len(new_results),
            "Newly relevant": len(newly_relevant_results),
            "Newly processed": len(processed_summaries),
            "Summary": final_summary[:500] + "..." if len(final_summary) > 500 else final_summary,
        }
    )

    return final_summary


@observe(name="Determine next action")
async def _execute_reasoning_step(
    run: DeepResearchRun,
    iteration: int,
    config: DeepResearchConfig,
    memory: DeepResearchMemory,
    allow_tools: bool = True,
) -> DeepResearchStep:
    """
    Execute agent reasoning step to decide next action.

    Args:
        allow_tools: If False, don't pass web_search tool (forces final report generation)
    """
    try:
        # Update span with input details
        observability_context.update_current_span(
            input={
                "Iteration": f"{iteration}/{config.max_iterations}",
                "Research query": run.input.get("query", ""),
                "Search queries so far": len(memory.search_queries),
                "Processed URLs": len(memory.processed_urls),
                "Extracted info items": len(memory.extracted_info),
                "Tools available": allow_tools,
            }
        )

        # Build template_values from input
        template_values = {
            **run.input,  # Spread all input variables
            "iteration": iteration,
            "max_iterations": config.max_iterations,
            "search_history": "\n".join(f"- {q}" for q in memory.search_queries),
            "extracted_info": "\n".join(f"- {info}" for info in memory.extracted_info),
            "processed_urls_count": len(memory.processed_urls),
        }

        # Define tool schemas for OpenAI function calling
        tools = None
        tool_choice = None

        if allow_tools:
            tools = [
                {
                    "type": "function",
                    "function": {
                        "name": "web_search",
                        "description": "Search the web for information to help answer the research question",
                        "parameters": {
                            "type": "object",
                            "properties": {
                                "query": {
                                    "type": "string",
                                    "description": "The search query to execute",
                                }
                            },
                            "required": ["query"],
                        },
                    },
                }
            ]
            tool_choice = "auto"
        else:
            # Max iterations reached - don't pass tools or tool_choice to force final report
            logger.info("Max iterations reached, forcing final report generation")

        # Execute reasoning prompt template with tool calling support
        # Pass full conversation history as additional messages
        result = await execute_prompt_template(
            system_name_or_config=config.reasoning_prompt,
            template_values=template_values,
            template_additional_messages=memory.conversation_history,
            tools=tools,
            tool_choice=tool_choice,
            parallel_tool_calls=config.parallel_tool_calls,
        )

        # Track usage and latency
        _track_usage(run, result)

        content = result.content
        tool_calls = result.tool_calls

        # Add to conversation history
        memory.conversation_history.append(
            {"role": "assistant", "tool_calls": tool_calls, "content": content}
        )

        decided_action = "final_report" if not tool_calls else "search"

        # Update span with output details
        output_data = {
            "Decision": decided_action,
            "Tool calls": len(tool_calls) if tool_calls else 0,
        }
        if tool_calls:
            output_data["Search queries"] = [
                tc.get("function", {}).get("arguments", "{}") for tc in tool_calls
            ]
        if content and decided_action == "final_report":
            output_data["Report preview"] = content[:200] + "..." if len(content) > 200 else content

        observability_context.update_current_span(output=output_data)

        step = DeepResearchStep(
            type=StepType.REASONING,
            title=f"Iteration {iteration}: Planning next action",
            details=ReasoningStepDetails(decided_action=decided_action),
            cost=result.cost if hasattr(result, "cost") else None,
            latency=result.latency if hasattr(result, "latency") else None,
            usage=result.usage if hasattr(result, "usage") else None,
        )

        return step

    except Exception as e:
        logger.exception(f"Reasoning step in iteration {iteration} failed")
        return DeepResearchStep(
            type=StepType.REASONING,
            title=f"Iteration {iteration}: Reasoning failed",
            details=ReasoningStepDetails(
                thought="Error occurred during reasoning", decided_action="error"
            ),
            error=str(e),
        )


@observe(name="Execute web search")
async def _execute_search_step(
    config: DeepResearchConfig, memory: DeepResearchMemory, query: str
) -> tuple[DeepResearchStep, list[dict]]:
    """Execute web search using Tavily API tool. Returns (step, results)."""
    try:
        # Update span with input details
        observability_context.update_current_span(
            input={
                "Query": query,
                "Max results": config.max_results,
            }
        )

        # Add query to memory
        memory.search_queries.append(query)

        # Call Tavily search tool via API server
        api_call = ApiToolCall(
            server="TAVILY",
            tool="search",
            input_params=ApiToolCallInputParams(
                requestBody={
                    "query": query,
                    "max_results": config.max_results,
                    "include_raw_content": True,
                }
            ),
        )

        response = await call_api_server_tool(api_call)

        # Parse response content (it's a JSON string)
        response_data = (
            json.loads(response.content)
            if isinstance(response.content, str)
            else response.content
        )

        # Parse Tavily response
        raw_results = (
            response_data.get("results", []) if isinstance(response_data, dict) else []
        )

        results = [
            {
                "title": r.get("title", ""),
                "url": r.get("url", ""),
                "content": r.get("content", ""),
                "snippet": r.get("content", ""),  # Use content as snippet
                "raw_content": r.get("raw_content", ""),
            }
            for r in raw_results
        ]

        # Initialize url_analysis entries for new URLs (will be updated after analysis)
        new_count = 0
        for r in results:
            url = r.get("url", "")
            if url and url not in memory.url_analysis:
                new_count += 1
                memory.url_analysis[url] = {
                    "title": r.get("title", ""),
                    "snippet": r.get("snippet", ""),
                    "raw_content": r.get("raw_content", ""),
                    "search_query": query,
                    "is_relevant": None,  # Will be set during analysis
                    "relevance_reasoning": None,
                    "processed": False,
                    "processing_summary": None,
                }

        # Update span with output details
        observability_context.update_current_span(
            output={
                "Total results": len(results),
                "New results": new_count,
                "URLs": [r.get("url", "") for r in results[:5]],  # First 5 URLs
            }
        )

        step = DeepResearchStep(
            type=StepType.SEARCH,
            title=f"Searching: '{query}'",
            details=SearchStepDetails(
                query=query, results_count=len(results), new_results_count=new_count
            ),
        )

        return step, results

    except Exception as e:
        logger.exception(f"Search step failed for query: {query}")
        step = DeepResearchStep(
            type=StepType.SEARCH,
            title=f"Search failed: '{query}'",
            details=SearchStepDetails(
                query=query, results_count=0, new_results_count=0
            ),
            error=str(e),
        )
        return step, []


@observe(name="Analyze search results")
async def _analyze_search_results(
    run: DeepResearchRun,
    config: DeepResearchConfig,
    memory: DeepResearchMemory,
    query: str,
    results: list[dict],
) -> tuple[DeepResearchStep, list[dict]]:
    """
    Analyze search results to determine which are relevant.
    Uses the analyze_search_results_prompt to filter results.
    Returns (step, relevant_results)
    """
    try:
        # Update span with input details
        observability_context.update_current_span(
            input={
                "Query": query,
                "Results to analyze": len(results),
                "Result titles": [r.get("title", "N/A") for r in results],
            }
        )

        # Format results for analysis (snippets only)
        results_text = "\n\n".join(
            [
                f"Result {i + 1}:\nTitle: {r.get('title', 'N/A')}\nURL: {r.get('url', 'N/A')}\nSnippet: {r.get('snippet', r.get('content', 'N/A'))}"
                for i, r in enumerate(results)
            ]
        )

        context = {
            "query": query,
            "results_count": len(results),
            "results": results_text,
        }

        result = await execute_prompt_template(
            system_name_or_config=config.analyze_search_results_prompt,
            template_values=context,
        )

        # Track usage and latency
        _track_usage(run, result)

        analysis = result.content

        # Parse relevant results with reasoning
        relevant_results = []
        try:
            parsed = SearchResultsAnalysis.model_validate_json(analysis)
            relevant_items = parsed.relevant_results
            relevant_urls = set()

            # Match URLs from analysis to actual result objects and attach reasoning
            for item in relevant_items:
                url = item.url
                reasoning = item.reasoning
                relevant_urls.add(url)

                # Find matching result
                for r in results:
                    if r.get("url") == url:
                        # Attach reasoning to the result object
                        result_with_reasoning = r.copy()
                        result_with_reasoning["relevance_reasoning"] = reasoning
                        relevant_results.append(result_with_reasoning)

                        # Update url_analysis in memory
                        if url in memory.url_analysis:
                            memory.url_analysis[url]["is_relevant"] = True
                            memory.url_analysis[url]["relevance_reasoning"] = reasoning
                        break

            # Mark all analyzed URLs (including irrelevant ones)
            for r in results:
                url = r.get("url", "")
                memory.analyzed_urls.add(url)

                # Mark irrelevant URLs (no reasoning available from LLM)
                if url not in relevant_urls and url in memory.url_analysis:
                    memory.url_analysis[url]["is_relevant"] = False

        except json.JSONDecodeError as e:
            # Fail fast: expected JSON format from relevance analysis
            error_msg = f"Relevance analysis must return valid JSON. Parse error: {e}. Content preview: {analysis}"
            logger.error(error_msg)
            step = DeepResearchStep(
                type=StepType.ANALYZE_RESULTS,
                title=f"Analysis failed for {len(results)} results",
                details=AnalyzeResultsStepDetails(
                    analyzed_count=len(results), relevant_count=0, relevant_urls=[]
                ),
                error=error_msg,
                cost=result.cost if hasattr(result, "cost") else None,
                latency=result.latency if hasattr(result, "latency") else None,
                usage=result.usage if hasattr(result, "usage") else None,
            )
            return step, []

        # Update span with output details
        observability_context.update_current_span(
            output={
                "Analyzed": len(results),
                "Relevant": len(relevant_results),
                "Irrelevant": len(results) - len(relevant_results),
                "Relevant URLs": [r.get("url", "") for r in relevant_results],
            }
        )

        step = DeepResearchStep(
            type=StepType.ANALYZE_RESULTS,
            title=f"Analyzed {len(results)} results: {len(relevant_results)} relevant",
            details=AnalyzeResultsStepDetails(
                analyzed_count=len(results),
                relevant_count=len(relevant_results),
                relevant_urls=[r.get("url", "") for r in relevant_results],
            ),
            cost=result.cost if hasattr(result, "cost") else None,
            latency=result.latency if hasattr(result, "latency") else None,
            usage=result.usage if hasattr(result, "usage") else None,
        )

        return step, relevant_results

    except Exception as e:
        logger.exception("Analyze search results failed")
        step = DeepResearchStep(
            type=StepType.ANALYZE_RESULTS,
            title=f"Analysis error for {len(results)} results",
            details=AnalyzeResultsStepDetails(
                analyzed_count=len(results), relevant_count=0, relevant_urls=[]
            ),
            error=str(e),
        )
        return step, []


@observe(name="Process search result")
async def _process_search_result(
    run: DeepResearchRun,
    config: DeepResearchConfig,
    memory: DeepResearchMemory,
    query: str,
    result: dict,
) -> DeepResearchStep:
    """
    Process individual search result page content.
    Uses the process_search_result_prompt to extract relevant information.
    """
    url = result.get("url", "")
    title = result.get("title", "Unknown")

    try:
        # Get page content (raw_content if available, otherwise snippet)
        page_content = (
            result.get("raw_content")
            or result.get("content")
            or result.get("snippet", "")
        )

        # Update span with input details
        observability_context.update_current_span(
            input={
                "URL": url,
                "Title": title,
                "Content length": len(page_content),
                "Relevance reasoning": result.get("relevance_reasoning", "N/A"),
            }
        )

        if not page_content:
            return DeepResearchStep(
                type=StepType.PROCESS_PAGE,
                title=f"Skipped: {title}",
                details=ProcessPageStepDetails(
                    url=url, page_title=title, summary="No content available"
                ),
            )

        # Limit content length
        page_content = page_content

        # Get relevance reasoning from analysis step
        relevance_reasoning = result.get("relevance_reasoning", "")

        context = {
            "query": query,
            "research_query": run.input.get("query", ""),
            "page_title": title,
            "page_url": url,
            "page_content": page_content,
            "relevance_reasoning": relevance_reasoning,
            "extracted_info": "\n".join(f"- {info}" for info in memory.extracted_info),
        }

        # Execute process search result prompt
        result_data = await execute_prompt_template(
            system_name_or_config=config.process_search_result_prompt,
            template_values=context,
        )

        # Track usage and latency
        _track_usage(run, result_data)

        summary = result_data.content

        # Update url_analysis in memory
        if url in memory.url_analysis:
            memory.url_analysis[url]["processed"] = True
            memory.url_analysis[url]["processing_summary"] = summary

        # Update span with output details
        observability_context.update_current_span(
            output={
                "Summary": summary[:300] + "..." if len(summary) > 300 else summary,
                "Summary length": len(summary),
            }
        )

        return DeepResearchStep(
            type=StepType.PROCESS_PAGE,
            title=f"Processed: {title}",
            details=ProcessPageStepDetails(
                url=url,
                page_title=title,
                summary=summary if len(summary) > 500 else summary,  # Limit for display
            ),
            cost=result_data.cost if hasattr(result_data, "cost") else None,
            latency=result_data.latency if hasattr(result_data, "latency") else None,
            usage=result_data.usage if hasattr(result_data, "usage") else None,
        )

    except Exception as e:
        logger.exception(f"Process search result failed for {url}")
        return DeepResearchStep(
            type=StepType.PROCESS_PAGE,
            title=f"Failed: {title}",
            details=ProcessPageStepDetails(
                url=url, page_title=title, summary="Processing failed"
            ),
            error=str(e),
        )


def _resolve_webhook_template(
    run: DeepResearchRun, template: dict[str, Any]
) -> dict[str, Any]:
    """
    Resolve webhook payload template by navigating paths from the run object.

    All paths are relative to the run object:
    - "run_id" → run.run_id
    - "client_id" → run.client_id
    - "input.field_name" → run.input.field_name
    - "result.field_name" → run.result.field_name
    - "result.nested.field" → run.result.nested.field

    Args:
        run: The research run
        template: Template dict with path references as values

    Returns:
        Resolved payload dict with actual values
    """

    def resolve_path(path: str | dict | list) -> Any:
        """Recursively resolve a path or nested structure."""
        if isinstance(path, dict):
            # Recursively resolve nested dicts
            return {k: resolve_path(v) for k, v in path.items()}
        elif isinstance(path, list):
            # Recursively resolve lists
            return [resolve_path(item) for item in path]
        elif not isinstance(path, str):
            # Return non-string values as-is
            return path

        # Navigate from run object using dot notation
        value = run
        for key in path.split("."):
            if isinstance(value, dict):
                value = value.get(key)
            elif hasattr(value, key):
                value = getattr(value, key)
            else:
                return None

            if value is None:
                return None

        return value

    return resolve_path(template)


async def _call_webhook(run: DeepResearchRun, config: DeepResearchConfig) -> None:
    """Call webhook API tool to notify completion and store call details."""
    webhook_details = WebhookCallDetails(
        api_server=config.webhook.api_server,
        api_tool=config.webhook.api_tool,
        success=False,
    )

    try:
        if not config.webhook or not config.webhook.enabled:
            logger.info(f"No webhook configured for run {run.run_id}, skipping")
            return

        if not config.webhook.api_server or not config.webhook.api_tool:
            webhook_details.error_message = "Missing api_server or api_tool"
            run.webhook_call = webhook_details
            logger.warning(
                f"Webhook enabled but missing api_server or api_tool for run {run.run_id}"
            )
            return

        payload = {}
        if config.webhook.payload_template:
            # Build payload by resolving template paths
            payload = _resolve_webhook_template(run, config.webhook.payload_template)

        webhook_details.request_payload = payload

        logger.info(
            f"Calling webhook for run {run.run_id}: {config.webhook.api_server}/{config.webhook.api_tool}"
        )
        logger.debug(f"Webhook payload: {json.dumps(payload, indent=2)}")

        api_call = ApiToolCall(
            server=config.webhook.api_server,
            tool=config.webhook.api_tool,
            input_params=ApiToolCallInputParams(
                requestBody=payload if payload else None
            ),
        )

        result = await call_api_server_tool(api_call)

        # Capture response details
        webhook_details.success = True
        webhook_details.response_status = 200  # Assuming success means 200
        webhook_details.response_body = (
            result if isinstance(result, dict) else {"data": str(result)}
        )

        logger.info(f"Webhook called successfully for run {run.run_id}")

    except Exception as e:
        webhook_details.success = False
        webhook_details.error_message = str(e)
        logger.warning(f"Failed to call webhook for run {run.run_id}: {e}")

    finally:
        # Always store webhook call details
        run.webhook_call = webhook_details


def _serialize_memory(memory: DeepResearchMemory) -> dict[str, Any]:
    """Convert memory to a JSON-serializable structure."""
    data = memory.model_dump(mode="json")
    data["analyzed_urls"] = list(memory.analyzed_urls)
    data["processed_urls"] = list(memory.processed_urls)
    return data


def _serialize_run_details(run: DeepResearchRun) -> dict[str, Any]:
    """Build details payload for persistence."""
    return {
        "memory": _serialize_memory(run.memory),
        "iterations": [
            iteration.model_dump(mode="json") for iteration in run.iterations
        ],
        "result": run.result,
        "error": run.error,
        "webhook_call": run.webhook_call.model_dump(mode="json")
        if run.webhook_call
        else None,
        "total_usage": run.total_usage,
        "total_latency": run.total_latency,
        "total_cost": run.total_cost,
    }


def _map_db_run_to_service(db_run: "DeepResearchRunDB") -> DeepResearchRun:
    """Hydrate service-layer run model from database entity."""
    details = db_run.details or {}
    memory_data = details.get("memory") or {}
    iterations_data = details.get("iterations") or []
    result = details.get("result")
    error = details.get("error")
    webhook_call_data = details.get("webhook_call")
    total_usage = details.get("total_usage")
    total_latency = details.get("total_latency")
    total_cost = details.get("total_cost")

    try:
        status = DeepResearchStatus(db_run.status)
    except ValueError:
        logger.warning("Unknown run status '%s', defaulting to pending", db_run.status)
        status = DeepResearchStatus.PENDING

    try:
        config_model = DeepResearchConfig.model_validate(db_run.config or {})
    except Exception:
        logger.exception("Failed to load config for run %s; using defaults", db_run.id)
        config_model = DeepResearchConfig()

    memory_model = (
        DeepResearchMemory.model_validate(memory_data)
        if memory_data
        else DeepResearchMemory()
    )
    iterations = [
        DeepResearchIteration.model_validate(item) for item in iterations_data
    ]

    webhook_call_model = (
        WebhookCallDetails.model_validate(webhook_call_data)
        if webhook_call_data
        else None
    )

    return DeepResearchRun(
        run_id=str(db_run.id),
        config_id=None,
        config_system_name=db_run.config_system_name,
        client_id=db_run.client_id,
        status=status,
        config=config_model,
        input=db_run.input or {},
        memory=memory_model,
        iterations=iterations,
        result=result,
        error=error,
        webhook_call=webhook_call_model,
        total_usage=total_usage,
        total_latency=total_latency,
        total_cost=total_cost,
        created_at=db_run.created_at,
        updated_at=db_run.updated_at,
    )


async def _persist_run_state(
    run_service: DeepResearchRunService,
    run_state: DeepResearchRun,
) -> None:
    """Persist current run status and details to the database."""
    details = _serialize_run_details(run_state)
    update = DeepResearchRunUpdateSchema(
        status=run_state.status.value,
        details=details,
    )
    await run_service.update(update, item_id=UUID(run_state.run_id), auto_commit=True)


@observe(
    name="Deep research workflow",
    description="Execute deep research workflow for a research run",
    channel="production",
    source="Runtime AI App",
)
async def run_deep_research_workflow(run_id: str | UUID) -> None:
    """Orchestrate deep research execution for a persisted run."""

    run_uuid = UUID(str(run_id))

    try:
        async with alchemy.get_session() as session:
            run_service = DeepResearchRunService(session=session)
            db_run = await run_service.get(run_uuid)
            run_model = _map_db_run_to_service(db_run)

            # Import here to avoid circular dependency
            from services.observability import observability_context

            # Update trace with deep research context
            observability_context.update_current_trace(
                name="Deep Research",
                type="deep_research"
            )

            async def persist(run_state: DeepResearchRun) -> None:
                await _persist_run_state(run_service, run_state)

            await execute_deep_research(run_model, persist_callback=persist)

            # Ensure final state is flushed even if last persist failed
            await _persist_run_state(run_service, run_model)
    except Exception:
        logger.exception("Failed to execute deep research workflow for run %s", run_id)

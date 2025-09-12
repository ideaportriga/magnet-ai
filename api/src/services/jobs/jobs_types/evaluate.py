import asyncio
import logging
import uuid
from datetime import datetime, timezone
from enum import Enum, StrEnum
from typing import Optional

from core.config.app import alchemy
from core.domain.evaluation_sets.service import EvaluationSetsService
from core.domain.evaluations.service import EvaluationsService
from core.domain.prompts.service import PromptsService
from core.domain.rag_tools.service import RagToolsService
from open_ai.utils_new import create_chat_completion_from_prompt_template
from prompt_templates.prompt_templates import get_prompt_template_by_system_name_flat
from services.observability import observability_context, observe
from services.rag_tools import execute_rag_tool

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class JobRunStatus(Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class JobType(StrEnum):
    RAG_EVAL = "rag_eval"
    PROMPT_EVAL = "prompt_eval"


# Retrieve variant configuration object using SQLAlchemy
async def get_tool_config(
    job_type: JobType, system_name: str, variant: Optional[str] = None
) -> dict:
    async with alchemy.get_session() as session:
        if job_type == JobType.PROMPT_EVAL:
            service = PromptsService(session=session)
            results = await service.list(system_name=system_name)
        else:
            service = RagToolsService(session=session)
            results = await service.list(system_name=system_name)

        for document in results:
            variant = variant or document.active_variant
            name = document.name
            id = str(document.id)
            description = document.description
            variant_object = next(
                (v for v in (document.variants or []) if v.get("variant") == variant),
                {},
            )
            return {
                "variant_object": variant_object,
                "name": name,
                "description": description,
                "id": id,
            }
    return {}


async def create_evaluation_record(
    job_id, job_type, system_name, variant, test_set_system_names
):
    # Retrieve particular variant of the tool config
    tool_variant_config = await get_tool_config(job_type, system_name, variant)

    variant_object = tool_variant_config.get("variant_object")
    name = tool_variant_config.get("name")
    description = tool_variant_config.get("description")
    id = tool_variant_config.get("id")

    # Initialize evaluation record
    evaluation_data = {
        "job_id": job_id,
        "type": job_type,
        "tool": {
            "id": id,
            "name": name,
            "description": description,
            "system_name": system_name,
            "variant_name": variant,
            "variant_object": variant_object,
        },
        "test_sets": test_set_system_names,
        "started_at": datetime.now(timezone.utc),
        "status": JobRunStatus.IN_PROGRESS.value,
        "errors": [],
        "finished_at": None,
        "results": [],
    }

    # Insert evaluation record in the database using SQLAlchemy
    try:
        logger.info(
            f"About to create evaluation with data types: "
            f"started_at={type(evaluation_data['started_at'])}, "
            f"finished_at={type(evaluation_data['finished_at'])}"
        )
        logger.info(f"Started_at value: {evaluation_data['started_at']}")
        logger.info(f"Finished_at value: {evaluation_data['finished_at']}")

        async with alchemy.get_session() as session:
            evaluations_service = EvaluationsService(session=session)
            # Use the evaluation_data dict as the data parameter
            evaluation = await evaluations_service.create(data=evaluation_data)
            await session.commit()

        logger.info(f"Evaluation ID created: {evaluation.id}")
        return evaluation.id, evaluation_data
    except Exception as e:
        logger.error(f"Failed to create evaluation record: {e}")
        logger.error(f"Exception type: {type(e).__name__}")
        logger.error(f"Exception args: {e.args}")
        if hasattr(e, "__cause__") and e.__cause__:
            logger.error(f"Caused by: {e.__cause__}")
        logger.error(f"Evaluation data: {evaluation_data}")
        import traceback

        logger.error(f"Full traceback: {traceback.format_exc()}")
        raise


# Function to execute RAG tool for test set item
async def execute_test_set_item_rag_tool(rag_tool_config: dict, user_input: str) -> str:
    logger.info(
        f"Executing RAG tool with config keys: {list(rag_tool_config.keys()) if rag_tool_config else 'None'}"
    )
    logger.info(f"RAG tool config: {rag_tool_config}")
    logger.info(f"User input: {user_input}")

    rag_tool_test_result = await execute_rag_tool(
        system_name_or_config=rag_tool_config,
        user_message=user_input,
    )

    logger.info(f"RAG tool execution completed. Answer: {rag_tool_test_result.answer}")
    logger.info(f"RAG tool result type: {type(rag_tool_test_result)}")

    return rag_tool_test_result.answer


# Perform the actual evaluation based on job type
async def evaluate_record(job_type, system_name, variant, config, user_message) -> dict:
    logger.info(f"Starting evaluation record for job type '{job_type}'")
    start_time = datetime.now()
    match job_type:
        # Evaluate a prompt template
        case JobType.PROMPT_EVAL:
            prompt_template_config = await get_prompt_template_by_system_name_flat(
                system_name,
                variant,
            )
            chat_completion, _ = await create_chat_completion_from_prompt_template(
                prompt_template_config=prompt_template_config,
                additional_messages=[
                    {
                        "role": "user",
                        "content": user_message,
                    },
                ],
            )
            latency = (datetime.now() - start_time).total_seconds() * 1000
            answer = chat_completion.choices[0].message.content
            usage = chat_completion.usage
            model_version = chat_completion.model

            usage = {
                "completion_tokens": usage.completion_tokens if usage else 0,
                "prompt_tokens": usage.prompt_tokens if usage else 0,
            }

            result = {
                "answer": answer,
                "latency": latency,
                "usage": usage,
                "model_version": model_version,
            }

            return result

        # Evaluate a RAG tool
        case JobType.RAG_EVAL:
            logger.info(f"Evaluating RAG tool with config: {config}")
            logger.info(f"User message for RAG: {user_message}")

            answer = await execute_test_set_item_rag_tool(
                rag_tool_config=config,
                user_input=user_message,
            )

            logger.info(f"RAG tool returned answer: {answer}")

            latency = (datetime.now() - start_time).total_seconds() * 1000
            logger.info(f"RAG evaluation latency: {latency}ms")

            result = {"answer": answer, "latency": latency}
            logger.info(f"Final RAG result: {result}")
            return result

    return {}


# Function to handle individual variant evaluation
@observe(name="Evaluate variant", description="Evaluate particular variant of a tool.")
async def evaluate_variant(
    evaluation_id,
    evaluation_record,
    job_type,
    system_name,
    test_set_system_names,
    iteration_count,
    batch_size=5,
):
    variant = evaluation_record.get("tool").get("variant_name")
    variant_object = evaluation_record.get("tool").get("variant_object")

    total_records = 0
    for test_set in test_set_system_names:
        async with alchemy.get_session() as session:
            evaluation_sets_service = EvaluationSetsService(session=session)
            evaluation_set_configs = await evaluation_sets_service.list(
                system_name=test_set
            )
            if evaluation_set_configs:
                evaluation_set_config = evaluation_set_configs[0]
                total_records += len(evaluation_set_config.items or [])

    observability_context.update_current_span(
        input={
            "Variant": variant,
            "Number of iterations": iteration_count,
            "Number of test sets": len(test_set_system_names),
            "Total number of test set records": total_records,
        }
    )

    try:
        # Function to evaluate a single test set item
        @observe(description="Evaluate a single record from a test set.")
        async def evaluate_test_set_item(
            iteration, test_set_index, item_index, test_set, test_set_item
        ):
            logger.info(
                f"Starting evaluation for iteration {iteration}, test_set_index {test_set_index}, item_index {item_index}"
            )

            user_message = test_set_item.get("user_input")
            expected_output = test_set_item.get("expected_result")

            logger.info(f"User message: {user_message}")
            logger.info(f"Expected output: {expected_output}")

            observability_context.update_current_span(
                name=f"Iteration #{iteration}.{test_set_index}.{item_index} - Run",
                input={
                    "Iteration": iteration,
                    "Test set": test_set,
                    "Evaluation input": user_message,
                    "Expected output": expected_output,
                },
            )

            # Perform evaluation
            logger.info(
                f"Calling evaluate_record with job_type={job_type}, system_name={system_name}, variant={variant}"
            )
            result = await evaluate_record(
                job_type, system_name, variant, variant_object, user_message
            )
            logger.info(f"Evaluation result: {result}")

            generated_output = result.get("answer", "")
            latency = result.get("latency", 0)
            usage = result.get("usage", {})
            model_version = result.get("model_version", "")

            # Construct the result record
            result_record = {
                "id": str(uuid.uuid4()),
                "model_version": model_version,
                "usage": usage,
                "latency": latency,
                "generated_output": generated_output,
                "test_set": test_set,
                "evaluated_at": datetime.now(timezone.utc),
                "expected_output": expected_output,
                "user_message": user_message,
                "iteration": iteration,
            }

            logger.info(f"Created result record with ID: {result_record['id']}")

            # Return the result record instead of saving it immediately
            logger.info("Returning result record for later batch save")
            return result_record

        # Execute iterations with batch processing
        tasks = []
        for iteration in range(1, iteration_count + 1):
            for test_set_index, test_set in enumerate(test_set_system_names):
                async with alchemy.get_session() as session:
                    evaluation_sets_service = EvaluationSetsService(session=session)
                    evaluation_set_configs = await evaluation_sets_service.list(
                        system_name=test_set
                    )

                # Check if test set config exists
                if not evaluation_set_configs:
                    evaluation_record["errors"].append(
                        f"Test set '{test_set}' not found"
                    )
                    continue

                evaluation_set_config = evaluation_set_configs[0]
                # Get test set items and process in batches
                test_set_items = evaluation_set_config.items or []
                for i in range(0, len(test_set_items), batch_size):
                    batch = test_set_items[i : i + batch_size]
                    for item_index, item in enumerate(batch):
                        tasks.append(
                            evaluate_test_set_item(
                                iteration,
                                test_set_index + 1,
                                i + item_index + 1,
                                test_set,
                                item,
                            )
                        )

        # Execute all tasks concurrently and collect results
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Collect all successful results
        all_result_records = []
        for result in results:
            if isinstance(result, dict) and "id" in result:
                all_result_records.append(result)
            elif isinstance(result, Exception):
                logger.error(f"Task failed with exception: {result}")
                evaluation_record["errors"].append(str(result))

        # Update evaluation status to completed
        evaluation_record["finished_at"] = datetime.now(timezone.utc)
        evaluation_record["status"] = JobRunStatus.COMPLETED.value

        # Final update of the evaluation record using SQLAlchemy with all results at once
        async with alchemy.get_session() as session:
            evaluations_service = EvaluationsService(session=session)

            # Get current evaluation to preserve any existing results
            evaluation = await evaluations_service.get(evaluation_id)
            if evaluation:
                current_results = evaluation.results or []
                current_results.extend(all_result_records)

                await evaluations_service.update(
                    item_id=str(evaluation_id),  # Convert UUID to string for item_id
                    data={
                        "status": evaluation_record["status"],
                        "finished_at": evaluation_record["finished_at"],
                        "errors": evaluation_record["errors"],
                        "results": current_results,
                    },
                )
                await session.commit()
                logger.info(
                    f"Final update: evaluation {evaluation_id} now has {len(current_results)} results"
                )
    except Exception as e:
        logger.error(f"Error during evaluation processing: {e}")


# Main evaluation function
async def evaluate(job_data) -> dict:
    job_id = str(job_data.get("_id"))
    job_type = job_data.get("type")
    config = job_data.get("config")
    iteration_count = job_data.get("iteration_count")

    async def start_new_thread(system_name: str, test_set_system_names, variants):
        try:
            evaluation_records = [
                await create_evaluation_record(
                    job_id, job_type, system_name, variant, test_set_system_names
                )
                for variant in variants
            ]

            # Execute the evaluation process directly
            await evaluate_tool(
                system_name=system_name,
                test_set_system_names=test_set_system_names,
                evaluation_records=evaluation_records,
            )

            return [str(evaluation_id) for evaluation_id, _ in evaluation_records]
        except Exception as e:
            # Log error with line number and detailed information
            line_number = e.__traceback__.tb_lineno if e.__traceback__ else -1
            logger.error(
                f"Error running evaluation for '{system_name}': {e} (Line {line_number})"
            )
            logger.error(f"Exception type: {type(e).__name__}")
            logger.error(f"Exception args: {e.args}")
            if hasattr(e, "__cause__") and e.__cause__:
                logger.error(f"Caused by: {e.__cause__}")
            import traceback

            logger.error(f"Full traceback: {traceback.format_exc()}")

            # Return a failed evaluation record
            return [
                {
                    "job_id": job_id,
                    "type": job_type,  # job_type is already a string
                    "system_name": system_name,
                    "test_sets": test_set_system_names,
                    "started_at": datetime.utcnow(),
                    "status": JobRunStatus.FAILED.value,
                    "finished_at": datetime.utcnow(),
                    "results": [],
                    "variant_object": {},
                }
            ]

    @observe(name="Run evaluation", channel="evaluation", source="Evaluation")
    async def evaluate_tool(
        system_name: str, test_set_system_names, evaluation_records
    ):
        tool_config = await get_tool_config(job_type, system_name)

        observability_context.update_current_trace(
            name=tool_config.get("name"),
            type="rag" if job_type == JobType.RAG_EVAL else "prompt-template",
        )

        # Use asyncio.gather to evaluate each variant in parallel
        tasks = []
        for evaluation_id, record in evaluation_records:
            tasks.append(
                evaluate_variant(
                    evaluation_id,
                    record,
                    job_type,
                    system_name,
                    test_set_system_names,
                    iteration_count,
                )
            )

        # Execute all evaluation tasks concurrently
        await asyncio.gather(*tasks, return_exceptions=True)

    try:
        evaluation_ids = []
        for config_item in config:
            evaluation_ids.extend(
                await start_new_thread(
                    config_item["system_name"],
                    config_item["test_set_system_names"],
                    config_item["variants"],
                )
            )

        # Insert all evaluation records into the database
        if evaluation_ids and len(evaluation_ids) > 0:
            return {
                "status": JobRunStatus.COMPLETED.value,
                "evaluation_records": evaluation_ids,
            }
        logger.warning("No evaluation records were created.")
        return {"status": JobRunStatus.FAILED.value}
    except Exception as e:
        line_number = e.__traceback__.tb_lineno if e.__traceback__ else -1
        logger.error(f"An error occurred during evaluation: {e} (Line {line_number})")
        return {"status": JobRunStatus.FAILED.value}

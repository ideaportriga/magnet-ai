import asyncio
import copy
from enum import StrEnum
from logging import getLogger

from bson import ObjectId
from pydantic import BaseModel

from open_ai.utils_new import create_chat_completion_from_prompt_template
from prompt_templates.prompt_templates import transform_to_flat
from services.rag_tools import execute_rag_tool
from stores import get_db_client
from utils.datetime_utils import utc_now_isoformat

client = get_db_client()

evaluation_job_collection = client.get_collection("evaluation_jobs")

logger = getLogger(__name__)


class EvaluationSetItem(BaseModel):
    user_input: str
    expected_result: str | None = None


class EvaluationSetType(StrEnum):
    RAG_TOOL = "rag_tool"
    PROMPT_TEMPLATE = "prompt_template"


class EvaluationSetConfig(BaseModel):
    system_name: str
    name: str
    description: str
    type: EvaluationSetType
    items: list[EvaluationSetItem] | None = (
        None  # During the creation of a record in the popup, it is not possible to immediately add items.
    )


class EvaluationRunStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


async def create_evaluation_job(
    evaluation_set: str,
    iteration_count: int,
    evaluation_target_tools: list[str] | None = None,
    evaluation_target_tools_variants: list[str] | None = None,
) -> dict:
    assert evaluation_target_tools, "Evaluation target tools not selected"

    evaluation_set_config = await client.get_collection("evaluation_sets").find_one(
        {"system_name": evaluation_set},
    )

    assert evaluation_set_config, "Evaluation set config not found"

    evaluation_set_config = EvaluationSetConfig(**evaluation_set_config)

    assert evaluation_set_config.items, "No evaluation set items"

    evaluation_job_id = await insert_evaluation_job(
        evaluation_set_config=evaluation_set_config,
    )

    logger.info(f"{evaluation_set_config.type=}")

    evaluation_target_tool_configs = await get_evaluation_target_tool_configs(
        system_names=evaluation_target_tools,
        evaluation_set_type=evaluation_set_config.type,
        variants=evaluation_target_tools_variants,
    )

    asyncio.create_task(
        run_evaluation_job(
            job_id=evaluation_job_id,
            evaluation_set_config=evaluation_set_config,
            evaluation_target_tool_configs=evaluation_target_tool_configs,
            iteration_count=iteration_count,
        ),
    )

    return {"id": evaluation_job_id}


async def get_evaluation_target_tool_configs(
    system_names: list[str],
    evaluation_set_type: EvaluationSetType,
    variants,
) -> list[dict]:
    evaluation_target_tool_configs = None

    match evaluation_set_type:
        case EvaluationSetType.RAG_TOOL:
            evaluation_target_tool_configs = await get_rag_tool_configs(
                system_names,
                variants,
            )

        case EvaluationSetType.PROMPT_TEMPLATE:
            evaluation_target_tool_configs = await get_prompt_template_configs(
                system_names,
                variants,
            )

        case _:
            raise ValueError("Test set type not supported")

    assert evaluation_target_tool_configs, "Missing evaluation target tool(s)"

    return evaluation_target_tool_configs


async def list_evaluation_jobs() -> list[dict]:
    cursor = evaluation_job_collection.find()
    entities = []
    async for document in cursor:
        entities.append({"id": str(document.pop("_id")), **document})

    return entities


async def get_evaluation_job(job_id: str) -> dict | None:
    document = await evaluation_job_collection.find_one({"_id": ObjectId(job_id)})

    if not document:
        return None

    document = {"id": str(document.pop("_id")), **document}

    return document


async def run_evaluation_job(
    job_id: str,
    evaluation_set_config: EvaluationSetConfig,
    evaluation_target_tool_configs: list[dict],
    iteration_count: int,
):
    job_filter = {"_id": ObjectId(job_id)}

    evaluation_set_type = evaluation_set_config.type
    evaluation_set_items = evaluation_set_config.items or []

    logger.info(f"{job_id=}, {len(evaluation_set_items)} items")

    try:
        for index, test_set_item in enumerate(evaluation_set_items):
            logger.info(
                f"Execute item #{index + 1}/{len(evaluation_set_items)} {job_id=}",
            )
            user_message = test_set_item.user_input
            expected_result = test_set_item.expected_result

            for evaluation_target_tool_config in evaluation_target_tool_configs:
                evaluated_tool_system_name = evaluation_target_tool_config.get(
                    "system_name",
                )

                for iteration in range(iteration_count):
                    answer = None

                    match evaluation_set_type:
                        case EvaluationSetType.PROMPT_TEMPLATE:
                            answer = await execute_test_set_item_prompt_template(
                                prompt_template_config=evaluation_target_tool_config,
                                user_input=user_message,
                            )

                        case EvaluationSetType.RAG_TOOL:
                            answer = await execute_test_set_item_rag_tool(
                                rag_tool_config=evaluation_target_tool_config,
                                user_input=user_message,
                            )

                    result_item = {
                        "iteration": iteration + 1,
                        "answer": answer,
                        "user_input": user_message,
                        "expected_result": expected_result,
                        "evaluated_tool_system_name": evaluated_tool_system_name,
                        "variant": evaluation_target_tool_config.get("active_variant"),
                    }

                    await evaluation_job_collection.update_one(
                        job_filter,
                        {"$push": {"result_items": result_item}},
                    )

        status = EvaluationRunStatus.COMPLETED

    except Exception as err:
        logger.error("Failed to search: %s", err)
        status = EvaluationRunStatus.FAILED

    await evaluation_job_collection.update_one(
        job_filter,
        {
            "$set": {
                "finished_at": utc_now_isoformat(),
                "status": status,
                "evaluated_tools": evaluation_target_tool_configs,
            },
        },
    )
    logger.info(f"Finished {job_id=}")


async def execute_test_set_item_prompt_template(
    prompt_template_config: dict,
    user_input: str,
) -> str:
    chat_completion, _ = await create_chat_completion_from_prompt_template(
        prompt_template_config=prompt_template_config,
        additional_messages=[
            {
                "role": "user",
                "content": user_input,
            },
        ],
    )

    return str(chat_completion.choices[0].message.content)


async def execute_test_set_item_rag_tool(rag_tool_config: dict, user_input: str) -> str:
    rag_tool_test_result = await execute_rag_tool(
        system_name_or_config=rag_tool_config,
        user_message=user_input,
    )

    return rag_tool_test_result.answer


async def get_prompt_template_configs(
    system_names: list[str],
    variants: list[str],
) -> list[dict]:
    prompt_template_cursor = client.get_collection("prompts").find(
        {"system_name": {"$in": system_names}},
    )
    prompt_template_configs = []

    async for document in prompt_template_cursor:
        base_config = {"id": str(document.pop("_id")), **document}

        for variant in variants:
            flat_config = transform_to_flat(copy.deepcopy(base_config), variant)
            prompt_template_configs.append(flat_config)

    return prompt_template_configs


async def get_rag_tool_configs(
    system_names: list[str], variants: list[str]
) -> list[dict]:
    rag_tool_configs_cursor = client.get_collection("rag_tools").find(
        {"system_name": {"$in": system_names}},
    )
    rag_tool_configs = []

    async for document in rag_tool_configs_cursor:
        base_config = {"id": str(document.pop("_id")), **document}

        for variant in variants:
            flat_config = transform_to_flat(copy.deepcopy(base_config), variant)
            rag_tool_configs.append(flat_config)

    return rag_tool_configs


async def insert_evaluation_job(evaluation_set_config: EvaluationSetConfig) -> str:
    evaluation_job = {
        "started_at": utc_now_isoformat(),
        "status": EvaluationRunStatus.IN_PROGRESS,
        "evaluation_set": {
            "system_name": evaluation_set_config.system_name,
            "name": evaluation_set_config.name,
            "type": evaluation_set_config.type,
        },
        "result_items": [],
    }

    evaluation_job_create_result = await evaluation_job_collection.insert_one(
        evaluation_job
    )
    evaluation_job_id = str(evaluation_job_create_result.inserted_id)

    return evaluation_job_id

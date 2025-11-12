import asyncio
import logging
import traceback
from datetime import datetime
from enum import StrEnum
from typing import Any

from services.jobs.jobs_types.evaluate import evaluate
from stores import get_db_client

# Initialize logging
logging.basicConfig(level=logging.INFO)
client = get_db_client()
jobs_collection = client.get_collection("jobs")


# Enums for Job Status and Type
class JobRunStatus(StrEnum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


class JobType(StrEnum):
    RAG_EVAL = "rag_eval"
    PROMPT_EVAL = "prompt_eval"


class ParallelExecutionType(StrEnum):
    THREADS = "threads"  # Use threads for parallel execution
    INNNER = "inner"  # Use parallel execution iteration inside the job function
    NONE = "none"  # Do not use parallel execution


async def run_job(data) -> dict[str, Any]:
    # Create a job record
    job_record = {
        "started_at": datetime.utcnow(),
        "status": JobRunStatus.IN_PROGRESS,
        "type": data.type,
        "iteration_count": data.iteration_count,
        "config": data.config,
        "result_entity": data.result_entity,
    }
    job_id = (await jobs_collection.insert_one(job_record)).inserted_id

    if not job_id:
        return {"error": "Failed to create job record"}
    job_record["_id"] = job_id

    # Select job function
    if data.type in {JobType.RAG_EVAL, JobType.PROMPT_EVAL}:
        job_function = evaluate
    else:
        await jobs_collection.update_one(
            {"_id": job_id},
            {"$set": {"status": JobRunStatus.FAILED, "finished_at": datetime.utcnow()}},
        )
        return {"error": "Unsupported job type"}

    execution_type = getattr(data, "execution_type", ParallelExecutionType.INNNER)
    # Choose execution mode based on parallel_execution flag
    if execution_type == ParallelExecutionType.INNNER:
        results = await job_function(job_record)
    elif execution_type == ParallelExecutionType.THREADS:
        tasks = [
            asyncio.create_task(job_function(job_record, iteration))
            for iteration in range(1, data.iteration_count + 1)
        ]
        results = await handle_futures(tasks, job_id)
    else:
        results = []
        for iteration in range(1, data.iteration_count + 1):
            start_time = datetime.utcnow()
            try:
                result_data = await job_function(job_record, iteration)
                end_time = datetime.utcnow()
                duration = (end_time - start_time).total_seconds()
                results.append(
                    {
                        "result": result_data,
                        "start_time": start_time,
                        "end_time": end_time,
                        "duration": duration,
                        "status": JobRunStatus.COMPLETED,
                    },
                )
            except Exception as e:
                error_info = traceback.format_exc()
                end_time = datetime.utcnow()
                duration = (end_time - start_time).total_seconds()

                logging.exception(
                    f"Error in iteration: {iteration}, error: {e}, traceback: {error_info}",
                )
                results.append(
                    {
                        "error": str(e),
                        "traceback": error_info,
                        "start_time": start_time,
                        "end_time": end_time,
                        "duration": duration,
                        "status": JobRunStatus.FAILED,
                    },
                )

    # Finalize job status
    job_status = (
        JobRunStatus.COMPLETED
        if all("error" not in r for r in results)
        else JobRunStatus.FAILED
    )
    await jobs_collection.update_one(
        {"_id": job_id},
        {
            "$set": {
                "status": job_status,
                "finished_at": datetime.utcnow(),
                "results": results,
            },
        },
    )

    return {"job_id": str(job_id), "status": job_status, "results": results}


async def handle_futures(tasks, job_id):
    results = []
    for coro in asyncio.as_completed(tasks):
        start_time = datetime.utcnow()
        try:
            result_data = await coro
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()
            results.append(
                {
                    "result": result_data,
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration": duration,
                    "status": JobRunStatus.COMPLETED,
                },
            )
        except Exception as e:
            error_info = traceback.format_exc()
            end_time = datetime.utcnow()
            duration = (end_time - start_time).total_seconds()

            logging.exception(
                f"Error during parallel execution, error: {e}, traceback: {error_info}",
            )
            results.append(
                {
                    "error": str(e),
                    "traceback": error_info,
                    "start_time": start_time,
                    "end_time": end_time,
                    "duration": duration,
                    "status": JobRunStatus.FAILED,
                },
            )
    return results

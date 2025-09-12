import asyncio
import logging
import pickle
from datetime import UTC, datetime

import nest_asyncio
from apscheduler.job import Job
from apscheduler.jobstores.base import BaseJobStore, JobLookupError

logger = logging.getLogger(__name__)


class CustomMongoDBJobStore(BaseJobStore):
    """Stores jobs in a MongoDB collection using custom MongoDB client."""

    def __init__(self, client, collection="jobs"):
        super().__init__()
        self.client = client
        self.collection_name = collection
        self._collection = None

    @property
    def collection(self):
        if self._collection is None:
            self._collection = self.client.get_collection(self.collection_name)
        return self._collection

    def _run_async(self, coro):
        loop = asyncio.get_event_loop()
        if loop.is_running():
            nest_asyncio.apply()
        return loop.run_until_complete(coro)

    def start(self, scheduler, alias):
        super().start(scheduler, alias)

        async def create_index():
            await self.collection.create_index("next_run_time")

        self._run_async(create_index())

    def lookup_job(self, job_id):
        async def find_one():
            return await self.collection.find_one({"_id": job_id})

        document = self._run_async(find_one())
        if document is None:
            return None
        return self._reconstitute_job(document["job_state"])

    def get_due_jobs(self, now):
        # Convert now to UTC timestamp to ensure consistent comparison
        timestamp = now.astimezone(UTC).timestamp()

        async def fetch_documents():
            cursor = self.collection.find({"next_run_time": {"$lte": timestamp}}).sort(
                "next_run_time",
                1,
            )
            return [doc async for doc in cursor]

        documents = self._run_async(fetch_documents())
        return self._get_jobs(documents)

    def get_next_run_time(self):
        async def find_one():
            return await self.collection.find_one(
                {"next_run_time": {"$ne": None}},
                sort=[("next_run_time", 1)],
            )

        document = self._run_async(find_one())
        if document is None:
            return None
        return datetime.fromtimestamp(document["next_run_time"], tz=UTC)

    def get_all_jobs(self):
        async def fetch_documents():
            cursor = self.collection.find()
            return [doc async for doc in cursor]

        documents = self._run_async(fetch_documents())
        return self._get_jobs(documents)

    def add_job(self, job):
        next_run_time = None
        if job.next_run_time:
            next_run_time = job.next_run_time.astimezone(UTC).timestamp()
        job_dict = {
            "_id": job.id,
            "job_state": pickle.dumps(job.__getstate__()),
            "next_run_time": next_run_time,
        }

        async def insert_one():
            await self.collection.insert_one(job_dict)

        self._run_async(insert_one())

    def update_job(self, job):
        next_run_time = None
        if job.next_run_time:
            next_run_time = job.next_run_time.astimezone(UTC).timestamp()
        job_dict = {
            "job_state": pickle.dumps(job.__getstate__()),
            "next_run_time": next_run_time,
        }

        async def update_one():
            return await self.collection.update_one({"_id": job.id}, {"$set": job_dict})

        result = self._run_async(update_one())
        if result.matched_count == 0:
            raise JobLookupError(job.id)

    def remove_job(self, job_id):
        async def delete_one():
            return await self.collection.delete_one({"_id": job_id})

        result = self._run_async(delete_one())
        if result.deleted_count == 0:
            raise JobLookupError(job_id)

    def remove_all_jobs(self):
        async def delete_many():
            await self.collection.delete_many({})

        self._run_async(delete_many())

    def _reconstitute_job(self, job_state):
        job_state = pickle.loads(job_state)
        job = Job.__new__(Job)
        job.__setstate__(job_state)
        job._scheduler = self._scheduler
        job._jobstore_alias = self._alias
        return job

    def _get_jobs(self, documents):
        jobs = []
        failed_job_ids = []

        for document in documents:
            try:
                jobs.append(self._reconstitute_job(document["job_state"]))
            except Exception as e:
                logger.error(f"Error reconstituting job {document['_id']}: {e}")
                failed_job_ids.append(document["_id"])

        if failed_job_ids:

            async def delete_many():
                await self.collection.delete_many({"_id": {"$in": failed_job_ids}})

            self._run_async(delete_many())

        return jobs

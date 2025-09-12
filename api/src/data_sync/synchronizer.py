import asyncio
import os
import traceback
from logging import getLogger

from data_sources.types.incremental_update_data import IncrementalUpdateData
from data_sync.data_processor import DataProcessor
from models import DocumentData
from services.observability import observability_context, observe
from services.observability.models import SpanExportMethod
from stores.document_store import DocumentStore
from utils.datetime_utils import utc_now_isoformat

logger = getLogger(__name__)

SOURCE_SYNC_PARALLEL_THREADS_NUM = int(
    os.environ.get("SOURCE_SYNC_PARALLEL_THREADS_NUM", 2),
)


class Synchronizer:
    def __init__(
        self,
        data_processor: DataProcessor,
        data_store: DocumentStore,
    ) -> None:
        self.data_store = data_store
        self.data_processor = data_processor

    async def sync(self, collection_id: str):
        try:
            await self.__load_data_from_data_source()

            existing_documents = await self.__get_existing_chunks(collection_id)
            logger.info(
                f"Existing documents in {collection_id=}: {len(existing_documents)}",
            )

            incremental_update_data: IncrementalUpdateData = (
                self.__get_incremental_changes(existing_documents)
            )

            # Incremental document sync TODO - refactor
            await self.__sync_incremental(
                collection_id=collection_id,
                incremental_update_data=incremental_update_data,
            )

            # docs_to_add = self.__create_chunks(incremental_update_data)
            # self.__sync_to_store(
            #     collection_id, docs_to_add, incremental_update_data.document_ids_to_delete
            # )

            sync_datetime = utc_now_isoformat()

            await self.data_store.update_collection_metadata(
                collection_id=collection_id,
                metadata={"last_synced": sync_datetime},
            )
        except asyncio.CancelledError:
            logger.info(
                "Collection sync was cancelled for collection '%s'", collection_id
            )
            raise
        except Exception as e:
            logger.error(
                "Error during collection sync for collection '%s': %s", collection_id, e
            )
            raise

    @observe(name="Fetch document list")
    async def __load_data_from_data_source(self):
        observability_context.update_current_span(
            description=f"Fetch list of documents from {self.data_processor.data_source.name} for synchronization.",
        )
        await self.data_processor.load_data()
        observability_context.update_current_span(
            output={
                "Document list size": len(
                    self.data_processor.get_all_records_basic_metadata(),
                ),
            },
        )

    @observe(
        name="Get existing chunks",
        description="Get existing chunks, stored in Magnet AI database.",
    )
    async def __get_existing_chunks(self, collection_id: str):
        try:
            documents = await self.data_store.list_documents(collection_id)
        except asyncio.CancelledError:
            logger.info(
                "Get existing chunks operation was cancelled for collection '%s'",
                collection_id,
            )
            raise
        except Exception as e:
            logger.error(
                "Error getting existing chunks for collection '%s': %s",
                collection_id,
                e,
            )
            raise

        observability_context.update_current_span(
            output={"Number of chunks in Magnet AI database": len(documents)}
        )

        return documents

    @observe(
        name="Calculate incremental changes",
        description="Compare existing chunks with documents in the source and calculate incremental changes.",
    )
    def __get_incremental_changes(
        self,
        existing_documents: list[dict],
    ) -> IncrementalUpdateData:
        source_basic_metadata = self.data_processor.get_all_records_basic_metadata()

        observability_context.update_current_span(
            input={
                f"Number of documents in {self.data_processor.data_source.name}": len(
                    source_basic_metadata,
                ),
                "Number of chunks in Magnet AI database": len(existing_documents),
            },
        )

        delta = self.data_processor.get_incremental_update_data(
            source_basic_metadata,
            existing_documents,
        )

        observability_context.update_current_span(
            output={
                "Number of documents to sync": len(delta.source_record_ids_to_add),
                "Number of chunks to delete": len(delta.document_ids_to_delete),
            },
        )

        return delta

    # TODO - refactor
    # Do not delete chunks for updated documents at once - delete before creating updated chunks
    @observe(
        name="Split file into chunks",
        description="Download file and split it into multiple chunks.",
    )
    async def __create_chunks(
        self,
        source_record_id_to_add: str,
    ) -> list[DocumentData]:
        observability_context.update_current_span(
            input={"Document ID": source_record_id_to_add},
        )

        chunks = await self.data_processor.create_chunks_from_doc(
            source_record_id_to_add
        )

        observability_context.update_current_span(
            output={"Number of chunks": len(chunks)},
        )

        return chunks

    @observe(
        name="Index chunks and save to database",
        description="Create embeddings for chunks and save them to the database, delete chunks that are no longer relevant.",
    )
    async def __sync_to_store(
        self,
        collection_id: str,
        docs_to_add: list[DocumentData],
        doc_ids_to_delete: list[str],
    ):
        observability_context.update_current_span(
            input={
                "Number of documents to sync": len(docs_to_add),
                "Number of chunks to delete": len(doc_ids_to_delete),
            },
            output={},
        )

        if docs_to_add:
            await self.data_store.create_documents(docs_to_add, collection_id)

        if doc_ids_to_delete:
            await self.data_store.delete_documents(
                document_ids=doc_ids_to_delete,
                collection_id=collection_id,
            )

    @observe(
        name="Split & sync",
        description="Download new documents and split them into chunks. Delete all chunks that are related to the modified documents, and re-download and split them again. And finally delete all chunks for removed documents.",
    )
    async def __sync_incremental(
        self,
        collection_id: str,
        incremental_update_data: IncrementalUpdateData,
    ):
        logger.info(
            f"Chunks to delete: {len(incremental_update_data.document_ids_to_delete)}",
        )

        if incremental_update_data.document_ids_to_delete:
            await self.data_store.delete_documents(
                document_ids=incremental_update_data.document_ids_to_delete,
                collection_id=collection_id,
            )

        source_records_total = len(incremental_update_data.source_record_ids_to_add)
        if source_records_total == 0:
            logger.info("No new source records to add.")
            return

        # Using a list to pass integer by reference to the worker
        source_records_synced = [0]
        source_records_failed = [0]

        logger.info(f"Source records to add: {source_records_total}")

        # Create a queue with a max size to apply backpressure
        # The size is a multiple of max_workers to ensure workers don't wait unnecessarily.
        max_workers = min(
            max(len(incremental_update_data.source_record_ids_to_add), 1),
            SOURCE_SYNC_PARALLEL_THREADS_NUM,
        )
        queue = asyncio.Queue(maxsize=max_workers * 2)

        @observe(
            name="Process document",
            description="Process document from data source, create chunks, transform if needed and save to database.",
        )
        async def __process_document(doc_id: str) -> bool:
            observability_context.update_current_span(input={"Document ID": doc_id})
            observability_context.update_current_config(
                span_export_method=SpanExportMethod.IGNORE_BUT_USE_FOR_TOTALS
            )

            docs_to_add = await self.__create_chunks(doc_id)
            await self.__sync_to_store(
                collection_id=collection_id,
                docs_to_add=docs_to_add,
                doc_ids_to_delete=[],
            )

            return True

        @observe(description="Document worker that processes documents from the queue.")
        async def worker(worker_id: int):
            observability_context.update_current_span(
                name=f"Document worker #{worker_id}"
            )

            while True:
                try:
                    # Get a document ID from the queue
                    doc_id = await queue.get()

                    try:
                        success = await __process_document(doc_id)
                        logger.info(f"Worker #{worker_id} processed document {doc_id}")
                    except Exception:
                        success = False
                        logger.error(
                            f"Worker #{worker_id} failed to process document {doc_id}"
                        )
                        traceback.print_exc()
                    finally:
                        if success:
                            source_records_synced[0] += 1
                        else:
                            source_records_failed[0] += 1

                        # Notify the queue that the item has been processed
                        queue.task_done()
                except asyncio.CancelledError:
                    logger.info(f"Worker #{worker_id} cancelled")
                    break

        # Create and start the worker tasks
        worker_tasks = [asyncio.create_task(worker(i)) for i in range(max_workers)]

        # Producer: Add document IDs to the queue
        for doc_id in incremental_update_data.source_record_ids_to_add:
            await queue.put(doc_id)

        # Wait for the queue to be empty (all docs processed)
        await queue.join()

        # Stop the worker tasks gracefully
        for task in worker_tasks:
            task.cancel()

        # Wait for all workers to finish cancelling
        await asyncio.gather(*worker_tasks, return_exceptions=True)

        observability_context.update_current_span(
            output={
                "Number of documents synced": source_records_synced,
                "Number of documents deleted": len(
                    incremental_update_data.document_ids_to_delete,
                ),
                "Number of documents failed": source_records_failed,
            },
        )

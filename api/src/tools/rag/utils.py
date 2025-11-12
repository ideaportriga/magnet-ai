from collections import defaultdict
from itertools import groupby

from langchain.schema import Document

from models import (
    ChunksByCollection,
    DocumentSearchResult,
    QueryChunksByCollectionBySource,
)
from stores import get_db_store

# Assume get_db_store can be made async if it does I/O
# store = get_db_store()
store = None


async def get_extended_chunks_query(
    search_result: DocumentSearchResult,
    context_window: int,
) -> QueryChunksByCollectionBySource:
    """For Small to Big Retrieval.

    Returning a broader number of chunks that surrounds the chunks from the `search_result`.

    Result items with not existent `collection_id`, `metadata.sourceId` or `metadata.chunkNumber` are ignored as not-chunked sources.
    """
    data = defaultdict(lambda: defaultdict(set[int]))

    for search_result_item in search_result:
        collection_id = search_result_item.collection_id
        source_id = search_result_item.metadata.get("sourceId")
        chunk_number = search_result_item.metadata.get("chunkNumber")

        if not (collection_id and source_id and chunk_number):
            continue

        data[collection_id][source_id].add(chunk_number)

    query: QueryChunksByCollectionBySource = {}

    for collection_id, chunks_by_source in data.items():
        query[collection_id] = {}

        for source_id, chunk_numbers in chunks_by_source.items():
            source_extended_chunk_numbers = set()

            for chunk_number in chunk_numbers:
                context_chunks = [
                    i
                    for i in range(
                        chunk_number - context_window,
                        chunk_number + context_window + 1,
                    )
                    if i > 0
                ]
                source_extended_chunk_numbers.update(context_chunks)

            query[collection_id][source_id] = list(source_extended_chunk_numbers)

    return query


async def get_chat_completion_input_documents(
    search_result: DocumentSearchResult,
    context_window: int,
) -> list[Document]:
    if context_window <= 0:
        return [
            Document(
                page_content=search_result_item.content,
                metadata=search_result_item.metadata,
            )
            for search_result_item in search_result
        ]

    extended_chunks_query = await get_extended_chunks_query(
        search_result=search_result,
        context_window=context_window,
    )

    store_instance = get_db_store()
    # Assume document_collections_query_chunks_context is async
    extended_chunks_by_collection = (
        await store_instance.document_collections_query_chunks_context(
            query=extended_chunks_query,
        )
    )

    input_documents = await _form_input_documents(
        search_result=search_result,
        extended_chunks_by_collection=extended_chunks_by_collection,
        separator=" ",
    )

    return input_documents


async def _form_input_documents(
    search_result: DocumentSearchResult,
    extended_chunks_by_collection: ChunksByCollection,
    separator: str = " ",
) -> list[Document]:
    extended_chunks_grouped: dict[str, dict[str, list[dict]]] = {}

    for collection_id, collection_chunks in extended_chunks_by_collection.items():
        collection_chunks = sorted(
            collection_chunks,
            key=lambda x: (x["metadata"]["sourceId"], x["metadata"]["chunkNumber"]),
        )
        collection_chunks_group_by_source_id = groupby(
            collection_chunks,
            key=lambda x: x["metadata"]["sourceId"],
        )
        collection_chunks_by_source_id: dict[str, list[dict]] = {
            key: list(group) for key, group in collection_chunks_group_by_source_id
        }

        extended_chunks_grouped[collection_id] = collection_chunks_by_source_id

    processed_sources: set[tuple[str, str]] = set()

    documents: list[Document] = []

    for search_result_item in search_result:
        collection_id = search_result_item.collection_id
        source_id = str(search_result_item.metadata.get("sourceId", ""))

        if not source_id:
            documents.append(
                Document(
                    page_content=search_result_item.content,
                    metadata=search_result_item.metadata,
                ),
            )
            continue

        source = (collection_id, source_id)

        if source in processed_sources:
            continue

        source_chunks = extended_chunks_grouped.get(collection_id, {}).get(
            source_id,
            [],
        )

        if not source_chunks:
            documents.append(
                Document(
                    page_content=search_result_item.content,
                    metadata=search_result_item.metadata,
                ),
            )
        else:
            chunk_group_documents = await _form_input_documents_for_source_chunks(
                source_chunks=source_chunks,
                separator=separator,
            )
            documents.extend(chunk_group_documents)

        processed_sources.add(source)

    return documents


async def _form_input_documents_for_source_chunks(
    source_chunks: list[dict],
    separator: str = " ",
) -> list[Document]:
    documents: list[Document] = []

    for chunk in source_chunks:
        chunk_metadata = chunk["metadata"]
        chunk_content = chunk["content"]

        documents.append(Document(page_content=chunk_content, metadata=chunk_metadata))

    return documents


# The approach combines sequential chunks into one document, which disallows precise citation to specific chunk
# def _form_input_documents_for_source_chunks(source_chunks: list[dict], separator: str = " ") -> list[Document]:
#     documents: list[Document] = []
#     content_list: list[str] = []
#     previous_chunk_number = None

#     for chunk in source_chunks:
#         chunk_number = chunk["metadata"]["chunkNumber"]

#         if previous_chunk_number and chunk_number != previous_chunk_number + 1:
#             # When there's a break in sequence, create a new Document
#             documents.append(Document(page_content=separator.join(content_list)))
#             content_list = []

#         content_list.append(chunk["content"])
#         previous_chunk_number = chunk_number

#     if content_list:
#         documents.append(Document(page_content=separator.join(content_list)))

#     return documents

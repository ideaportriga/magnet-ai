import os

from models import DocumentSearchResult
from services.observability import observability_context, observe
from services.utils.get_ids_by_system_names import get_ids_by_system_names
from stores import get_db_store
from type_defs.pagination import FilterObject
from validation.rag_tools import RetrieveConfig

# Assume get_db_store can be awaited to get the store
store = get_db_store()

env = os.environ


@observe(name="Retrieve documents from collections")
async def retrieve(
    *,
    user_message: str,
    filter: FilterObject | None = None,
    retrieve_config: RetrieveConfig,
    max_chunks_retrieved: int,
) -> DocumentSearchResult:
    # FIXME - currently collection_system_names contains collection ids, not system names.

    collection_ids = await get_ids_by_system_names(
        retrieve_config.collection_system_names, "collections"
    )

    if not collection_ids:
        raise ValueError("No collection ids found")

    if isinstance(collection_ids, str):
        collection_ids = [collection_ids]

    document_search_result = await store.document_collections_similarity_search(
        collection_ids=collection_ids,
        retrieve_config=retrieve_config,
        query=user_message,
        num_results=max_chunks_retrieved,
        filter=filter,
    )

    selected_top_results = await select_top_results(
        document_search_result=document_search_result,
        score_threshold=retrieve_config.similarity_score_threshold,
        num_results=max_chunks_retrieved,
    )

    return selected_top_results


@observe(
    name="Select top results",
    description="Select top results from all search results based on the score threshold.",
    capture_output=True,
)
async def select_top_results(
    document_search_result: DocumentSearchResult,
    score_threshold: float,
    num_results: int,
) -> DocumentSearchResult:
    selected_top_results: DocumentSearchResult = []

    observability_context.update_current_span(
        input={
            "score_threshold": score_threshold,
            "num_results": num_results,
            "documents": document_search_result,
        },
    )

    for document_search_result_item in document_search_result:
        if document_search_result_item.score < score_threshold:
            break

        selected_top_results.append(document_search_result_item)

        if len(selected_top_results) >= num_results:
            break

    return selected_top_results

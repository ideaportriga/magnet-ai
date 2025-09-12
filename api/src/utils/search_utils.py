from decimal import ROUND_HALF_UP, Decimal

from models import DocumentSearchResult, DocumentSearchResultItem


def reciprocal_rank_fusion(
    result_1: DocumentSearchResult,
    result_2: DocumentSearchResult,
    num_results: int,
):
    """Implements Reciprocal Rank Fusion to combine results from semantic and full-text search.

    RRF score = sum(1 / (k + r)) where:
    - r is the rank of the document in each result list
    - k is a constant that prevents items appearing low in only one list from getting too much weight
    """
    k = 1

    # Create a dictionary to store combined scores
    combined_scores = {}

    # Process semantic search results
    for rank, item in enumerate(result_1):
        if item.id not in combined_scores:
            combined_scores[item.id] = {"item": item, "score": 0}
        combined_scores[item.id]["score"] += 1.0 / (k + rank)

    # Process full-text search results
    for rank, item in enumerate(result_2):
        if item.id not in combined_scores:
            combined_scores[item.id] = {"item": item, "score": 0}
        combined_scores[item.id]["score"] += 1.0 / (k + rank)

    # Convert scores to decimal with proper rounding
    for doc_id in combined_scores:
        item = combined_scores[doc_id]["item"]
        rrf_score = Decimal(combined_scores[doc_id]["score"]).quantize(
            Decimal("0.0000"),
            rounding=ROUND_HALF_UP,
        )
        # Create a new item with the fused score
        combined_scores[doc_id]["item"] = DocumentSearchResultItem(
            id=item.id,
            score=rrf_score,
            content=item.content,
            collection_id=item.collection_id,
            metadata=item.metadata,
        )

    # Sort by score in descending order and return top results
    fused_results = sorted(
        [item_data["item"] for item_data in combined_scores.values()],
        key=lambda x: x.score,
        reverse=True,
    )

    # Limit to num_results
    return fused_results[:num_results]

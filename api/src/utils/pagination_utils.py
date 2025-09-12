from typing import Any

from bson import ObjectId
from litestar.exceptions import ClientException

from stores.database_client import DatabaseClient


def serialize_mongo_documents(items):
    """Convert ObjectId to string in a list of MongoDB documents"""
    for item in items:
        if "_id" in item:
            item["id"] = str(item["_id"])
            item["_id"] = str(item["_id"])
    return items


async def paginate_collection(
    collection_name: str,
    data: Any,  # Replace with the appropriate type if needed
    client: DatabaseClient,
    additional_filters: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Paginate a collection based on offset pagination parameters.

    Args:
        collection_name: Name of the MongoDB collection
        data: Pagination request data

    Returns:
        Dictionary with paginated items and metadata

    """
    filters = (
        data.filters.model_dump(exclude_none=True, by_alias=True)
        if data.filters
        else {}
    )
    if additional_filters:
        filters.update(additional_filters)

    # Convert _id filter values to ObjectId
    if "_id" in filters:
        if isinstance(filters["_id"], dict):
            for op, value in filters["_id"].items():
                if value is not None:
                    try:
                        if op in ["$in", "$nin"] and isinstance(value, list):
                            filters["_id"][op] = [ObjectId(v) for v in value]
                        else:
                            filters["_id"][op] = ObjectId(value)
                    except Exception:
                        raise ClientException(f"Invalid ObjectId format: {value}")
        else:
            try:
                filters["_id"] = ObjectId(filters["_id"])
            except Exception:
                raise ClientException("Invalid ObjectId format")

    # Apply field inclusion or exclusion, supporting nested fields
    projection = None
    if data.fields:
        projection = {field: 1 for field in data.fields}
    elif data.exclude_fields:
        projection = {field: 0 for field in data.exclude_fields}

    # Use async MongoDB driver methods
    cursor = (
        client.get_collection(collection_name)
        .find(filters, projection)
        .sort(data.sort, data.order)
        .skip(data.offset)
        .limit(data.limit)
    )
    items = await cursor.to_list(length=data.limit)
    items = serialize_mongo_documents(items)

    collection = client.get_collection(collection_name)
    total_count = await collection.count_documents(filters)

    return {
        "items": items,
        "total": total_count,
        "limit": data.limit,
        "offset": data.offset,
    }

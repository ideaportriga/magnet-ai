from datetime import UTC, datetime
from typing import Any

from bson import ObjectId
from litestar import Controller, delete, get, patch, post, put
from litestar.exceptions import ClientException, NotFoundException, ValidationException
from litestar.status_codes import HTTP_200_OK, HTTP_204_NO_CONTENT
from pydantic import BaseModel

from stores import get_db_client
from type_defs.pagination import (
    CursorPaginationRequest,
    OffsetPaginationRequest,
)
from utils.pagination_utils import paginate_collection

MAX_LIMIT = 5000


def serialize_mongo_documents(items):
    """Convert ObjectId to string in a list of MongoDB documents"""
    for item in items:
        if "_id" in item:
            item["id"] = str(item["_id"])
            item["_id"] = str(item["_id"])
    return items


def create_entity_controller(
    collection_name: str,
    model: type[BaseModel] | type[dict] = dict,
    exclude_fields: list[str] | None = None,
    path_param: str | None = None,
    tags_param: list[str] | None = None,
) -> type[Controller]:
    """Create a controller with CRUD operations for an entity"""

    class EntityController(Controller):
        if path_param:
            path = path_param

        if tags_param:
            tags = tags_param

        @get()
        async def list_entities(self) -> list[dict[str, Any]]:
            client = get_db_client()
            projection = (
                {field: 0 for field in exclude_fields} if exclude_fields else None
            )
            cursor = client.get_collection(collection_name).find({}, projection)

            entities = []
            async for document in cursor:
                doc_id = str(document.pop("_id"))
                if "id" in document:
                    document["original_id"] = document["id"]
                document["id"] = doc_id
                entities.append(document)

            return entities

        @post()
        async def create_entity(self, data: model) -> dict[str, str]:
            client = get_db_client()

            data_dict = data.model_dump() if isinstance(data, BaseModel) else data

            metadata = {
                "created_at": datetime.utcnow(),
                "modified_at": datetime.utcnow(),
            }
            data_dict["_metadata"] = metadata
            result = await client.get_collection(collection_name).insert_one(data_dict)

            return {"inserted_id": str(result.inserted_id)}

        @post("/bulk")
        async def create_entities(self, data: list[model]) -> dict[str, list[str]]:
            client = get_db_client()
            current_time = datetime.now(UTC)

            validated_data_list = []
            for item in data:
                data_dict = item.model_dump() if isinstance(item, BaseModel) else item
                data_dict["_metadata"] = {
                    "created_at": current_time,
                    "modified_at": current_time,
                }
                validated_data_list.append(data_dict)

            result = await client.get_collection(collection_name).insert_many(
                validated_data_list,
            )
            inserted_ids = [str(_id) for _id in result.inserted_ids]

            return {"inserted_ids": inserted_ids}

        @get("/code/{code:str}")
        async def get_entity_by_code(self, code: str) -> dict[str, Any]:
            client = get_db_client()
            document = await client.get_collection(collection_name).find_one(
                {"system_name": code},
            )

            if not document:
                raise NotFoundException()

            entity = {"id": str(document.pop("_id")), **document}

            return entity

        @get("/id/{entity_id:str}")
        async def get_entity(self, entity_id: str) -> dict[str, Any]:
            # TODO - simplify validation using types?
            if not ObjectId.is_valid(entity_id):
                raise ClientException("Invalid entity ID")

            client = get_db_client()
            document = await client.get_collection(collection_name).find_one(
                {"_id": ObjectId(entity_id)},
            )

            if not document:
                raise NotFoundException()

            entity = {"id": str(document.pop("_id")), **document}
            return entity

        @put("/{entity_id:str}")
        async def replace_entity(self, entity_id: str, data: model) -> dict[str, Any]:
            client = get_db_client()

            data_dict = data.model_dump() if isinstance(data, BaseModel) else data

            data_dict["_metadata"] = {"modified_at": datetime.now(UTC)}

            result = await client.get_collection(collection_name).replace_one(
                {"_id": ObjectId(entity_id)},
                {"$set": data_dict},
            )

            if result.matched_count == 0:
                raise NotFoundException(detail=f"Entity with id {entity_id} not found")

            return {"updated_id": entity_id}

        @patch("/{entity_id:str}")
        async def update_entity(self, entity_id: str, data: model) -> dict[str, Any]:
            client = get_db_client()

            data_dict = data.model_dump() if isinstance(data, BaseModel) else data

            # Oracle Mongo API throws an excepton if update_data is array
            # {'errmsg': 'Field u has invalid type ARRAY.', 'code': 3016, 'codeName': 'MONGO-3016', 'ecid': '6790f71d5fb04f4e949a21271803ba37', 'ok': 0.0}
            # update_data = [{"$set": validated_data}, {"$set": {"_metadata.modified_at": datetime.utcnow()}}]
            update_data = {
                "$set": {
                    **data_dict,
                    "_metadata.modified_at": datetime.now(UTC),
                },
            }
            result = await client.get_collection(collection_name).update_one(
                {"_id": ObjectId(entity_id)},
                update_data,
            )

            if result.matched_count == 0:
                raise NotFoundException(detail=f"Entity with id {entity_id} not found")

            return {"updated_id": entity_id}

        @delete("/{entity_id:str}", status_code=HTTP_204_NO_CONTENT)
        async def delete_entity(self, entity_id: str) -> None:
            client = get_db_client()

            try:
                result = await client.get_collection(collection_name).delete_one(
                    {"_id": ObjectId(entity_id)},
                )
            except Exception:
                raise ValidationException(detail="Invalid ID format")

            if result.deleted_count == 0:
                raise NotFoundException(detail=f"Entity with id {entity_id} not found")

        @get("/schema")
        async def get_model_schema(self) -> dict[str, Any]:
            if not model or not issubclass(model, BaseModel):
                raise NotFoundException("No model schema available")

            schema = model.model_json_schema()

            return schema

        @post("/paginate/cursor", status_code=HTTP_200_OK)
        async def cursor_pagination(
            self,
            data: CursorPaginationRequest,
        ) -> dict[str, Any]:
            client = get_db_client()
            filters = data.filters or {}
            if data.cursor:
                try:
                    filters["_id"] = {"$gt": ObjectId(data.cursor)}
                except Exception:
                    raise ClientException("Invalid cursor format")

            # Apply field inclusion or exclusion, supporting nested fields
            projection = None
            if data.fields:
                projection = {field: 1 for field in data.fields}
            elif data.exclude_fields:
                projection = {field: 0 for field in data.exclude_fields}

            cursor = (
                client.get_collection(collection_name)
                .find(filters, projection)
                .sort(data.sort, data.order)
                .limit(data.limit)
            )
            items = []
            async for document in cursor:
                items.append(document)

            items = serialize_mongo_documents(items)

            next_cursor = str(items[-1]["_id"]) if items else None

            return {"items": items, "next_cursor": next_cursor}

        @post("/paginate/offset", status_code=HTTP_200_OK)
        async def offset_pagination(
            self,
            data: OffsetPaginationRequest,
        ) -> dict[str, Any]:
            return await paginate_collection(
                collection_name,
                data,
                client=get_db_client(),
            )

    return EntityController

from datetime import UTC, datetime
from logging import getLogger

from models import DocumentData
from stores import get_db_client, get_db_store

# Assume async versions of get_db_client and get_db_store
client = get_db_client()
store = get_db_store()

logger = getLogger(__name__)

COLLECTION_NAMES_BY_ENTITY_TYPE = {
    "ai_apps": "ai_apps",
    "rag_tools": "rag_tools",
    "retrieval_tools": "retrieval_tools",
    "prompt_templates": "prompts",
    "models": "models",
}


async def export_entities(data: dict, skip_chunks: bool = False) -> dict:
    logger.info("start export")

    result = {}

    for entity_type, system_names in data.items():
        system_names = [system_name for system_name in system_names if system_name]
        logger.info(f"export {entity_type=}, {system_names=}")

        if entity_type == "knowledge_sources":
            exported_knowledge_sources = await _export_knowledge_sources(
                system_names, skip_chunks
            )
            result[entity_type] = exported_knowledge_sources

            continue

        if entity_type not in COLLECTION_NAMES_BY_ENTITY_TYPE:
            logger.info(f"Unsupported entity type {entity_type}")

            continue

        collection_name = COLLECTION_NAMES_BY_ENTITY_TYPE[entity_type]
        collection = client.get_collection(collection_name)

        # TODO - keep only system_name
        filter = {
            "$or": [
                {"code": {"$in": system_names}},
                {"system_name": {"$in": system_names}},
            ],
        }
        projection = {"_id": False, "id": False, "_metadata": False}

        try:
            cursor = collection.find(filter, projection)
            result[entity_type] = await cursor.to_list(length=None)
        except Exception as e:
            logger.error(f"Error exporting {entity_type}: {e}")
            result[entity_type] = []

    return result


async def import_entities(data: dict) -> None:
    logger.info("start import")

    for entity_type, entities in data.items():
        if not entities:
            logger.info("Skip - no entities")
            continue

        logger.info(f"import {entity_type=}, record count: {len(entities)}")

        if entity_type == "knowledge_sources":
            await _import_knowledge_sources(entities)
            continue

        if entity_type not in COLLECTION_NAMES_BY_ENTITY_TYPE:
            logger.info(f"Unsupported entity type {entity_type}")
            continue

        collection_name = COLLECTION_NAMES_BY_ENTITY_TYPE[entity_type]
        collection = client.get_collection(collection_name)

        for entity in entities:
            current_time = datetime.now(UTC)
            entity["_metadata"] = {
                "created_at": current_time,
                "modified_at": current_time,
            }

        try:
            await collection.insert_many(entities)
        except Exception as e:
            logger.error(f"Error importing {entity_type}: {e}")


async def _export_knowledge_sources(
    system_names: list[str], skip_chunks: bool = False
) -> list[dict]:
    logger.info("Start knowledge sources export")
    # TODO - code -> system_name
    try:
        knowledge_sources = await store.list_collections(
            {"system_name": {"$in": system_names}},
        )
    except Exception as e:
        logger.error(f"Error listing knowledge sources: {e}")
        return []

    if not skip_chunks:
        for knowledge_source in knowledge_sources:
            collection_id = knowledge_source.pop("id")
            try:
                chunks = await store.list_documents(collection_id=collection_id)
            except Exception as e:
                logger.error(f"Error listing documents for {collection_id}: {e}")
                chunks = []

            for chunk in chunks:
                chunk.pop("id")

            knowledge_source["chunks"] = chunks

    return knowledge_sources


async def _import_knowledge_sources(knowledge_sources: list[dict]) -> None:
    logger.info("Start knowledge sources import")

    for knowledge_source in knowledge_sources:
        chunks: list[dict] = knowledge_source.pop("chunks", [])

        documents = [DocumentData(**chunk) for chunk in chunks]

        try:
            knowledge_source_id = await store.create_collection(
                metadata=knowledge_source,
            )

            logger.info(f"Imported {knowledge_source_id=}")
        except Exception as e:
            logger.error(f"Error creating collection: {e}")
            continue

        if chunks:
            try:
                await store.create_documents(
                    documents=documents,
                    collection_id=knowledge_source_id,
                )
                logger.info(
                    f"Imported {len(documents)} chunks for {knowledge_source_id=}",
                )
            except Exception as e:
                logger.error(f"Error creating documents for {knowledge_source_id}: {e}")

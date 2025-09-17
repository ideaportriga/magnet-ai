from services.knowledge_sources.models import MetadataAutomapField
from stores import get_db_store

store = get_db_store()


async def automap_metadata(collection_id: str, exclude_fields: list[str] | None = None):
    documents = await store.list_documents(collection_id)
    mapping: dict[str, MetadataAutomapField] = {}
    for document in documents:
        metadata = document.get("metadata", {}).get("sourceMetadata", {})
        for key, _ in metadata.items():
            if key in exclude_fields:
                continue
            mapping[key] = MetadataAutomapField(
                enabled=True,
                name=key,
                mapping=f'$.sourceMetadata."{key}"',
            )
    return mapping

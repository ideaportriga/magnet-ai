from services.knowledge_sources.models import MetadataAutomapField
from stores import get_db_store

store = get_db_store()


def _build_metadata_mapping(
    data: dict,
    prefix: str = "$",
    name_prefix: str = "",
    mapping: dict[str, MetadataAutomapField] | None = None,
    exclude_fields: list[str] | None = None,
) -> dict[str, MetadataAutomapField]:
    if mapping is None:
        mapping = {}
    if exclude_fields is None:
        exclude_fields = []

    for key, value in data.items():
        full_key = f"{prefix}.{key}" if prefix != "$" else f"$.{key}"
        simple_name = f"{name_prefix}_{key}" if name_prefix else key
        if key in exclude_fields:
            continue
        if isinstance(value, dict):
            _build_metadata_mapping(
                value, full_key, simple_name, mapping, exclude_fields
            )
        else:
            mapping[full_key] = MetadataAutomapField(
                enabled=True,
                name=simple_name,
                mapping=full_key,
            )
    return mapping


async def automap_metadata(collection_id: str, exclude_fields: list[str] | None = None):
    documents = await store.list_documents(collection_id)
    mapping: dict[str, MetadataAutomapField] = {}
    for document in documents:
        metadata = document.get("metadata", {})
        _build_metadata_mapping(
            metadata, mapping=mapping, exclude_fields=exclude_fields
        )
    return mapping

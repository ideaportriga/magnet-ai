from __future__ import annotations

from stores import get_db_store

_store = get_db_store()
_COLLECTION_CACHE: dict[str, str] = {}


async def get_or_create_collection_id(system_name: str) -> str:
    # Try cache first
    if system_name in _COLLECTION_CACHE:
        return _COLLECTION_CACHE[system_name]

    # Try to find existing collection by system_name
    cols = await _store.list_collections(query={"system_name": system_name})
    if cols:
        cid = cols[0]["id"]
        _COLLECTION_CACHE[system_name] = cid
        return cid

    # Otherwise create it — **provide an id here**
    payload = {
        "name": system_name.capitalize(),
        "system_name": system_name,
        "type": "generic",
        "created_by": "system",
        "updated_by": "system",
    }
    cid = await _store.create_collection(payload)
    _COLLECTION_CACHE[system_name] = cid
    return cid

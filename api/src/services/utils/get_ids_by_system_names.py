from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from core.config.base import get_settings
from core.db.models.collection.collection import Collection


async def get_ids_by_system_names(system_name_list_or_str, collection_name):
    """
    Get IDs by system names for specified table/collection.

    Args:
        system_name_list_or_str: Single system name (str) or list of system names
        collection_name: Name of the table/collection (currently only "collections" supported)

    Returns:
        Single ID (str) if input was string, list of IDs if input was list
    """
    if isinstance(system_name_list_or_str, str):
        system_name_list = [system_name_list_or_str]
        return_single = True
    else:
        system_name_list = system_name_list_or_str
        return_single = False

    # Currently only collections table is supported
    if collection_name != "collections":
        raise ValueError(f"Unsupported collection_name: {collection_name}")

    try:
        # Create database session
        settings = get_settings()
        engine = settings.db.get_engine()

        async with AsyncSession(engine) as session:
            # Use SQLAlchemy query with IN clause for efficient batch lookup
            stmt = select(Collection.id).where(
                Collection.system_name.in_(system_name_list)
            )
            result = await session.execute(stmt)
            entities = result.scalars().all()

            ids = [str(entity) for entity in entities]
    except Exception:
        # Handle/log exception as needed
        ids = []

    if return_single:
        return ids[0] if ids else None
    return ids

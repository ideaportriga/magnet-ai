# Async compatibility check: True
import os
import re
import uuid

from bson import ObjectId, errors


def validate_id(id: str):
    db_type = os.environ.get("DB_TYPE", "COSMOS")

    if db_type == "ORACLE":
        if not re.fullmatch(r"[0-9A-F]{32}", id):
            raise errors.InvalidId(f"Invalid hexadecimal string: {id}")
        return id
    if db_type == "COSMOS" or db_type == "MONGODB":
        return ObjectId(id)
    if db_type == "PGVECTOR":
        try:
            # Validate UUID format and return as string
            uuid_obj = uuid.UUID(id)
            return str(uuid_obj)
        except ValueError:
            raise errors.InvalidId(f"Invalid UUID string: {id}")
    raise ValueError(f"Unsupported DB_TYPE: {db_type}")

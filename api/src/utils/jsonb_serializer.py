"""
Custom serializer/deserializer for JsonB fields.
Handles datetime and UUID objects for proper serialization in PostgreSQL JSONB.
"""

import json
import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from bson import ObjectId
from sqlalchemy import TEXT, TypeDecorator
from sqlalchemy.dialects.postgresql import JSONB

# Predefined field sets for different use cases
DEFAULT_TARGET_FIELDS = {
    "id",
    "updated_at",
    "created_at",
    "_id",
    "user_id",
    "session_id",
}
AUDIT_FIELDS = {"id", "created_at", "updated_at", "created_by", "updated_by"}
CONVERSATION_FIELDS = {
    "updated_at",
    "started_at",
    "completed_at",
    "user_id",
    "session_id",
    "created_at",
    "id",
}
MONGODB_FIELDS = {"_id", "id", "created_at", "updated_at", "modified_at"}
VARIANT_FIELDS = {"id", "created_at", "updated_at", "modified_at"}


class JsonBCustomEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for JsonB fields.

    Handles special data types:
    - datetime: converts to ISO format string
    - UUID: converts to string
    - ObjectId: converts to string
    - Decimal: converts to string to preserve precision
    """

    def default(self, obj: Any) -> Any:
        if isinstance(obj, datetime):
            # Convert datetime to ISO format with UTC timezone
            return obj.isoformat()

        elif isinstance(obj, uuid.UUID):
            # Convert UUID to string
            return str(obj)

        elif isinstance(obj, ObjectId):
            # Convert MongoDB ObjectId to string
            return str(obj)

        elif isinstance(obj, Decimal):
            # Convert Decimal to string to preserve precision
            return str(obj)

        # For other types use standard handler
        return super().default(obj)


def jsonb_serialize(data: Any) -> str:
    """
    Serialize data for saving in JsonB field.

    Args:
        data: Data to serialize

    Returns:
        JSON string with properly handled datetime and UUID
    """
    return json.dumps(data, cls=JsonBCustomEncoder, ensure_ascii=False)


def jsonb_deserialize(json_str: str, target_fields: set[str] | None = None) -> Any:
    """
    Deserialize data from JsonB field.

    Tries to automatically restore datetime and UUID objects from strings,
    but only for specified fields.

    Args:
        json_str: JSON string from database
        target_fields: Set of field names to process.
                      Default: {'id', 'updated_at', 'created_at', '_id', 'user_id', 'session_id'}

    Returns:
        Deserialized data with restored types
    """
    data = json.loads(json_str)
    return _restore_types_recursive(data, target_fields)


def _restore_types_recursive(data: Any, target_fields: set[str] | None = None) -> Any:
    """
    Recursively restore types in data structure.

    Args:
        data: Data to process
        target_fields: Set of field names to process.
                      If None, all fields are processed

    Returns:
        Data with restored types
    """
    # Default fields that require processing
    if target_fields is None:
        target_fields = DEFAULT_TARGET_FIELDS

    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            if key in target_fields and isinstance(value, str):
                # Process only target fields
                result[key] = _try_restore_type(value)
            else:
                # Recursively process nested structures
                result[key] = _restore_types_recursive(value, target_fields)
        return result

    elif isinstance(data, list):
        return [_restore_types_recursive(item, target_fields) for item in data]

    return data


def _try_restore_type(value: str) -> Any:
    """
    Tries to restore the type for a string value.

    Args:
    value: String to process

    Returns:
    Restored object or original string
    """
    # Trying to restore datetime
    if _is_datetime_string(value):
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except (ValueError, TypeError):
            pass

    # Trying to restore UUID
    if _is_uuid_string(value):
        try:
            return uuid.UUID(value)
        except (ValueError, TypeError):
            pass

    # Trying to restore ObjectId
    if _is_objectid_string(value):
        try:
            return ObjectId(value)
        except (ValueError, TypeError):
            pass

    return value


def _is_datetime_string(value: str) -> bool:
    """
    Checks if the string is a datetime in ISO format.

    Args:
    value: String to check

    Returns:
    True if the string looks like a datetime
    """
    # Simple check for ISO datetime format
    if len(value) < 19:  # Minimum length for YYYY-MM-DDTHH:MM:SS
        return False

    # Checking main ISO format patterns
    return (
        "T" in value
        and (":" in value)
        and (value.count("-") >= 2)
        and (value[4] == "-" and value[7] == "-")
    )


def _is_uuid_string(value: str) -> bool:
    """
    Checks if the string is a UUID.

    Args:
    value: String to check

    Returns:
    True if the string looks like a UUID
    """
    if len(value) != 36:
        return False

    # UUID format: 8-4-4-4-12
    parts = value.split("-")
    return (
        len(parts) == 5
        and len(parts[0]) == 8
        and len(parts[1]) == 4
        and len(parts[2]) == 4
        and len(parts[3]) == 4
        and len(parts[4]) == 12
        and all(c.isalnum() for part in parts for c in part)
    )


def _is_objectid_string(value: str) -> bool:
    """
    Checks if the string is a MongoDB ObjectId.

    Args:
    value: String to check

    Returns:
    True if the string looks like an ObjectId
    """
    return len(value) == 24 and all(c in "0123456789abcdef" for c in value.lower())


# Example usage with SQLAlchemy TypeDecorator


class CustomJsonB(TypeDecorator):
    """
    Custom data type for PostgreSQL JSONB with automatic
    serialization/deserialization of datetime and UUID.

    Processes only the specified fields to improve performance.
    """

    impl = JSONB
    cache_ok = True

    def __init__(self, target_fields: set[str] | None = None, **kwargs):
        """
        Args:
            target_fields: A set of field names to process.
                          Default: DEFAULT_TARGET_FIELDS
        """
        super().__init__(**kwargs)
        self.target_fields = target_fields or DEFAULT_TARGET_FIELDS

    def process_bind_param(self, value, dialect):
        """
        Processes the value before saving it to the database.
        """
        if value is not None:
            # If it's already a string, return as is
            if isinstance(value, str):
                return value
            # Return Python objects directly - let asyncpg encoder handle serialization
            # This avoids double serialization: CustomJsonB → asyncpg encoder
            return value
        return value

    def process_result_value(self, value, dialect):
        """
        Processes the value after retrieving it from the database.
        """
        if value is not None:
            # If we got dict/list from JSONB, restore types only for target fields
            return _restore_types_recursive(value, self.target_fields)
        return value


# Alternative version if you need to work with JSON as text
class CustomJsonBText(TypeDecorator):
    """
    Custom data type for JSON stored as TEXT with automatic
    serialization/deserialization of datetime and UUID.

    Processes only the specified fields to improve performance.
    """

    impl = TEXT
    cache_ok = True

    def __init__(self, target_fields: set[str] | None = None, **kwargs):
        """
        Args:
            target_fields: A set of field names to process.
                          Default: DEFAULT_TARGET_FIELDS
        """
        super().__init__(**kwargs)
        self.target_fields = target_fields or DEFAULT_TARGET_FIELDS

    def process_bind_param(self, value, dialect):
        """
        Processes the value before saving it to the database.
        """
        if value is not None:
            if isinstance(value, str):
                return value
            return jsonb_serialize(value)
        return value

    def process_result_value(self, value, dialect):
        """
        Processes the value after retrieving it from the database.
        """
        if value is not None:
            return jsonb_deserialize(value, self.target_fields)
        return value

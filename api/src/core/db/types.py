"""
Custom SQLAlchemy types for database models.
"""

from __future__ import annotations

from sqlalchemy import Text, TypeDecorator


class EncryptedJsonB(TypeDecorator):
    """Custom type that encrypts JSON data before storing in database."""

    impl = Text
    cache_ok = True

    def __init__(self, key: str, **kwargs):
        from advanced_alchemy.types import EncryptedText

        self.encrypted_type = EncryptedText(key=key)
        super().__init__(**kwargs)

    def process_bind_param(self, value, dialect):
        """Convert dict to JSON string before encryption."""
        if value is not None:
            if isinstance(value, dict):
                import json

                value = json.dumps(value)
            return self.encrypted_type.process_bind_param(value, dialect)
        return value

    def process_result_value(self, value, dialect):
        """Decrypt and parse JSON string back to dict."""
        if value is not None:
            decrypted = self.encrypted_type.process_result_value(value, dialect)
            if decrypted is not None:
                try:
                    import json

                    return json.loads(decrypted)
                except json.JSONDecodeError:
                    return decrypted
        return value

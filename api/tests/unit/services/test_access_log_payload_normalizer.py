"""Unit tests for the access-log payload normalizer.

Legacy rows in ``access_audit_log`` were written when the asyncpg JSONB
codec was not idempotent, so a Python ``dict`` got serialized twice and
stored as a JSON-stringified-dict. Pydantic later refused those rows and
the read endpoint returned 500, leaving the admin UI with an empty table.

The normalizer in ``routes.admin.access_log`` parses string payloads on
read so the endpoint serves legacy rows alongside the new dict rows.
"""

from __future__ import annotations

import pytest


@pytest.mark.unit
class TestNormalizePayload:
    def test_dict_passes_through(self):
        from routes.admin.access_log import _normalize_payload

        payload = {"email": "u@e.com", "client_id": None}
        assert _normalize_payload(payload) == payload

    def test_none_becomes_empty_dict(self):
        from routes.admin.access_log import _normalize_payload

        assert _normalize_payload(None) == {}

    def test_json_string_is_parsed(self):
        from routes.admin.access_log import _normalize_payload

        legacy = '{"email": "ivan@example.com", "client_id": null}'
        assert _normalize_payload(legacy) == {
            "email": "ivan@example.com",
            "client_id": None,
        }

    def test_invalid_json_string_wrapped_under_raw(self):
        from routes.admin.access_log import _normalize_payload

        assert _normalize_payload("not json") == {"_raw": "not json"}

    def test_non_object_json_wrapped_under_raw(self):
        from routes.admin.access_log import _normalize_payload

        # A JSON array is valid JSON but not a dict — payload schema needs
        # an object, so we wrap to keep the schema happy without dropping
        # the data outright.
        assert _normalize_payload("[1, 2, 3]") == {"_raw": [1, 2, 3]}

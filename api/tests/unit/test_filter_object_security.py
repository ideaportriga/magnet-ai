"""Regression tests for FilterObject SQLi hardening (BACKEND_FIXES_ROADMAP.md §A.4).

FilterObject feeds metadata_filter_builder implementations (pgvector, oracle)
that interpolate field names directly into SQL / JSON path expressions. The
hardening adds a strict identifier whitelist at the Pydantic boundary — these
tests pin that behaviour so a future "just make it work" change can't
re-introduce the injection surface.
"""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from type_defs.pagination import FilterObject, PaginationBase


class TestFilterObjectFieldNameValidation:
    def test_valid_simple_field(self):
        obj = FilterObject.model_validate({"status": {"$eq": "active"}})
        assert obj is not None

    def test_valid_nested_field(self):
        FilterObject.model_validate({"user.profile.age": {"$gt": 18}})

    def test_valid_field_with_hyphen(self):
        FilterObject.model_validate({"content-type": {"$eq": "pdf"}})

    def test_valid_logical_operators(self):
        FilterObject.model_validate(
            {"$and": [{"a": {"$eq": 1}}, {"$or": [{"b": {"$eq": 2}}]}]}
        )

    @pytest.mark.parametrize(
        "payload",
        [
            {"foo' OR '1'='1": {"$eq": "bar"}},
            {"metadata')--": {"$exists": True}},
            {"a; DROP TABLE users;--": {"$eq": 1}},
            {"' UNION SELECT null,null--": {"$eq": 1}},
            {'name" OR "a"="a': {"$eq": 1}},
            {"a b": {"$eq": 1}},  # spaces not allowed
            {"": {"$eq": 1}},  # empty rejected
            {"1field": {"$eq": 1}},  # must start with letter/underscore
        ],
    )
    def test_field_name_injection_rejected(self, payload):
        with pytest.raises((ValidationError, ValueError)):
            FilterObject.model_validate(payload)

    def test_injection_in_nested_and_rejected(self):
        with pytest.raises((ValidationError, ValueError)):
            FilterObject.model_validate({"$and": [{"foo' OR 1=1--": {"$eq": "x"}}]})


class TestPaginationLimitCap:
    """Regression for §A.1 — limit must be capped server-side."""

    def test_limit_above_cap_rejected(self):
        with pytest.raises(ValidationError):
            PaginationBase(limit=10_000)

    def test_limit_at_cap_accepted(self):
        PaginationBase(limit=1000)

    def test_zero_limit_rejected(self):
        with pytest.raises(ValidationError):
            PaginationBase(limit=0)

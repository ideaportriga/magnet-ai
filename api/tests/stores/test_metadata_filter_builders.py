
from stores.oracle.metadata_filter_builder import OracleMetadataFilterBuilder
from stores.pgvector_db.metadata_filter_builder import PgVectorMetadataFilterBuilder
from type_defs.pagination import FilterObject


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _pg_build(filter_dict: dict, field_mapping: dict | None = None) -> str:
    """Build a PgVector filter expression from a raw dict."""
    builder = PgVectorMetadataFilterBuilder()
    fo = FilterObject.model_validate(filter_dict)
    config = {"metadata_config": None}
    if field_mapping:
        config["metadata_config"] = [
            {"enabled": True, "name": k, "mapping": v} for k, v in field_mapping.items()
        ]
    return builder.build(config, fo)


def _ora_build(filter_dict: dict, field_mapping: dict | None = None) -> str:
    """Build an Oracle filter expression from a raw dict."""
    builder = OracleMetadataFilterBuilder()
    fo = FilterObject.model_validate(filter_dict)
    config = {"metadata_config": None}
    if field_mapping:
        config["metadata_config"] = [
            {"enabled": True, "name": k, "mapping": v} for k, v in field_mapping.items()
        ]
    return builder.build(config, fo)


# ===========================================================================
# PgVector tests — null handling
# ===========================================================================


class TestPgVectorNullHandling:
    def test_in_with_null_and_value(self):
        result = _pg_build({"$and": [{"org": {"$in": ["Finland", None]}}]})
        assert "IS NULL" in result
        assert "@>" in result
        assert "OR" in result

    def test_in_with_only_null(self):
        result = _pg_build({"org": {"$in": [None]}})
        assert "IS NULL" in result

    def test_in_with_multiple_values_and_null(self):
        result = _pg_build({"org": {"$in": ["Finland", "Sweden", None]}})
        assert "IS NULL" in result
        assert result.count("@>") == 2

    def test_nin_with_null_and_value(self):
        result = _pg_build({"$and": [{"org": {"$nin": ["Finland", None]}}]})
        assert "IS NOT NULL" in result
        assert "NOT" in result
        assert "AND" in result

    def test_nin_with_only_null(self):
        result = _pg_build({"org": {"$nin": [None]}})
        assert "IS NOT NULL" in result

    def test_in_empty_list(self):
        result = _pg_build({"org": {"$in": []}})
        assert result == "FALSE"

    def test_nin_empty_list(self):
        result = _pg_build({"org": {"$nin": []}})
        assert result == "TRUE"


# ===========================================================================
# PgVector tests — array metadata field support (JSONB containment @>)
# ===========================================================================


class TestPgVectorArrayMetadata:
    def test_eq_uses_containment(self):
        """$eq should use @> to match both scalar and array metadata values."""
        result = _pg_build({"manufacturer": {"$eq": "KONECRANES"}})
        assert "@>" in result
        assert "'\"KONECRANES\"'::jsonb" in result

    def test_ne_uses_not_containment(self):
        """$ne should use NOT @> to support array metadata values."""
        result = _pg_build({"manufacturer": {"$ne": "KONECRANES"}})
        assert "NOT" in result
        assert "@>" in result

    def test_in_uses_containment(self):
        """$in should use @> for each value."""
        result = _pg_build({"org": {"$in": ["Finland", "Sweden"]}})
        assert result.count("@>") == 2
        assert "'\"Finland\"'::jsonb" in result
        assert "'\"Sweden\"'::jsonb" in result

    def test_nin_uses_not_containment(self):
        """$nin should use NOT @> for each value."""
        result = _pg_build({"org": {"$nin": ["Finland", "Sweden"]}})
        assert result.count("NOT") == 2
        assert result.count("@>") == 2

    def test_gt_still_uses_text_extraction(self):
        """$gt and other comparison ops should still use ->> text extraction."""
        result = _pg_build({"age": {"$gt": 25}})
        assert "->>" in result
        assert ">" in result
        assert "@>" not in result

    def test_eq_with_numeric(self):
        result = _pg_build({"count": {"$eq": 5}})
        assert "@>" in result
        assert "'5'::jsonb" in result

    def test_eq_with_field_mapping(self):
        result = _pg_build(
            {"manufacturer": {"$eq": "KONECRANES"}},
            field_mapping={"manufacturer": "source.manufacturer"},
        )
        assert "@>" in result
        assert "'\"KONECRANES\"'::jsonb" in result


# ===========================================================================
# Oracle tests — null handling
# ===========================================================================


class TestOracleNullHandling:
    def test_in_with_null_and_value(self):
        result = _ora_build({"$and": [{"org": {"$in": ["Finland", None]}}]})
        assert "!(exists(@.org))" in result
        assert "[*]" in result

    def test_in_with_only_null(self):
        result = _ora_build({"org": {"$in": [None]}})
        assert "!(exists(@.org))" in result

    def test_nin_with_null_and_value(self):
        result = _ora_build({"$and": [{"org": {"$nin": ["Finland", None]}}]})
        assert "exists(@.org)" in result
        assert "[*]" in result

    def test_nin_with_only_null(self):
        result = _ora_build({"org": {"$nin": [None]}})
        assert "exists(@.org)" in result

    def test_in_empty_list(self):
        result = _ora_build({"org": {"$in": []}})
        assert "1 == 0" in result

    def test_nin_empty_list(self):
        result = _ora_build({"org": {"$nin": []}})
        assert "1 == 1" in result


# ===========================================================================
# Oracle tests — array metadata field support ([*] wildcard)
# ===========================================================================


class TestOracleArrayMetadata:
    def test_eq_uses_wildcard(self):
        """$eq should use [*] to match both scalar and array metadata values."""
        result = _ora_build({"manufacturer": {"$eq": "KONECRANES"}})
        assert '@.manufacturer[*] == "KONECRANES"' in result

    def test_ne_uses_negated_wildcard(self):
        """$ne should use !([*] ==) to support array metadata values."""
        result = _ora_build({"manufacturer": {"$ne": "KONECRANES"}})
        assert '!(@.manufacturer[*] == "KONECRANES")' in result

    def test_in_uses_wildcard(self):
        """$in should use [*] for each value."""
        result = _ora_build({"org": {"$in": ["Finland", "Sweden"]}})
        assert '@.org[*] == "Finland"' in result
        assert '@.org[*] == "Sweden"' in result

    def test_nin_uses_negated_wildcard(self):
        """$nin should use negated [*] for each value."""
        result = _ora_build({"org": {"$nin": ["Finland", "Sweden"]}})
        assert '!(@.org[*] == "Finland")' in result
        assert '!(@.org[*] == "Sweden")' in result

    def test_gt_still_uses_direct_path(self):
        """$gt and other comparison ops should still use direct path."""
        result = _ora_build({"age": {"$gt": 25}})
        assert "@.age > 25" in result
        assert "[*]" not in result


# ===========================================================================
# FilterObject model_dump preserves null in lists
# ===========================================================================


class TestFilterObjectNullPreservation:
    def test_null_in_list_survives_model_dump_with_exclude_none(self):
        fo = FilterObject.model_validate(
            {"$and": [{"org": {"$in": ["Finland", None]}}]}
        )
        dumped = fo.model_dump(exclude_none=True, by_alias=True)
        in_list = dumped["$and"][0]["org"]["$in"]
        assert None in in_list

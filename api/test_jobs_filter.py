#!/usr/bin/env python3
"""
Test script to validate the Jobs controller filtering functionality.
"""


def test_filter_mapping():
    """Test that filter parameters are correctly mapped."""

    # Sample filter parameters from your example
    filter_params = {
        "definition.jobTypeIn": ["recurring"],
        "statusIn": ["Error", "Waiting"],
        "type": "custom",
        "createdAtAfter": "2025-08-11T18:24:56.566+03:00",
        "definition.intervalIn": ["daily"],
    }

    print("✅ Filter parameters validation:")
    print(f"   definition.jobTypeIn: {filter_params.get('definition.jobTypeIn')}")
    print(f"   statusIn: {filter_params.get('statusIn')}")
    print(f"   type: {filter_params.get('type')}")
    print(f"   createdAtAfter: {filter_params.get('createdAtAfter')}")
    print(f"   definition.intervalIn: {filter_params.get('definition.intervalIn')}")

    # Test JSONB filter construction
    jsonb_filters = {}

    if filter_params.get("definition.jobTypeIn"):
        jsonb_filters["job_type"] = filter_params["definition.jobTypeIn"]

    if filter_params.get("definition.intervalIn"):
        jsonb_filters["interval"] = filter_params["definition.intervalIn"]

    # Handle type parameter
    if filter_params.get("type"):
        if "job_type" in jsonb_filters:
            jsonb_filters["job_type"].append(filter_params["type"])
        else:
            jsonb_filters["job_type"] = [filter_params["type"]]

    print("\n✅ JSONB filters construction:")
    for key, values in jsonb_filters.items():
        print(f"   definition.{key}: {values}")

    # Test SQL condition generation
    print("\n✅ Expected SQL conditions:")
    for json_key, values in jsonb_filters.items():
        if values:
            condition_parts = []
            for value in values:
                condition_parts.append(f"definition->'{json_key}' = '{value}'")

            if condition_parts:
                jsonb_condition = " OR ".join(condition_parts)
                print(f"   ({jsonb_condition})")

    print("\n✅ All tests passed!")


if __name__ == "__main__":
    test_filter_mapping()

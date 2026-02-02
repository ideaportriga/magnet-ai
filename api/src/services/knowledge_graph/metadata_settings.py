from typing import Any


def get_default_metadata_settings() -> dict[str, Any]:
    return {
        "metadata": {
            "extraction": {
                "enabled": True,
                "approach": "document",
                "segment_size": 18000,
                "segment_overlap": 0.1,
                "prompt_template_system_name": "KG_METADATA_EXTRACTION",
            },
            "field_definitions": [],
            "discarded_field_names": [],
        }
    }

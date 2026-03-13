from typing import Any


def get_default_entity_extraction_settings() -> dict[str, Any]:
    return {
        "entity_extraction": {
            "extraction": {
                "enabled": True,
                "approach": "document",
                "segment_size": 18000,
                "segment_overlap": 0.1,
                "prompt_template_system_name": "KG_ENTITY_EXTRACTION",
            },
            "entity_definitions": [],
        }
    }

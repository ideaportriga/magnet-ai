from typing import Any


def get_default_entity_extraction_settings() -> dict[str, Any]:
    return {
        "entity_extraction": {
            "extraction": {
                "enabled": True,
                "approach": "document",
                "mode": "basic",
                "segment_size": 18000,
                "segment_overlap": 0.1,
                "max_extraction_iterations": 3,
                "schema_format": "typescript",
                "prompt_template_system_name": "KG_ENTITY_EXTRACTION",
                "analysis_prompt_template_system_name": "KG_ENTITY_EXTRACTION_ANALYSIS",
                "reflective_prompt_template_system_name": "KG_ENTITY_EXTRACTION_REFLECTIVE",
                "self_tuning_prompt_template_system_name": "KG_ENTITY_EXTRACTION_SELF_TUNING",
                "self_tuning_analysis_prompt_template_system_name": "KG_ENTITY_EXTRACTION_SELF_TUNING_ANALYSIS",
            },
            "performance_optimizations": {
                "relevance_filter": {
                    "prompt_template_system_name": "",
                },
            },
            "entity_definitions": [],
        }
    }

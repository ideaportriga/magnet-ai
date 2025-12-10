from typing import Any


def get_default_retrieval_settings() -> dict[str, Any]:
    return {
        "retrieval_variant": "base_variant",
        "retrieval_tools": {
            "findDocumentsBySummarySimilarity": {
                "description": "Find documents by summary similarity",
                "enabled": True,
                "searchControl": "configuration",
                "searchMethod": "vector",
                "scoreThreshold": 0.7,
                "limit": 5,
                "hybridWeight": 0.5,
            },
            "findChunksBySimilarity": {
                "description": "Find chunks by similarity",
                "enabled": True,
                "searchControl": "configuration",
                "searchMethod": "vector",
                "scoreThreshold": 0.7,
                "limit": 5,
                "hybridWeight": 0.5,
            },
            "exit": {
                "description": "Exit the tool call loop",
                "enabled": True,
                "maxIterations": 4,
                "answerMode": "answer_with_sources",
                "outputFormat": "markdown",
            },
        },
    }

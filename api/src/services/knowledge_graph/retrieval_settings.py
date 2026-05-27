from typing import Any


def get_default_retrieval_settings() -> dict[str, Any]:
    return {
        "retrieval_variant": "base_variant",
        "retrieval_tools": {
            "findDocumentsByMetadata": {
                "description": "Filter documents by their metadata fields",
                "enabled": True,
                # can be: agent | collaborative | external
                "searchControl": "collaborative",
                # can be: merge_and | merge_or | agent_priority | external_priority
                "filterMergeStrategy": "merge_and",
            },
            "findDocumentsBySummarySimilarity": {
                "description": "Find documents by summary similarity",
                "enabled": True,
                "searchMethod": "hybrid",
                "scoreThreshold": 0,
                "limit": 5,
                "rrfK": 60,
            },
            "retrieveChunks": {
                "description": "Searches the document corpus for passages relevant to an information need. You don't need to think about retrieval mechanics - just describe what you're looking for.",
                "enabled": True,
                "searchMethod": "hybrid",
                "scoreThreshold": 0,
                "limit": 5,
                "rrfK": 60,
                # Candidates each sub-query fetches before RRF fusion (hybrid/keyword).
                "candidatePoolSize": 30,
                # Number of query variants reformulation produces per search type.
                "keywordVariants": 1,
                "vectorVariants": 1,
                "promptTemplateName": "KG_CHUNK_QUERY_REFORMULATION",
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

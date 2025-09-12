json
{
  "_id": {
    "$oid": "66f15844a0a7015adc495039"
  },
  "retrieve": {
    "collection_system_names": [
      "Magnet_AI_Manual"
    ],
    "similarity_score_threshold": 0.75,
    "max_chunks_retrieved": 5,
    "chunk_context_window_expansion_size": 1
  },
  "ui_settings": {
    "header_configuration": {
      "header": "",
      "sub_header": ""
    },
    "user_fideback": false,
    "show_link_titles": false,
    "offer_to_bypass_cache": false,
    "sample_questions": {
      "enabled": true,
      "questions": {
        "question1": "Adding RAG Tools",
        "question2": "Creating Knowledge Sources",
        "question3": "Deleting AI Apps"
      }
    }
  },
  "language": {
    "detect_question_language": {
      "enabled": false,
      "prompt_template": "RAG_TOOL_DETECT_LANGUAGE"
    },
    "multilanguage": {
      "enabled": false,
      "source_language": "English",
      "prompt_template_translation": "RAG_TOOL_TRANSLATE_TEXT"
    }
  },
  "system_name": "MAGNET_RETRIEVAL_TOOL",
  "name": "Magnet retrieval tool",
  "description": "Magnet retrieval tool",
  "_metadata": {
    "created_at": {
      "$date": "2024-09-23T12:00:04.799Z"
    },
    "modified_at": {
      "$date": "2024-10-15T14:01:47.866Z"
    }
  }
}
```json
{
  "_id": {
    "$oid": "67a33513142d8f4e00dc14a9"
  },
  "variants": [
    {
      "retrieve": {
        "collection_system_names": [
          "MAGNET_AI_MANUAL_-_HUBSPOT_PDF"
        ],
        "similarity_score_threshold": 0.51,
        "max_chunks_retrieved": 5,
        "chunk_context_window_expansion_size": 0,
        "rerank": {
          "enabled": false,
          "model": "",
          "top_n": 5,
          "return_documents": false,
          "truncation": false,
          "max_chunks_retrieved": 5
        }
      },
      "generate": {
        "prompt_template": "QA_SYSTEM_PROMPT_TEMPLATE_COPY"
      },
      "post_process": {
        "answered_check": {
          "enabled": false,
          "prompt_template": "Q&A_RESPONSE_CHECK"
        },
        "detect_question_language": {
          "enabled": false,
          "prompt_template": "RAG_TOOL_DETECT_LANGUAGE"
        },
        "check_is_hallucinate": {
          "enabled": false,
          "prompt_template": "QA_HALLUCINATION_CHECK"
        },
        "categorization": {
          "enabled": false,
          "prompt_template": "POST_PROCESS",
          "categories": [
            "RAG Tool",
            "Retrieval Tool",
            "Prompt Template",
            "Knowledge Source",
            "AI App",
            "Other"
          ]
        },
        "enabled": true
      },
      "ui_settings": {
        "header_configuration": {
          "header": "",
          "sub_header": ""
        },
        "user_fideback": true,
        "show_link_titles": false,
        "offer_to_bypass_cache": false,
        "sample_questions": {
          "enabled": true,
          "questions": {
            "question1": "What does a RAG Tool do?",
            "question2": "What does a Prompt Template do?",
            "question3": "How to configure AI App?"
          }
        }
      },
      "sample_test_set": null,
      "language": {
        "detect_question_language": {
          "enabled": false,
          "prompt_template": "RAG_TOOL_DETECT_LANGUAGE"
        },
        "multilanguage": {
          "enabled": true,
          "source_language": "English",
          "prompt_template_translation": "RAG_TOOL_TRANSLATE_TEXT"
        }
      },
      "variant": "variant_1",
      "description": null
    }
  ],
  "active_variant": "variant_1",
  "system_name": "MAGNET_AI_MANUAL_HUBSPOT",
  "name": "Magnet AI Manual (Hubspot)",
  "description": "",
  "_metadata": {
    "created_at": {
      "$date": "2025-02-05T09:53:23.726Z"
    },
    "modified_at": {
      "$date": "2025-04-16T07:00:22.776Z"
    }
  }
}
```
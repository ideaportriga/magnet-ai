```json
{
  "_id": {
    "$oid": "679a1198e71dc907fb264620"
  },
  "name": "LLM chat completion request",
  "type": "chat-completion",
  "start_time": {
    "$date": "2025-01-29T11:31:35.878Z"
  },
  "end_time": {
    "$date": "2025-01-29T11:31:39.890Z"
  },
  "latency": 4011.8729999999996,
  "status": "success",
  "status_message": null,
  "metadata": {},
  "description": null,
  "model": {
    "name": "AZURE_GPT-4O",
    "display_name": "Azure OpenAI GPT 4o",
    "provider": "azure_open_ai",
    "provider_display_name": "Azure Open AI",
    "parameters": {
      "llm": "gpt-4o",
      "temperature": 0,
      "top_p": 1,
      "max_tokens": null,
      "response_format": {
        "type": "json_object"
      },
      "tools": null,
      "top_n": null
    }
  },
  "input": [
    {
      "role": "system",
      "content": "You are an AI assistant analyzing a customer-service agent conversation. Your task is to classify the interaction based on the full conversation history, including the most recent message, to determine the topic or provide an alternative classification. Use the conversation history to identify whether the most recent user message depends on prior context or stands independently. Depending on the classification, you may also suggest a response message for the assistant.\n\nInputs:\nConversation History: A list of messages between the customer and the service agent, with the most recent message included at the end. Each message is an object with \"role\" and \"content\". The \"role\" is either \"user\" (for customer messages) or \"assistant\" (for service agent messages), and the \"content\" is the message text.\nTopics:\n```json\n[{'system_name': 'demo', 'name': 'Topic for answering all enquiries', 'description': 'Use this topic to answer user questions on general GMC policies, operations, contact details as well as contact and agreement data.'}]\n\n```\n\nSpecial Classifications: Use these enum values when no topics applies:\ngreeting: The user message is a greeting or introductory comment.\nfarewell: The user message is a goodbye or conclusion.\noff_topic: The message is irrelevant or unrelated to the listed topics.\nrequest_not_clear: The user’s request is ambiguous or lacks sufficient detail.\nother: For messages that do not fit into any predefined categories or classifications.\n\njson schema:\n```json\n{\n    \"type\": \"object\",\n    \"properties\": {\n      \"intent\": {\n        \"type\": \"string\",\n        \"enum\": [\n          \"topic\",\n          \"greeting\",\n          \"farewell\",\n          \"off_topic\",\n          \"request_not_clear\",\n          \"other\"\n        ],\n        \"description\": \"The selected classification category.\"\n      },\n      \"topic\": {\n        \"type\": [\n          \"string\",\n          \"null\"\n        ],\n        \"enum\": [\n          ['demo']\n        ],\n        \"description\": \"The system name of the selected topic, or null if not applicable.\"\n      },\n      \"reason\": {\n        \"type\": \"string\",\n        \"description\": \"Explanation of why this classification or topic was chosen.\"\n      },\n      \"assistant_message\": {\n        \"type\": [\n          \"string\",\n          \"null\"\n        ],\n        \"description\": \"The suggested response for the assistant to send to the user, or null if classification is 'topic'.\"\n      }\n    },\n    \"additionalProperties\": false,\n    \"required\": [\n      \"intent\",\n      \"reason\",\n      \"assistant_message\"\n    ]\n}\n```"
    },
    {
      "role": "user",
      "content": "[\n  {\n    \"role\": \"user\",\n    \"content\": \"Hello!\"\n  }\n]"
    }
  ],
  "output": "{\n    \"intent\": \"greeting\",\n    \"topic\": null,\n    \"reason\": \"The user's message is a simple greeting without any specific inquiry or context.\",\n    \"assistant_message\": \"Hello! How can I assist you today?\"\n}",
  "usage_details": {
    "input": 560,
    "input_details": {
      "units": "tokens",
      "standard": 560,
      "cached": 0
    },
    "output": 50,
    "output_details": {
      "units": "tokens",
      "standard": 50,
      "reasoning": 0
    },
    "total": 610
  },
  "cost_details": {
    "input": 0.0014000000000000002,
    "input_details": {
      "standard": 0.0014000000000000002,
      "cached": 0
    },
    "output": 0.0005,
    "output_details": {
      "standard": 0.0005,
      "reasoning": 0
    },
    "total": 0.0019000000000000002
  },
  "prompt_template": {
    "name": "DEFAULT_AGENT_CLASSIFICATION",
    "display_name": "Default Agent Classification",
    "description": "Classify user's interaction",
    "variant": "variant_4",
    "text": "You are an AI assistant analyzing a customer-service agent conversation. Your task is to classify the interaction based on the full conversation history, including the most recent message, to determine the topic or provide an alternative classification. Use the conversation history to identify whether the most recent user message depends on prior context or stands independently. Depending on the classification, you may also suggest a response message for the assistant.\n\nInputs:\nConversation History: A list of messages between the customer and the service agent, with the most recent message included at the end. Each message is an object with \"role\" and \"content\". The \"role\" is either \"user\" (for customer messages) or \"assistant\" (for service agent messages), and the \"content\" is the message text.\nTopics:\n```json\n{TOPIC_DEFINITIONS}\n\n```\n\nSpecial Classifications: Use these enum values when no topics applies:\ngreeting: The user message is a greeting or introductory comment.\nfarewell: The user message is a goodbye or conclusion.\noff_topic: The message is irrelevant or unrelated to the listed topics.\nrequest_not_clear: The user’s request is ambiguous or lacks sufficient detail.\nother: For messages that do not fit into any predefined categories or classifications.\n\njson schema:\n```json\n{\n    \"type\": \"object\",\n    \"properties\": {\n      \"intent\": {\n        \"type\": \"string\",\n        \"enum\": [\n          \"topic\",\n          \"greeting\",\n          \"farewell\",\n          \"off_topic\",\n          \"request_not_clear\",\n          \"other\"\n        ],\n        \"description\": \"The selected classification category.\"\n      },\n      \"topic\": {\n        \"type\": [\n          \"string\",\n          \"null\"\n        ],\n        \"enum\": [\n          {TOPIC_SYSTEM_NAMES}\n        ],\n        \"description\": \"The system name of the selected topic, or null if not applicable.\"\n      },\n      \"reason\": {\n        \"type\": \"string\",\n        \"description\": \"Explanation of why this classification or topic was chosen.\"\n      },\n      \"assistant_message\": {\n        \"type\": [\n          \"string\",\n          \"null\"\n        ],\n        \"description\": \"The suggested response for the assistant to send to the user, or null if classification is 'topic'.\"\n      }\n    },\n    \"additionalProperties\": false,\n    \"required\": [\n      \"intent\",\n      \"reason\",\n      \"assistant_message\"\n    ]\n}\n```"
  }
}
```
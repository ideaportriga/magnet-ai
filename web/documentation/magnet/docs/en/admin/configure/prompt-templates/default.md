### Default Prompt Templates

Magnet AI comes with some default Prompt Templates that are critically important for other tools like RAG Tools and Agents, as well as execute post-processing tasks. Some of them include placeholders for specific variables that are enclosed in curly braces.

**Important:** Make sure you do not change or remove any of such placeholders.

- QA_SYSTEM_PROMPT_TEMPLATE
  Used by: RAG Tool
  Default Prompt Template for response generation, specifically tuned for OpenAI models.
  `{context}` : placeholder for retrieved context (chunks of content).
- RAG_TOOL_DETECT_LANGUAGE
  Used by: RAG Tool, Retrieval Tool
  Default Prompt Template for language detection for multi-lingual use cases.
- RAG_TOOL_TRANSLATE_TEXT
  Used by: RAG Tool, Retrieval Tool
  Default Prompt for translation in multi-lingual use cases.
  `{source_language}` : placeholder for source language in translation flow
  `{target_language}` : placeholder for target language in translation flow
- POST_PROCESS
  Used by: RAG Tool
  Default Prompt Template for post-processing of RAG Tool response. Ensures correct metrics are collected for the Usage reports/dashboards.
  `{CATEGORIES}` : placeholder for question categories (topics). Category values are configured per each RAG Tool via UI.
- DEFAULT_AGENT_CLASSIFICATION
  Used by: Agent
  Default Prompt Template for Topic selection in Agents. Also detects other types of user intent like greeting/farewell or off-topic. An LLM that supports JSON mode must be used for this Prompt Template.
  `{TOPIC_DEFINITIONS}` : placeholder for each Topic’s name, system name, and LLM description.
- DEFAULT_AGENT_TOPIC_PROCESSING
  Used by: Agent
  Default Prompt Template for Topic processing and tool calling after the Topic has been selected. An LLM that supports Tool Calling must be used for this Prompt Template.
  `{TOPIC_NAME}` : placeholder for the selected topic name.
  `{TOPIC_INSTRUCTIONS}` : placeholder for additional/advanced instructions that can be configured on Topic level.
- PASS
  Used by: Agent
  Specific Topic Selection Prompt Template for the cases when there is only 1 topic in an Agent. Use it to avoid extra call to the LLM.
  Instructions for this Prompt Template are blank.
- DEFAULT_AGENT_TOPIC_PROCESSING
  Used by: Agent
  Default Prompt Template for post-processing of Agent conversations. Detects metrics like conversation sentiment and resolution status.
  `{CONVERSATION}` : the entire conversation between Agent and user.

# RAG Tools

**RAG** stands for **Retrieval-augmented generation**, a technique that enhances LLM responses by retrieving relevant information from a specified knowledge base before generating an answer.

RAG tools answer user questions by embedding them into a vector store, semantically searching for related vectorized data and generating a response grounded in retrieved data. Most common use case for RAG Tools is a Q&A system.

RAG Tools cannot exist without [Knowledge Sources](../../../en/admin/connect/knowledge-sources/overview.md) (otherwise the LLMs would make up their own answers to user questions) and [Prompt Templates](../prompt-templates/overview.md), that determine the format, structure, and versatilty of the LLM responses. Also, Prompt Templates optionally ensure on-the-fly content translation and post-processing of RAG queries.

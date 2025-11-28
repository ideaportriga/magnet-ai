# Overview

In this tutorial, we will be building a Q&A Agent that answers users’ questions by searching a knowledge base. You will also learn how to evaluate the Q&A part of Agent and monitor the Agent's performance.

Let’s start by understanding the assets necessary for configuring the Agent.

- **LLM’s** that support JSON mode and tool calling for the Agent Prompt Templates to work correctly. Let’s assume you’ve got them deployed and added to the Models library in Magnet AI. [Learn more](../../../admin/connect/models/adding-models.md) about adding models.

- A **Knowledge Source** that the Agent will ground its answers in.

- Some **Prompt Templates** that will orchestrate the Agent, generate answers, and post-process outputs. We will be using default Prompt Templates provided with Magnet AI.

- A **RAG Tool** to give the Agent the ability to answer from knowledge base.

- An **Agent** itself that will be using this RAG Tool as an action.

- Optionally - a **Test Set** with sample inputs and expected outputs to evaluate the RAG Tool before making it live.

- An **AI App** to deliver the Agent UI to end users in a low-code way. Alternatively, the Agent can be called via API.

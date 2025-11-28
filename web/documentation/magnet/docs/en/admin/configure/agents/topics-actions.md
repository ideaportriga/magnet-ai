# Agents: Topics and Actions

## Topics

A key building block of an Agent in Magnet AI is the **Topic**. 

Topics group together related Actions (these correpospond to tools in common Gen AI terminology). Some examples of Topics for a service-oriented Agent could be “Order Management”, “Account Management”, “Refunds and Returns”. The "Order Management" topic could contain actions like Cancel Order, Get Orders, Update order, and so on. 

The scope of each Topic depends on the use case and general Agent scope. Open AI [recommends using up to 20 tools](https://platform.openai.com/docs/guides/function-calling?api-mode=responses#best-practices-for-defining-functions) at a time, which translates to up to 20 Actions in a Topic, but according to the source, it is just a soft suggestion.

Make sure each of your Topics has a comprehensive description for the LLM, so that the Agent can decide when to use each Topic.

## Actions

While Topics serve to detect user intent and route the Agent, the actual tool calling capability happens on the **Action** level. 

Objects that can be used as Agent Actions are: 

- API Tools

- MCP Tools

- RAG Tools

- Retrieval Tools

- Prompt Templates.
  
  Here are some examples of Actions and tool types behind them:

- Update customer’s contact information: **API Tool**

- Answer user query using a Knowledge source: **RAG Tool** or **Retrieval Tool**

- Summarize given context: **Prompt Template**

It is critically important to have detailed and accurate LLM descriptions for your Agent's Actions. The LLM will also look at Action parameters and their descriptions, if there are any provided. 

# Agents: Topics and Actions

## Topics

A key building block of an Agent is the **Topic**. 

Topics group together related Actions (also known as tools in the Gen AI industry). Some examples of Topics could be “Order Management”, “Account Management”, “Refunds and Returns”. The "Order Management" topic could contain actions like Cancel Order, Get Orders, Update order. 

The scope of each Topic depends on the use case and general Agent scope. Open AI [recommends using up to 20 tools](https://platform.openai.com/docs/guides/function-calling?api-mode=responses#best-practices-for-defining-functions) at a time, which translates to up to 20 Actions in a Topic, but according to the source, it is just a soft suggestion.

Make sure each of your Topics has a comprehensive description for the LLM, so that the Agent can decide when to use each Topic.

## Actions

While Topics serve to detect user intent and route the Agent, the actual tool calling capability happens on the **Action** level. 

Objects that can be used as Agent Actions: 

- API Tools

- RAG Tools

- Retrieval Tools

- Prompt Templates.
  
  
  Here are some examples of Actions and tool types behind them:

- Update customer’s contact information: **API Tool**

- Answer a user query from a Knowledge source: **RAG Tool**

- Retrieve links to content without generating text: **Retrieval Tool**

- Summarize a record: **Prompt Template**


For Actions to function well, it is critical to have detailed and accurate LLM descriptions. The LLM may also look at Action parameters and their descriptions, if there are any. This can be especially important in case of API tool-based Actions where certain parameters must be passed in order to call the function.



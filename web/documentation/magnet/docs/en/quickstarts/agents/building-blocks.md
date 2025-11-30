# Building Blocks of the Agent

## How Agents work in Magnet AI

Agents in Magnet AI typically process user queries in two steps:

1. Analyze user input to identify intent and select a matching Topic
2. Process selected Topic and call one or multiple Actions inside it.

---

### Building blocks of the Agent

#### 📂 Topics

Topic is a subject, or area of Agent's capabilities. Some examples of Topics could be “Order management”, “Refunds and returns”, or “Account management”, but the granularity of Topics can vary depending on specific use case. It is important to have an effective description of each Topic, because this is what the LLM uses to select relevant Topics.

#### 🎫 Actions

Actions are tools inside a Topic that can be called to process user query. Actions can have parameters that need to be populated before the according function is called (for example, these parameters could be a record ID, a field value, etc). Ideally, both the Action itself and its parameters should have descriptions to enable the LLM to process Actions more accurately.

#### ✨ Subject selection Prompt Template

These are instructions for the Agent on how to identify a Topic as well as handle cases when no Topic has been identified. This Prompt Template model must support _JSON mode_.

#### 📝 Topic processing Prompt Template

These are general instructions on how to process Topics that apply to all Topics across Agent. This Prompt Template model must support _tool calling_.

## Conversations

Threads of user and assistant (Agent) messages linked together with a unique ID are called **Conversations**. These are stored in Magnet AI for a limited period of time and can be used for debugging and reports. By analyzing past Conversations, you can identify gaps, improve your Agent, and reduce its costs and latency.

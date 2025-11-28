# Agents

## The principles of Agentic flow

Agents are considered the next step of Gen AI evolution. They generally share 4 core traits:

<div class="grid-container">
    <div class="grid-item">Reasoning</div>
    <div class="grid-item">Tool usage</div>
    <div class="grid-item">Orchestration</div>
    <div class="grid-item">Memory</div>
</div>

The key enabler of agentic flow is **Tool calling** (Function calling).

An Agent is equipped with tools, or **Actions**, as they are called in Magnet AI, which can be generated from [RAG Tools](../rag-tools/overview.md), API Tools, [Retrieval Tools](../retrieval-tools/overview.md), and [Prompt Templates](../prompt-templates/overview.md). 

## How the Agentic flow works with tool calling:

1. Agent receives and analyzes user input, which could be something like *“I want to cancel my order”* or *“What is the return policy for product X”.*
2. Agent detects user intent, and if it matches a specific Topic, Agent proceeds to Topic execution using provided instructions.
3. During Topic processing step the Agent decides whether it can use one or multiple Actions to answer user’s query.
4. If it finds a matching Action, it checks whether all inputs are provided to execute the Action, and asks for missing values if necessary. Some examples of such inputs could be a record ID or a field value.
5. Agent passes all required inputs to the function, and the function is called by the backend.
6. Agent returns function call outputs to the user, wrapping them in a user-friendly message.

## Gen AI Agents vs Workflows

You might be wondering how Agents with tool calling abilities are different from workflow-based Agents. The key difference is that in workflows, sequence of actions is pre-determined, while tool calling gives Agents the autonomy to dynamically decide about the optimal trajectory.

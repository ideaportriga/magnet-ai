# Agents

Agents in Magnet AI use the tool (function) calling ability of the LLMs to orchestrate their work and dynamically generate workflows based on given context.

While Gen AI Agents are quite complex systems, Magnet AI enables admins to configure and deploy agentic flows through a low-code interface.

Frequent use cases for agentic flows include customer email processing and customer case resolution.

## Sample use case

For example, to process a simple customer case where a customer is asking to change their contact information, the Agent would first understand user intent, then, using provided context, it would retrieve customer's contact information and update the necessary fields, then it might draft a response for the customer and post-process the case (generate case summary, mark as done, etc).

For actions that require human oversight, such as updating data, Agents can request confirmation before proceeding. In this example, the Agent could first present the suggested contact information updates to the user and only apply the changes once they are approved.

[Learn more](/docs/en/quickstarts/agents/overview.html) about how Agents work in Magnet AI.

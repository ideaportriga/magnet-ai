# Using Prompt Templates

## Using Prompt Templates in other Magnet AI tools

Magnet AI is shipped with a set of [default Prompt Templates](../../../en/admin/configure/prompt-templates/default.md) that enable essential task execution, like answer generation in RAG Tools, post-processing of RAG and Agent output, and translation in multi-lingual flows. By default, these Prompt Templates are pre-selected across different parts of the application, so when you start using Magnet AI, you don't need to dive deep into prompt engineering - evrything works out of the box with preconfigured Prompt Templates.

As your AI solutions evolve, you might need to clone and adjust default Prompt Templates or create your own ones from scratch. Then just replace default Prompt Templates in other tools and test the impact.

[Read more](../../../en/admin/configure/prompt-templates/configuration.md) about configuring Prompt Templates.

## Using standalone Prompt Templates

Prompt Templates can be accessed from another system via API to handle tasks like:

- Summarize case or email;
- Create a draft email message;
- Translate a record;
- Categorize a case;
- Analyze sentiment, and more.

To use a Prompt Template from an external system, you need to pass the required context (such as a case description or email body) to the LLM and implement a trigger in your system to initiate the call.

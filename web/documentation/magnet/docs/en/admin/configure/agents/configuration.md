# Agent Configuration

Let's have a look at each of the tabs of the Agent configuration screen.

## Topics

##### Topic selection Prompt Template

Topic selection prompt instructs the Agent how to detect correct Topics from user input and handle cases when a Topic was not found. It also covers other types of user intent such as greeting, farewell, offtopic input etc.

This Prompt Template model must support JSON mode.

![](../../../images/2025-06-02-15-34-10-image.png)

##### Agent topics

This is the list of all Topics that are available for the Agent. You can add new Topics and delete existing ones here. Click on a Topic name to view its details in the Preview panel.

![](../../../images/2025-06-02-15-35-33-image.png)

Make sure each of your Topics has an accurate and informative description for the LLM. Provide instructions on cases when this Topic should be selected and what kind of questions users might be asking within this Topic.

Click the  `More details & Actions` button to drill down to Topic actions.

<img src="../../../images/2025-06-02-15-37-29-image.png" title="" alt="" width="380">

#### Topic processing Prompt Template

This template provides general instructions on how to process topics, primarily by calling relevant Actions (also known as tools). These instructions are are applicable to the entire Agent. The LLM used for the Prompt TEmplate must support tool calling.

![](../../../images/2025-06-02-15-40-18-image.png)

#### Topic advanced instructions

Topic processing Prompt Template can be enriched with Topic-specific instructions. Use this field to provide additional instructions that are specific to current Topic.

![](../../../images/2025-06-02-15-41-51-image.png)

#### Topic Actions

This is the list of all Actions available under current Topic. Click on an Action to view its details in the Preview area.

![](../../../images/2025-06-02-15-43-21-image.png)

**Important**: 

- **Action LLM name** must be unique within the Topic and cannot contain spaces.
  
  <img title="" src="../../../images/2025-06-02-15-52-35-image.png" alt="" width="298">

- **Description for the LLM** must provide accurate information about what the Action does.
  
  <img src="../../../images/2025-06-02-15-52-44-image.png" title="" alt="" width="304">

- **User Confirmation** setting requires a human confirmation before the action is called. This is helpful for cases when data gets updated or deleted by the Agent.
  
  <img src="../../../images/2025-06-02-15-52-55-image.png" title="" alt="" width="316">

- **Custom action description** field (enabled if User Confirmation is on) provides the option to override default instructions on how Action description is presented to the end user on UI. Namely, when user is prompted to confirm an action, they see a summary of that is going to happen. This summary is generated using degault global instructions. If you need to re-shape it, use the Custom action description field.
  
  <img src="../../../images/2025-06-02-15-53-13-image.png" title="" alt="" width="327">
  
  <img src="../../../images/2025-06-02-15-58-49-image.png" title="" alt="" width="321">

- **Parameters** tab provides an overview of actions parameters, if any. Applicable to Actions derived from API Tools. 
  
  <img src="../../../images/2025-06-02-15-58-00-image.png" title="" alt="" width="316">

## Post-processing

#### Conversation closure interval

This parameter controls time period after which conversations with the Agent are automatically closed and post-processed. Default value is 1 day, but intervals of 3 days and 1 week are also available. Conversation closure and post-processing are handled by a regular job run. 

![](../../../images/2025-06-02-17-05-47-image.png)

#### Post-processing

Enable post-processing to collect metrics about conversations, like user sentiment, language, or resolution status. Metrics are generated with the help of a post-processing Prompt Template.

Post-processing is done on the conversation level. Message post-processing is not yet released.

<img src="../../../images/2025-06-02-17-09-52-image.png" title="" alt="" width="506">

## UI Settings

#### Welcome message

A field to provide a default welcome message for the end-users.

<img src="../../../images/2025-06-02-17-11-18-image.png" title="" alt="" width="480">

#### User feedback

Enable user feedback to collect likes and dislikes. For negative feedback, a comment can also be provided, so that Agent owners can analyze feedback. User likes and dislikes are included in the Usage reports on both message and conversation level.

<img src="../../../images/2025-06-02-17-13-00-image.png" title="" alt="" width="358">

#### Sample questions

Provide up to 3 sample questions to help users start their first conversation with the Agent.

<img title="" src="../../../images/2025-06-02-17-14-07-image.png" alt="" width="466">

## Conversations

Under the Conversations tab, the history of past conversations with the Agent is stored. 

## Notes

Use this tab to store your notes and test inputs for the Agent.

## Test sets

Specific Test sets for evaluating Agents are not yet available, but you can choose a RAG or Prompt Template Test set here and use it for quick testing of specific Agent actions.

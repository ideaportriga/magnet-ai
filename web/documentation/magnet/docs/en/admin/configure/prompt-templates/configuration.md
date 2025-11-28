# Prompt Template configuration

Let’s have a closer look at Prompt Templates parameters available for Magnet AI users. 



## Category

Category is a property that enables option filtering when configuring other features that reference Prompt Templates. This helps organize and limit Prompt Templates available for selection. This parameter can be changed any time after the creation and only affects filtering in dropdowns.

<img src="../../../images/2025-06-02-14-45-55-image.png" title="" alt="" width="540">

**RAG:** Prompt Templates used by RAG Tools (generation, post-processing)

**Agent:** Prompt Templates used by Agents (Topic selection, Topic processing)

**Prompt Tool:** Prompt Templates available for Agents as Actions

**Generic:** all other Prompt Templates 

## Prompt Template

These are the instructions for the LLM, ot the body of Prompt Template. Use this tab to write your instructions for the LLM like description of context that it will receive, task it needs to execute, tone and format of response, restrictions and guardrails, examples of correct output etc.

![image.png](image.png)

## Model settings

Choose the optimal model that ensures sufficient quality of output and necessary format. Adjust the Temperature and Top P parameters. 

Temperature controls how random/creative the model response is, with 0 being the most predictable and 1 the most creative. Top P controls how many possible words the LLM considers when choosing the next word, with 0 being the narrowest choice of words and 1 the most diverse.

Output limit is an advanced setting that can be useful when you need the LLM to respond with a limited number of tokens. 

![](../../../images/2025-06-02-13-09-38-image.png)

## Response format

For models that support JSON format output, you can switch on the toggle to make the model **respond with JSON**. 

> Please keep in mind that also with the JSON mode setting on, you still need to instruct the model to respond in JSON format in the Prompt Template body.

**Match schema** is a more advanced setting. It allows you to provide your JSON schema that the response must adhere to. 

![image.png](image%202.png)

## Notes

Use this tab to store test inputs. Alternatively, you can use this field to simply keep your notes about the Prompt Template and its configuration.

![image.png](image%203.png)

## Test sets

This tab allows to associate a Test set with the Prompt Template for quick access to Test set records. Pick the most relevant Test set from the dropdown, and the records will appear in the list. Clicking on a test record copies it into the Preview area.

![image.png](image%204.png "image.png")

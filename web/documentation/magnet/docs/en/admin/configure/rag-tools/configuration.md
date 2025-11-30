# RAG Tool Configuration

The RAG configuration screen is split into several tabs, or sections.

## Retrieve

##### Knowledge sources

This is the critical setting that you are prompted to configure when you are creating a new RAG Tool. This may be one or multiple Knowledge Sources for the LLM to ground its response when answering users’ questions.

![](../../../images/2025-06-02-13-48-15-image.png)

##### Similarity score threshold

Similarity score threshold indicates the minimum similarity score that is required for a chunk to be retrieved. A higher score (like 0.9) means that the match between chunk meaning and user input meaning must be very high. A lower score means that less relevant chunks may be retrieved. Default value is `0.75`, which is a moderate similarity score.

![](../../../images/2025-06-02-14-11-37-image.png)

##### Number of chunks to select

This parameter controls how many chunks are selected and passed to the LLM for generation if there are multiple chunks with score that fits the threshold. For example, with default Similarity score threshold value of `0.75`, if there are 10 chunks with score above `0.75` and Number of chunks to select is set to `5`, only 5 top chunks will be sent to the LLM for answer generation. If there are 3 chunks with score above `0.75`, only these three will be passed to the LLM.

![](../../../images/2025-06-02-14-11-56-image.png)

##### Number of added chunks

Number of added chunks specifies how many neighboring chunks should be appended to each retrieved chunk, which can be helpful when valuable context spans across neighbouring chunks. Start with the default value of `0` and adjust if needed.

<img src="../../../images/2025-06-09-12-57-32-image.png" title="" alt="" width="278">

##### Re-ranking

Re-ranking improves the accuracy of RAG Tool response by retrieving a broader range of chunks and re-assessing their relevance score. The top few chunks from the re-ranked list are then used to generate a better, more accurate answer. To do this, a re-ranking model is used.

<img src="../../../images/2025-06-09-12-57-59-image.png" title="" alt="" width="482">

If Re-ranking is enabled, it is recommended to set a _lower similarity score threshold_, because at the first step we need to grab a wider range of chunks for further re-ranking. Also, if this technique is enabled, you have an additional parameter under the Chunk limits: `Max number of chunks to retrieve for re-ranking` . This controls how many chunks will actually get re-ranked. Default value is `5`. Other Chunk limits also remain applicable if Re-ranking is enabled.

<img src="../../../images/2025-06-09-12-58-17-image.png" title="" alt="" width="339">

## Generate

This section contains just one parameter - the generation Prompt Template, which shapes the structure, format and tone of RAG output.

If you need to edit this Prompt Template, we recommend that you first clone the default one and make changes in it, or create a new variant of default Prompt Template. Make sure you do not remove the `{context}` placeholder from the Prompt Template.

[Learn more](../prompt-templates/default.html) about the generation Prompt Template.

![](../../../images/2025-06-02-14-12-22-image.png)

## Language

##### Multi-lingual RAG

This setting should be turned on for cases when users ask questions in languages other than that of the Knowledge Source.

The Multi-lingual RAG flow works by detecting user question language, translating the query into the language of Knowledge Source and, after response has been generated, translating it back into user’s language. This approach makes additional calls to LLM, but it significantly improves the quality of multi-lingual RAG.

![](../../../images/2025-06-02-14-17-57-image.png)

## Post-process

Post-processing is an additional workflow that processes RAG-generated output and generates metrics for analytical reports. Currently supported metrics include language, question topic, and answered/not answered.

The Post-processing Prompt Template provides instructions on how to extract these specific metrics from a RAG response, so normally there is no need to edit or replace it. Make sure you manually add some Topics to classify your user questions - these are configured on the RAG tool level.

![](../../../images/2025-06-02-14-19-07-image.png)

## UI settings

UI Settings provide additional customization options for end-user experience, such as heading and subheading and sample questions that give users a hint on what kind of questions they can ask. Here you can also enable user feedback to collect likes and dislikes. Сhanges that you make are immediately available in the Preview area.

![](../../../images/2025-06-02-14-35-12-image.png)

## Test sets

Under the Test sets tab, you can select the most relevant or frequently used Test set with test records for the RAG Tool. This speeds up testing of the RAG Tool: just pick a record and it immediately gets copied into the Preview area.

![](../../../images/2025-06-02-14-36-49-image.png)

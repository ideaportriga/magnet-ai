import os
from dataclasses import dataclass

from models import DocumentSearchResult
from open_ai.utils_new import create_chat_completion_from_prompt_template
from prompt_templates.prompt_templates import get_prompt_template_by_system_name_flat
from tools.rag.utils import get_chat_completion_input_documents

env = os.environ

SYSTEM_PROMPT_TEMPLATE_CODE: str = env.get(
    "QA_SYSTEM_PROMPT_TEMPLATE_CODE",
    "QA_SYSTEM_PROMPT_TEMPLATE",
)


@dataclass
class ChatCompletionResult:
    answer: str
    resulting_prompt: dict | None = None


async def get_chat_completion_answer(
    prompt: str,
    document_search_result: DocumentSearchResult,
    context_window: int,
    system_prompt_template_code=SYSTEM_PROMPT_TEMPLATE_CODE,
) -> ChatCompletionResult:
    if not document_search_result:
        return ChatCompletionResult(answer=env.get("NO_ANSWER_TEXT", ""))

    input_documents = await get_chat_completion_input_documents(
        search_result=document_search_result,
        context_window=context_window,
    )

    prompt_template_config = await get_prompt_template_by_system_name_flat(
        system_prompt_template_code,
    )
    if "{context}" not in prompt_template_config.get("text", ""):
        raise ValueError("Missing placeholder {context}")

    context = "\n\n".join(get_document_context(doc) for doc in input_documents)

    chat_completion, messages = await create_chat_completion_from_prompt_template(
        prompt_template_config=prompt_template_config,
        prompt_template_values={
            "context": context,
        },
        additional_messages=[
            {
                "role": "user",
                "content": prompt,
            },
        ],
    )
    answer = chat_completion.choices[0].message.content or ""

    return ChatCompletionResult(answer=answer, resulting_prompt={"messages": messages})


def get_document_context(doc):
    content = doc.page_content

    # Keep content_override for backward compatibility
    if doc.metadata.get("content_override"):
        content = doc.metadata.get("content_override")
    elif doc.metadata.get("content", {}).get("retrieval"):
        content = doc.metadata.get("content", {}).get("retrieval")

    return (
        f"Title: {doc.metadata.get('title', '')}\n"
        f"URL: {doc.metadata.get('source', '')}\n"
        f"{content}"
    )

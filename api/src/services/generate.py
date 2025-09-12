from logger.utils import logger
from services.get_chat_completion_answer import (
    ChatCompletionResult,
    get_chat_completion_answer,
)


async def generate(
    prompt,
    document_search_result,
    context_window,
    system_prompt_template_system_name,
) -> ChatCompletionResult:
    try:
        answer = await get_chat_completion_answer(
            prompt=prompt,
            document_search_result=document_search_result,
            context_window=context_window,
            system_prompt_template_code=system_prompt_template_system_name,
        )

        # TODO - remove after document_search_result_item.score is already float
        for document_search_result_item in document_search_result:
            document_search_result_item.score = float(document_search_result_item.score)

        return answer

    except Exception as err:
        logger.error("Failed to search: %s", err)
        raise err

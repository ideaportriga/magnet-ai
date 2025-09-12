import os
from dataclasses import dataclass
from logging import getLogger
from typing import Optional

from services.language import TextTranslation, detect_language_and_translate_text
from services.rerank import rerank
from services.retrieve import retrieve
from validation.rag_tools import LanguageConfig
from validation.retrieval_tools import RetrievalToolTest

logger = getLogger(__name__)
env = os.environ


@dataclass
class RetrievalToolTestResult:
    results: list


# Search response validation
async def flow_retrieval_test(input: RetrievalToolTest) -> RetrievalToolTestResult:
    logger.info("user_message: %s", input)

    # TODO - refactor
    user_message = input.user_message

    multilanguage_context = await create_multilanguage_context(
        user_message=user_message,
        language_config=input.language,
    )

    if multilanguage_context:
        user_message = multilanguage_context.user_message_translation

    # Step 1: Retrieve
    max_chunks_retrieved = input.retrieve.max_chunks_retrieved

    if input.retrieve.rerank is not None and input.retrieve.rerank.enabled:
        max_chunks_retrieved = input.retrieve.rerank.max_chunks_retrieved

    results = await retrieve(
        user_message=user_message,
        collection_system_names=input.retrieve.collection_system_names,
        max_chunks_retrieved=max_chunks_retrieved,
        similarity_score_threshold=input.retrieve.similarity_score_threshold,
    )
    # Step 1.5 Rerank
    if input.retrieve.rerank is not None and input.retrieve.rerank.enabled:
        results = await rerank(
            documents=results,
            model_system_name=input.retrieve.rerank.model,
            query=user_message,
            top_n=input.retrieve.max_chunks_retrieved,
        )

    # Step 2: Return the response
    return RetrievalToolTestResult(results=results)


@dataclass
class MultilanguageContext:
    user_message_language: str
    user_message_original: str
    user_message_translation: str
    source_language: str
    prompt_template_translation: str


async def create_multilanguage_context(
    user_message: str,
    language_config: LanguageConfig | None = None,
) -> Optional["MultilanguageContext"]:
    if not language_config or not language_config.multilanguage.enabled:
        return None

    user_message_translation: TextTranslation | None = None

    logger.info("multilanguage - detect language and translate user_message")
    source_language = language_config.multilanguage.source_language
    user_message_translation = await detect_language_and_translate_text(
        text=user_message,
        prompt_template_detect_language=language_config.detect_question_language.prompt_template,
        prompt_template_translate=language_config.multilanguage.prompt_template_translation,
        target_language=source_language,
    )

    if not user_message_translation or not user_message_translation.translation:
        return None

    multilanguage_context = MultilanguageContext(
        user_message_language=user_message_translation.source_language,
        user_message_original=user_message,
        user_message_translation=user_message_translation.translation,
        source_language=source_language,
        prompt_template_translation=language_config.multilanguage.prompt_template_translation,
    )

    logger.info(
        "user_message source language: '%s'",
        user_message_translation.source_language,
    )

    return multilanguage_context

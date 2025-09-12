import json
import os
from logging import getLogger

from open_ai.utils_new import create_chat_completion_from_prompt_template
from prompt_templates.prompt_templates import (
    get_prompt_template_by_system_name_flat,
    transform_to_flat,
)
from services.generate import generate
from services.language import (
    TextTranslation,
    detect_language_and_translate_text,
    translate_text,
)
from services.observability import observability_context, observe
from services.observability.models import FeatureType, ObservedFeature
from services.rag_tools.models import (
    MultilanguageContext,
    RagToolTestResult,
    RagToolTestResultVerboseDetails,
)
from services.rerank import rerank
from services.retrieve import retrieve
from validation.rag_tools import (
    GenerateConfig,
    LanguageConfig,
    PostProcessConfig,
    RagToolsBase,
    RetrieveConfig,
)

env = os.environ
logger = getLogger(__name__)


async def execute_rag_tool(
    *,
    system_name_or_config: str | dict,
    user_message: str,
    config_override: RagToolsBase | None = None,
    verbose: bool = False,
) -> RagToolTestResult:
    # Get RAG Tool config
    if isinstance(system_name_or_config, str):
        rag_tool_config = await get_rag_by_system_name_flat(system_name_or_config)
    else:
        rag_tool_config = system_name_or_config

    # Record RAG Tool execution (used for metrics and analytics)
    observed_feature = ObservedFeature(
        type=FeatureType.RAG_TOOL,
        id=rag_tool_config.get("id"),
        system_name=rag_tool_config.get("system_name"),
        display_name=rag_tool_config.get("name"),
        variant=rag_tool_config.get("active_variant"),
    )
    with observability_context.observe_feature(observed_feature) as instance_id:
        observability_context.update_current_trace(
            extra_data={"question": user_message}
        )
        observability_context.update_current_span(
            name="Calling RAG Tool", extra_data={"question": user_message}
        )

        if config_override:
            language_config = config_override.language
            retrieve_config = config_override.retrieve
            generate_config = config_override.generate
            post_process_config = config_override.post_process
        else:
            language_config = LanguageConfig(**rag_tool_config.get("language", {}))
            retrieve_config = RetrieveConfig(**rag_tool_config.get("retrieve", {}))
            generate_config = GenerateConfig(**rag_tool_config.get("generate", {}))
            post_process_config = PostProcessConfig(
                **rag_tool_config.get("post_process", {}),
            )

        multilanguage_context = await create_multilanguage_context(
            user_message=user_message,
            language_config=language_config,
        )
        if multilanguage_context:
            user_message = multilanguage_context.user_message_translation

        # Step 1: Retrieve

        max_chunks_retrieved = retrieve_config.max_chunks_retrieved

        if retrieve_config.rerank is not None and retrieve_config.rerank.enabled:
            max_chunks_retrieved = retrieve_config.rerank.max_chunks_retrieved

        results = await retrieve(
            user_message=user_message,
            collection_system_names=retrieve_config.collection_system_names,
            max_chunks_retrieved=max_chunks_retrieved,
            similarity_score_threshold=retrieve_config.similarity_score_threshold,
        )

        # Step 1.5 Rerank
        if retrieve_config.rerank is not None and retrieve_config.rerank.enabled:
            results = await rerank(
                documents=results,
                model_system_name=retrieve_config.rerank.model,
                query=user_message,
                top_n=retrieve_config.max_chunks_retrieved,
            )

        # Step 2: Generate
        generate_result = await generate(
            user_message,
            results,
            retrieve_config.chunk_context_window_expansion_size,
            generate_config.prompt_template,
        )
        answer = generate_result.answer

        # TODO - refactor
        if multilanguage_context:
            answer_translation = await translate_text(
                text=answer,
                prompt_template=multilanguage_context.prompt_template_translation,
                target_language=multilanguage_context.user_message_language,
                source_language=multilanguage_context.source_language,
            )
            answer = answer_translation

        # Step 3: Post-process
        if post_process_config and post_process_config.enabled:
            post_process_result = await _post_process(
                post_process_config=post_process_config,
                answer=answer,
                results=results,
            )
            observability_context.update_current_span(extra_data=post_process_result)

        # Step 5: Return the response
        verbose_details = (
            RagToolTestResultVerboseDetails(
                resulting_prompt=generate_result.resulting_prompt,
            )
            if verbose
            else None
        )

        observability_context.update_current_span(extra_data={"answer": answer})

        # Update trace metadata
        observability_context.update_current_trace(
            extra_data={"chunks_retrieved": len(results), "answer": answer}
        )

        return RagToolTestResult(
            answer=answer,
            results=results,
            verbose_details=verbose_details,
            trace_id=observability_context.get_current_trace_id(),
            analytics_id=instance_id,
        )


async def create_multilanguage_context(
    user_message: str,
    language_config: LanguageConfig | None = None,
) -> MultilanguageContext | None:
    if not language_config or not language_config.multilanguage.enabled:
        return None

    user_message_translation: TextTranslation | None = None

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


async def get_rag_by_system_name_flat(
    system_name: str,
    variant: str | None = None,
) -> dict:
    try:
        from core.config.app import alchemy
        from core.domain.rag_tools.schemas import RagTool
        from core.domain.rag_tools.service import RagToolsService

        async with alchemy.get_session() as session:
            service = RagToolsService(session=session)
            rag_tool = await service.get_one_or_none(system_name=system_name)
            print(rag_tool)
            if not rag_tool:
                raise LookupError(f"RAG Tool with system name '{system_name}' not found")
            config = service.to_schema(rag_tool, schema_type=RagTool)
            print(config)
            return transform_to_flat(config.model_dump(), variant)
    except Exception as e:
        logger.warning("Failed to get rag tool: '%s': %s", system_name, e)
        raise


# TODO: this needs to be refactored, it should work in a separate thread
@observe(
    name="Post processing",
    description="Post-process LLM response, to identify the topic and to check if the question was answered.",
)
async def _post_process(post_process_config: PostProcessConfig, answer, results):
    if post_process_config.enabled:
        prompt_template_system_name = post_process_config.categorization.prompt_template
        prompt_template_config = await get_prompt_template_by_system_name_flat(
            prompt_template_system_name=prompt_template_system_name,
        )
        categories = "{" + ",".join(post_process_config.categorization.categories) + "}"

        prompt_template_values = {
            "CATEGORIES": categories,
        }
        chat_completion, _ = await create_chat_completion_from_prompt_template(
            prompt_template_config=prompt_template_config,
            prompt_template_values=prompt_template_values,
            additional_messages=[
                {
                    "role": "user",
                    "content": answer,
                },
            ],
        )

        # Parse post-process result
        post_process_result = (
            json.loads(chat_completion.choices[0].message.content)
            if chat_completion.choices[0].message.content
            else None
        )

        # Update metrics
        is_answered = False
        if len(results) == 0:
            resolution = "no_results"
        elif post_process_result and post_process_result.get("is_answered"):
            resolution = "question_answered"
            is_answered = True
        else:
            resolution = "question_not_answered"

        return {
            "is_answered": is_answered,
            "resolution": resolution,
            "topic": post_process_result.get("category")
            if post_process_result
            else None,
            "language": post_process_result.get("language")
            if post_process_result
            else None,
        }

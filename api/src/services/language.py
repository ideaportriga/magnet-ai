from dataclasses import dataclass

from services.observability import observe
from services.prompt_templates import execute_prompt_template


@dataclass
class TextTranslation:
    source_language: str
    translation: str | None


@observe(name="Detect language and translate text")
async def detect_language_and_translate_text(
    text: str,
    prompt_template_detect_language: str,
    target_language: str,
    prompt_template_translate: str,
) -> TextTranslation:
    source_language = await detect_language(
        user_message=text,
        prompt_template=prompt_template_detect_language,
    )

    translation = None

    if source_language != target_language:
        translation = await translate_text(
            text=text,
            prompt_template=prompt_template_translate,
            target_language=target_language,
            source_language=source_language,
        )

    return TextTranslation(source_language=source_language, translation=translation)


async def translate_text(
    text: str,
    prompt_template: str,
    target_language: str,
    source_language: str,
) -> str:
    system_message_values = {
        "source_language": source_language,
        "target_language": target_language,
    }
    result = await execute_prompt_template(
        system_name_or_config=prompt_template,
        template_values=system_message_values,
        template_additional_messages=[
            {
                "role": "user",
                "content": text,
            },
        ],
    )

    return result.content


async def detect_language(user_message: str, prompt_template: str) -> str:
    result = await execute_prompt_template(
        system_name_or_config=prompt_template,
        template_additional_messages=[
            {
                "role": "user",
                "content": user_message,
            },
        ],
    )

    return result.content

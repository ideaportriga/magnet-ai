import logging
import os
import re

from openai.types.chat import ChatCompletion

from observability.event_logger import EventLogger
from open_ai.utils_new import create_chat_completion
from prompt_templates.prompt_templates import get_prompt_template_by_system_name_flat

env = os.environ

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)


formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
console_handler.setFormatter(formatter)

logger.addHandler(console_handler)
event_logger = EventLogger()


async def log_documents(documents, prompt_id):
    for doc in documents:
        event_name = "magnetui-search-document"
        properties = {
            "chunkTitle": doc.metadata.get("chunkTitle", "Unknown Title"),
            "source": doc.metadata.get("source", "Unknown Source"),
            "sourceId": doc.metadata.get("sourceId", "Unknown Source ID"),
            "title": doc.metadata.get("title", "No Title"),
            "score": getattr(doc, "score", 0),
            "completion": getattr(doc, "completion", False),
            "promptId": prompt_id,
        }
        await event_logger.log_event(event_name, properties)


async def _chat_completion(prompt_template_system_name, user_message) -> ChatCompletion:
    if prompt_template_system_name:
        prompt_template = await get_prompt_template_by_system_name_flat(
            prompt_template_system_name,
        )

        temperature = prompt_template.get("temperature")
        top_p = prompt_template.get("topP")
        model = prompt_template.get("model")
        system_message = prompt_template.get("text")
        response_format = prompt_template.get("response_format")
        messages = [
            {
                "role": "system",
                "content": system_message,
            },
            {
                "role": "user",
                "content": user_message,
            },
        ]
    else:
        raise Exception("template not found")

    response = await create_chat_completion(
        messages=messages,
        llm=model,
        temperature=temperature,
        top_p=top_p,
        response_format=response_format,
    )

    return response


async def is_answered(user_message, prompt_template="IS_ANSWERED"):
    default_answer = env.get("NO_ANSWER_TEXT", "")

    try:
        if user_message == default_answer:
            return {"is_answered": False, "has_docs": False}

        result = await _chat_completion(prompt_template, user_message)
        content = result.choices[0].message.content or ""
        is_answered = "true" in content

        return {"is_answered": is_answered, "has_docs": True}
    except Exception:
        # You can log the exception or handle it differently if needed
        return {"is_answered": "unknown", "has_docs": "unknown"}


async def get_language(user_message, language=None, prompt_template="DETECT_LANGUAGE"):
    try:
        if language is not None:
            return {"language": language}

        result = await _chat_completion(prompt_template, user_message)
        content = result.choices[0].message.content or ""
        language = retrieve_language_from_string(content)

        return {"language": language}
    except Exception:
        # Handle the error appropriately
        return {"language": "Unknown"}


def retrieve_language_from_string(test_string: str = "English") -> str:
    languages = [
        "English",
        "Chinese",
        "Hindi",
        "Spanish",
        "French",
        "Standard Arabic",
        "Bengali",
        "Russian",
        "Portuguese",
        "Urdu",
        "Indonesian",
        "German",
        "Japanese",
        "Swahili",
        "Marathi",
        "Telugu",
        "Turkish",
        "Korean",
        "Tamil",
        "Italian",
        "Vietnamese",
        "Cantonese",
        "Thai",
        "Dutch",
        "Greek",
        "Polish",
        "Persian",
        "Romanian",
        "Serbian",
        "Croatian",
        "Bosnian",
        "Ukrainian",
        "Maithili",
        "Sundanese",
        "Sinhalese",
        "Amharic",
        "Gujarati",
        "Oromo",
        "Kurdish",
        "Burmese",
        "Azerbaijani",
        "Fula",
        "Igbo",
        "Uzbek",
        "Sindhi",
        "Malayalam",
        "Hausa",
        "Pashto",
        "Yoruba",
        "Punjabi",
        "Khmer",
        "Somali",
        "Albanian",
        "Lithuanian",
        "Mongolian",
        "Armenian",
        "Slovak",
        "Slovenian",
        "Macedonian",
        "Norwegian",
        "Finnish",
        "Hungarian",
        "Danish",
        "Bulgarian",
        "Hebrew",
        "Georgian",
        "Amharic",
        "Nepali",
        "Sinhala",
        "Kazakh",
        "Tajik",
        "Turkmen",
        "Kyrgyz",
        "Pashto",
        "Dzongkha",
        "Afrikaans",
        "Estonian",
        "Latvian",
        "Swedish",
        "Belarusian",
        "Icelandic",
        "Maltese",
        "Irish",
        "Welsh",
        "Basque",
        "Catalan",
        "Luxembourgish",
        "Frisian",
        "Scottish Gaelic",
        "Breton",
        "Corsican",
        "Aromanian",
        "Galician",
        "Ladino",
        "Walloon",
        "Samogitian",
        "Karelian",
        "Livonian",
        "Veps",
        "Ingrian",
        "Votic",
        "Moksha",
        "Mari",
        "Udmurt",
        "Komi",
        "Chuvash",
        "Ossetian",
        "Bashkir",
        "Tatar",
        "Chechen",
        "Abkhaz",
        "Adyghe",
        "Kabardian",
        "Karachay-Balkar",
        "Nogai",
        "Kalmyk",
        "Tuvinian",
        "Altai",
        "Khakas",
        "Shor",
        "Sakha",
        "Evenki",
        "Nenets",
        "Chukchi",
        "Koryak",
        "Itelmen",
        "Ainu",
        "Yukaghir",
        "Gilyak",
        "Aleut",
    ]

    regex_pattern = r"\b(" + "|".join([re.escape(lang) for lang in languages]) + r")\b"
    matches = re.findall(regex_pattern, test_string, re.IGNORECASE)

    if matches:
        return min(matches, key=lambda x: languages.index(x.title()))
    return "unknown"


async def get_category(
    user_message,
    prompt_template="CATEGORIZATION",
    possible_categries=None,
):
    try:
        if possible_categries is None:
            return {"category": "unknown"}

        result = await _chat_completion(prompt_template, user_message)
        content = result.choices[0].message.content or ""
        category = retrieve_category_from_string(content, possible_categries)

        return {"category": category}
    except Exception:
        return {"category": "unknown"}


def retrieve_category_from_string(content, possible_categries):
    for category in possible_categries:
        if category.lower() in content.lower():
            return category
    return "unknown"

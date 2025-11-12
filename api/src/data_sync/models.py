from enum import StrEnum


class ChunkingStrategy(StrEnum):
    NONE = "none"
    RECURSIVE_CHARACTER_TEXT_SPLITTING = "recursive_character_text_splitting"
    HTML_HEADER_SPLITTING = "html_header_splitting"

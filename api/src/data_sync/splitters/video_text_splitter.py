import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import timedelta
from typing import override

from langchain.schema.document import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from data_sync.splitters.abstract_splitter import AbstractSplitter
from data_sync.utils import clean_text


@dataclass
class Chapter:
    start_time: int
    title: str
    content: str


CHAPTER_PATTERN = re.compile(
    r"## \[([0-9]{2}:[0-9]{2}:[0-9]{2})\] (.+?)\n\n([\s\S]+?)(?=\n## \[([0-9]{2}:[0-9]{2}:[0-9]{2})\]|\Z)",
    re.DOTALL,
)

NO_CHAPTERS_SPLITTER = RecursiveCharacterTextSplitter()


class VideoTextSplitter(AbstractSplitter):
    def __init__(
        self,
        url: str | Callable[[Chapter | None], str],
        description: str,
        base_metadata: dict,
    ):
        self.url = url
        self.description = description
        self.base_metadata = dict(
            {
                **base_metadata,
                "type": "video",
            },
        )

    @override
    async def split(self) -> list[Document]:
        chapters = self.__parse_chapters()

        if not chapters:
            return self.__create_chunks_from_description()

        return self.__create_chunks_from_chapters(chapters)

    def __parse_chapters(self):
        matches = CHAPTER_PATTERN.finditer(self.description)

        chapters = []

        for match in matches:
            start_time_str = match.group(1)
            title = match.group(2).strip()
            content = match.group(3).strip()

            hours, minutes, seconds = map(int, start_time_str.split(":"))
            duration = timedelta(hours=hours, minutes=minutes, seconds=seconds)
            start_time = int(duration.total_seconds())

            chapter = Chapter(title=title, start_time=start_time, content=content)
            chapters.append(chapter)

        return chapters

    def __create_chunks_from_description(self) -> list[Document]:
        embed_url = self.url if isinstance(self.url, str) else self.url(None)
        metadata = {
            **self.base_metadata,
            "source": embed_url,  # for backward compatibility
            "embed_url": embed_url,
        }

        chunks = NO_CHAPTERS_SPLITTER.split_text(self.description)

        return [
            Document(page_content=clean_text(chunk), metadata=metadata)
            for chunk in chunks
        ]

    def __create_chunks_from_chapters(self, chapters: list[Chapter]) -> list[Document]:
        chunks = []

        for chapter in chapters:
            page_content = chapter.content
            chapter_title = chapter.title
            chapter_start_time = chapter.start_time
            main_title = self.base_metadata.get("title")
            document_title = f"{chapter_title} ({main_title})"
            embed_url = self.url if isinstance(self.url, str) else self.url(chapter)

            metadata = {
                **self.base_metadata,
                "chapterStartTime": chapter_start_time,
                "chapterTitle": chapter_title,
                "mainTitle": main_title,
                "title": document_title,
                "embedUrl": embed_url,
                "source": embed_url,  # for backward compatibility
            }

            chunks.append(
                Document(page_content=clean_text(page_content), metadata=metadata),
            )

        return chunks

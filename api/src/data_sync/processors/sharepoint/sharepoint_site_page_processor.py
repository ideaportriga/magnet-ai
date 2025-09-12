from logging import getLogger
from urllib.parse import urljoin

from bs4 import BeautifulSoup
from html2text import HTML2Text
from langchain.schema import Document
from langchain.text_splitter import (
    CharacterTextSplitter,
    RecursiveCharacterTextSplitter,
)
from office365.sharepoint.files.file import File

from data_sources.sharepoint.types import DocumentSourceType

logger = getLogger(__name__)


class SharepointSitePageProcessor:
    def _create_site_page_documents(
        self,
        file: File,
        base_metadata: dict,
        base_url: str,
        embed_title: bool,
    ) -> list[Document]:
        file_name = file.name

        logger.info("Create documents for site page `%s`", file_name)

        # TODO - do we need also "LayoutWebpartsContent" prop for other page types?
        list_item = (
            file.listItemAllFields.select(["CanvasContent1"]).get().execute_query()
        )

        page_content = list_item.properties.get("CanvasContent1")

        documents = []

        if page_content:
            parsed_content = self.__parse_page(
                page_content=page_content,
                base_url=base_url,
            )

            if embed_title:
                document = Document(
                    page_content=base_metadata.get("title", ""),
                    metadata={
                        **base_metadata,
                        "type": DocumentSourceType.SITE_PAGE,
                        "content": {
                            "unmodified": parsed_content,
                            "retrieval": parsed_content,
                        },
                    },
                )
            else:
                document = Document(
                    page_content=parsed_content,
                    metadata={
                        **base_metadata,
                        "type": DocumentSourceType.SITE_PAGE,
                    },
                )

            document_chunks = self.__split_document_to_chunks(document)
            documents.extend(document_chunks)

        return documents

    def __split_document_to_chunks(self, document: Document) -> list[Document]:
        main_title = document.metadata.get("title")
        document_chunks = split_docs([document], 12000)
        chunks_total = len(document_chunks)

        for i, chunk in enumerate(document_chunks):
            chunk_number = i + 1
            chunk_title = f"{main_title} ({chunk_number}/{chunks_total})"

            chunk.metadata.update(
                {
                    "chunkTitle": chunk_title,
                    "chunkNumber": chunk_number,
                    "chunksTotal": chunks_total,
                },
            )

        return document_chunks

    def __parse_page(self, page_content: str, base_url: str):
        soup = BeautifulSoup(page_content, "html.parser")

        for anchor in soup.find_all("a", href=True):
            href = anchor["href"]

            if href.startswith("/"):
                absolute_url = urljoin(base_url, href)
                anchor["href"] = absolute_url

        # replace the Unicode character \u200b (a zero-width space) with an empty string
        # page_text = soup.get_text().replace("\u200b", "")
        clean_html = str(soup).replace("\u200b", "")

        # convert to markdown
        h = HTML2Text()
        h.body_width = 0
        page_text = h.handle(clean_html)

        return page_text


def split_docs(documents, chunk_size: int, chunk_overlap: int = 0):
    # Split documents to chunks
    # First try to split it using CharacterTextSplitter - It uses \n\n only to split and it can fail
    char_text_splitter = CharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    splitted_docs_simple = char_text_splitter.split_documents(documents)

    # Now let's split all the documents that did not fit with a recursive splitter
    # It will split the doc using  ["\n\n", "\n", " ", ""]
    recursive_text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )
    return recursive_text_splitter.split_documents(splitted_docs_simple)

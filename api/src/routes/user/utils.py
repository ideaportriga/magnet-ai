from typing import Annotated, Any

from kreuzberg import ExtractionConfig, PageConfig, extract_bytes
from litestar import Controller, post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.exceptions import ClientException
from litestar.params import Body
from litestar.status_codes import HTTP_200_OK
from pydantic import BaseModel

from api.tags import TagNames
from services.knowledge_graph.readers.kreuzberg_reader import mime_type_from_filename


class ParsePdfResponse(BaseModel):
    pages: list[str]


class ParseDocumentResponse(BaseModel):
    pages: list[str]
    metadata: dict[str, Any] = {}


class UserUtilsController(Controller):
    path = "/utils"
    tags = [TagNames.UserUtils]

    @post("/parse-pdf", status_code=HTTP_200_OK)
    async def parse_pdf(
        self,
        data: Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)],
    ) -> ParsePdfResponse:
        """Parse a document file and extract text from its pages.

        Accepts any format supported by kreuzberg. MIME type is resolved
        from the upload content-type or inferred from the filename.
        """
        if not data:
            raise ClientException("No file provided")

        content = await data.read()
        filename = data.filename or ""
        mime_type = data.content_type or mime_type_from_filename(filename)
        if not mime_type:
            mime_type = "application/pdf"  # Fallback for legacy callers

        config = ExtractionConfig(
            output_format="markdown",
            pages=PageConfig(extract_pages=True),
        )
        result = await extract_bytes(content, mime_type, config=config)
        pages = (
            [p["content"] for p in result.pages] if result.pages else [result.content]
        )
        return ParsePdfResponse(pages=pages)

    @post("/parse-document", status_code=HTTP_200_OK)
    async def parse_document(
        self,
        data: Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)],
    ) -> ParseDocumentResponse:
        """Parse any supported document and extract text from its pages"""
        if not data:
            raise ClientException("No file provided")

        content = await data.read()
        filename = data.filename or ""
        mime_type = data.content_type or mime_type_from_filename(filename)
        if not mime_type:
            raise ClientException(
                "Cannot determine file type. Provide a file with a known extension."
            )

        config = ExtractionConfig(
            output_format="markdown",
            pages=PageConfig(extract_pages=True),
        )
        result = await extract_bytes(content, mime_type, config=config)
        pages = (
            [p["content"] for p in result.pages] if result.pages else [result.content]
        )

        metadata: dict[str, Any] = {}
        page_count = result.get_page_count()
        if page_count:
            metadata["page_count"] = page_count
        if result.metadata:
            for key in ("title", "authors", "subject"):
                val = result.metadata.get(key)
                if val:
                    metadata[key] = val
        if result.tables:
            metadata["tables_count"] = len(result.tables)
        if result.detected_languages:
            metadata["detected_languages"] = result.detected_languages

        return ParseDocumentResponse(pages=pages, metadata=metadata)

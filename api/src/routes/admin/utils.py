from typing import Annotated

from cryptography.fernet import Fernet
from kreuzberg import ExtractionConfig, PageConfig, extract_bytes
from litestar import Controller, post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.exceptions import ClientException
from litestar.params import Body
from litestar.status_codes import HTTP_200_OK
from pydantic import BaseModel

from services.knowledge_graph.readers.kreuzberg_reader import mime_type_from_filename


class ParsePdfResponse(BaseModel):
    pages: list[str]


# duplicate of UserUtilsController TODO - rework
class UtilsController(Controller):
    path = "/utils"
    tags = ["Admin / Utils"]

    @post("/parse-pdf", status_code=HTTP_200_OK)
    async def parse_pdf(
        self,
        data: Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)],
    ) -> ParsePdfResponse:
        """Parse a document file and extract text from its pages.

        Accepts any format supported by kreuzberg (PDF, DOCX, PPTX, XLSX,
        images, HTML, email, etc.). The MIME type is resolved from the
        uploaded file's content-type header or inferred from its filename.
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

    @post("/generate_secret_encryption_key", status_code=HTTP_200_OK)
    async def generate_secret_encryption_key(
        self,
    ) -> dict:
        """
        Generates A URL-safe base64-encoded 32-byte key
        which can be used as a vaulue of the environment variable `SECRET_ENCRYPTION_KEY`
        to encrypt secrets stored in the database.
        """

        secret_encryption_key = Fernet.generate_key().decode()

        return {"key": secret_encryption_key}

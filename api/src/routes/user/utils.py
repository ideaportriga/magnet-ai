import io
from typing import Annotated

from litestar import Controller, post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.exceptions import ClientException
from litestar.params import Body
from litestar.status_codes import HTTP_200_OK
from pydantic import BaseModel
from pypdf import PdfReader

from api.tags import TagNames


class ParsePdfResponse(BaseModel):
    pages: list[str]


class UserUtilsController(Controller):
    path = "/utils"
    tags = [TagNames.UserUtils]

    @post("/parse-pdf", status_code=HTTP_200_OK)
    async def parse_pdf(
        self,
        data: Annotated[UploadFile, Body(media_type=RequestEncodingType.MULTI_PART)],
    ) -> ParsePdfResponse:
        """Parse PDF file and extract text from its pages"""
        if not data:
            raise ClientException("No file provided")

        content = await data.read()
        pdf_reader = PdfReader(io.BytesIO(content))
        pages = [page.extract_text() for page in pdf_reader.pages]

        return ParsePdfResponse(pages=pages)

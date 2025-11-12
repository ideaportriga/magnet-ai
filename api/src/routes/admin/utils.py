import io
from typing import Annotated

from cryptography.fernet import Fernet
from litestar import Controller, post
from litestar.datastructures import UploadFile
from litestar.enums import RequestEncodingType
from litestar.exceptions import ClientException
from litestar.params import Body
from litestar.status_codes import HTTP_200_OK
from pydantic import BaseModel
from pypdf import PdfReader



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
        """Parse PDF file and extract text from its pages"""
        if not data:
            raise ClientException("No file provided")

        content = await data.read()
        pdf_reader = PdfReader(io.BytesIO(content))
        pages = [page.extract_text() for page in pdf_reader.pages]

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


import logging
from pathlib import Path
from typing import Optional

from pypdf import PdfReader

logger = logging.getLogger(__name__)


class DefaultPdfReader:
    """Process PDF files and extract text with page information."""

    def __init__(self, page_delimiter: str = "\n\f"):
        self.page_delimiter = page_delimiter

    def extract_text_from_bytes(self, pdf_bytes: bytes) -> tuple[str, int]:
        """Extract text from PDF bytes with page awareness.

        Args:
            pdf_bytes: PDF file content as bytes

        Returns:
            Tuple of (extracted_text, total_pages)

        Raises:
            ValueError: If PDF cannot be read
        """
        try:
            logger.info("Reading PDF from bytes")

            # Create a BytesIO-like object from bytes
            from io import BytesIO

            pdf_file = BytesIO(pdf_bytes)
            pdf_reader = PdfReader(pdf_file)
            total_pages = len(pdf_reader.pages)

            page_texts = []
            for page_number, page in enumerate(pdf_reader.pages, start=1):
                text_from_page = page.extract_text(extraction_mode="plain")

                page_text = f"[Page: {page_number}]\n{text_from_page}"

                page_texts.append(page_text)

            # Join all pages with page delimiter
            pdf_content = self.page_delimiter.join(page_texts)

            logger.info(
                f"Successfully extracted text from {total_pages} pages, total length: {len(pdf_content)} chars"
            )

            return pdf_content, total_pages

        except Exception as e:
            logger.error(f"Error reading PDF bytes: {e}")
            raise ValueError(f"Failed to read PDF bytes: {e}") from e

    def extract_metadata(self, file_path: str | Path) -> Optional[dict]:
        """Extract metadata from PDF file.

        Args:
            file_path: Path to the PDF file

        Returns:
            Dictionary containing PDF metadata or None if extraction fails
        """
        file_path = Path(file_path)

        try:
            pdf_reader = PdfReader(file_path)
            metadata = pdf_reader.metadata

            if metadata:
                return {
                    "title": metadata.get("/Title"),
                    "author": metadata.get("/Author"),
                    "subject": metadata.get("/Subject"),
                    "creator": metadata.get("/Creator"),
                    "producer": metadata.get("/Producer"),
                    "creation_date": str(metadata.get("/CreationDate")),
                    "modification_date": str(metadata.get("/ModDate")),
                }

            return None

        except Exception as e:
            logger.warning(f"Failed to extract PDF metadata: {e}")
            return None

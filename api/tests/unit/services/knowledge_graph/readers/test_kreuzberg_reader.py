"""Tests for KreuzbergReader and MIME type detection utilities."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from services.knowledge_graph.readers.kreuzberg_reader import (
    KreuzbergReader,
    mime_type_from_filename,
)


# ---------------------------------------------------------------------------
# mime_type_from_filename
# ---------------------------------------------------------------------------


class TestMimeTypeFromFilename:
    def test_pdf(self):
        assert mime_type_from_filename("report.pdf") == "application/pdf"

    def test_docx(self):
        assert (
            mime_type_from_filename("doc.docx")
            == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
        )

    def test_png(self):
        assert mime_type_from_filename("image.png") == "image/png"

    def test_html(self):
        assert mime_type_from_filename("page.html") == "text/html"

    def test_htm_variant(self):
        assert mime_type_from_filename("page.htm") == "text/html"

    def test_unknown_extension(self):
        assert mime_type_from_filename("file.xyz123") is None

    def test_no_extension(self):
        assert mime_type_from_filename("README") is None

    def test_case_insensitive(self):
        assert mime_type_from_filename("DOC.PDF") == "application/pdf"

    def test_nested_path(self):
        assert mime_type_from_filename("/some/path/to/file.xlsx") == (
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

    def test_eml(self):
        assert mime_type_from_filename("message.eml") == "message/rfc822"

    def test_epub(self):
        assert mime_type_from_filename("book.epub") == "application/epub+zip"


# ---------------------------------------------------------------------------
# KreuzbergReader
# ---------------------------------------------------------------------------


class TestKreuzbergReader:
    @pytest.mark.asyncio
    async def test_extract_from_bytes_with_mime(self):
        """When mime_type is provided, it should be used directly."""
        fake_result = MagicMock()
        fake_result.content = "# Title\n\nHello world"
        fake_result.get_page_count.return_value = 2
        fake_result.metadata = {"title": "Test"}
        fake_result.tables = []
        fake_result.detected_languages = ["en"]
        fake_result.pages = None

        with patch(
            "services.knowledge_graph.readers.kreuzberg_reader.extract_bytes",
            new_callable=AsyncMock,
            return_value=fake_result,
        ) as mock_extract:
            reader = KreuzbergReader()
            text, metadata = await reader.extract_from_bytes(
                b"fake-pdf-bytes", mime_type="application/pdf"
            )

            mock_extract.assert_awaited_once()
            call_args = mock_extract.call_args
            assert call_args[0][1] == "application/pdf"

            assert text == "# Title\n\nHello world"
            assert metadata["total_pages"] == 2
            assert metadata["title"] == "Test"
            assert metadata["detected_languages"] == ["en"]

    @pytest.mark.asyncio
    async def test_extract_from_bytes_infers_mime_from_filename(self):
        """When mime_type is None, it should be inferred from filename."""
        fake_result = MagicMock()
        fake_result.content = "extracted text"
        fake_result.get_page_count.return_value = None
        fake_result.metadata = {}
        fake_result.tables = [MagicMock()]
        fake_result.detected_languages = []
        fake_result.pages = None

        with patch(
            "services.knowledge_graph.readers.kreuzberg_reader.extract_bytes",
            new_callable=AsyncMock,
            return_value=fake_result,
        ) as mock_extract:
            reader = KreuzbergReader()
            text, metadata = await reader.extract_from_bytes(
                b"<html>hello</html>", filename="page.html"
            )

            call_args = mock_extract.call_args
            assert call_args[0][1] == "text/html"
            assert text == "extracted text"
            assert metadata["tables_count"] == 1

    @pytest.mark.asyncio
    async def test_extract_raises_without_mime_or_filename(self):
        """Should raise ValueError when MIME cannot be determined."""
        with patch(
            "kreuzberg.detect_mime_type",
            side_effect=Exception("cannot detect"),
        ):
            reader = KreuzbergReader()
            with pytest.raises(ValueError, match="Cannot determine MIME type"):
                await reader.extract_from_bytes(b"unknown-data")

    @pytest.mark.asyncio
    async def test_ocr_option_configures_ocr(self):
        """When ocr=True in options, OcrConfig should be set."""
        fake_result = MagicMock()
        fake_result.content = "OCR text"
        fake_result.get_page_count.return_value = 1
        fake_result.metadata = {}
        fake_result.tables = []
        fake_result.detected_languages = []
        fake_result.pages = None

        with patch(
            "services.knowledge_graph.readers.kreuzberg_reader.extract_bytes",
            new_callable=AsyncMock,
            return_value=fake_result,
        ) as mock_extract:
            reader = KreuzbergReader(reader_options={"ocr": True})
            await reader.extract_from_bytes(b"image-bytes", mime_type="image/png")

            call_args = mock_extract.call_args
            config = call_args[1].get("config") or call_args[0][2]
            assert config.ocr is not None

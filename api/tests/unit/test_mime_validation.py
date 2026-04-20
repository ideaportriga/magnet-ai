"""Regression tests for storage.mime_validation (§C.1)."""

from __future__ import annotations

import pytest
from litestar.exceptions import ClientException

from storage.mime_validation import validate_upload_mime


class TestMimeValidation:
    def test_pdf_with_pdf_content_ok(self):
        validate_upload_mime("report.pdf", "application/pdf")

    def test_docx_allows_zip_fallback(self):
        validate_upload_mime(
            "doc.docx",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
        validate_upload_mime("doc.docx", "application/zip")

    def test_png_with_jpeg_content_rejected(self):
        with pytest.raises(ClientException):
            validate_upload_mime("image.png", "image/jpeg")

    def test_pdf_with_executable_content_rejected(self):
        with pytest.raises(ClientException):
            validate_upload_mime("doc.pdf", "application/x-dosexec")

    def test_renamed_executable_rejected_regardless_of_extension(self):
        with pytest.raises(ClientException):
            validate_upload_mime("whatever.pdf", "application/x-executable")

    def test_unknown_extension_rejected(self):
        with pytest.raises(ClientException):
            validate_upload_mime("evil.exe", "application/pdf")

    def test_octet_stream_allowed_for_known_extension(self):
        # kreuzberg returns octet-stream when unsure — we trust the extension.
        validate_upload_mime("notes.txt", "application/octet-stream")

    def test_csv_accepts_plain_text(self):
        validate_upload_mime("rows.csv", "text/plain")
        validate_upload_mime("rows.csv", "text/csv")

"""Tests for content_config_services defaults and feature flag."""

from unittest.mock import patch

from services.knowledge_graph.content_config_services import (
    get_default_content_configs,
)
from services.knowledge_graph.models import ContentReaderName


class TestGetDefaultContentConfigs:
    def test_returns_all_expected_configs(self):
        configs = get_default_content_configs()
        names = [c.name for c in configs]
        assert "PDF" in names
        assert "Word" in names
        assert "PowerPoint" in names
        assert "Excel" in names
        assert "HTML" in names
        assert "Images" in names
        assert "Email" in names
        assert "Default" in names

    def test_default_is_last(self):
        configs = get_default_content_configs()
        assert configs[-1].name == "Default"

    def test_images_config_has_ocr_option(self):
        configs = get_default_content_configs()
        images = next(c for c in configs if c.name == "Images")
        assert images.reader["options"]["ocr"] is True

    def test_email_glob_pattern(self):
        configs = get_default_content_configs()
        email = next(c for c in configs if c.name == "Email")
        assert "*.eml" in email.glob_pattern
        assert "*.msg" in email.glob_pattern


class TestPdfReaderNameFeatureFlag:
    def test_pdf_uses_kreuzberg_when_flag_true(self):
        with patch(
            "services.knowledge_graph.content_config_services.USE_KREUZBERG", True
        ):
            configs = get_default_content_configs()
            pdf = next(c for c in configs if c.name == "PDF")
            assert pdf.reader["name"] == ContentReaderName.KREUZBERG

    def test_pdf_uses_legacy_reader_when_flag_false(self):
        with patch(
            "services.knowledge_graph.content_config_services.USE_KREUZBERG", False
        ):
            configs = get_default_content_configs()
            pdf = next(c for c in configs if c.name == "PDF")
            assert pdf.reader["name"] == ContentReaderName.PDF

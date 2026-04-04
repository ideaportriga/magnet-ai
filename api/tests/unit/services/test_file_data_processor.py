"""Tests for UrlDataSource and UrlDataProcessor (format-agnostic kreuzberg processing)."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from data_sources.file.source import UrlDataSource


class TestUrlDataSource:
    """Tests for UrlDataSource accepting all formats."""

    @pytest.mark.asyncio
    async def test_default_allows_all_extensions(self):
        """By default, no extension filtering is applied."""
        urls = [
            "https://example.com/doc.pdf",
            "https://example.com/doc.docx",
            "https://example.com/image.png",
            "https://example.com/data.csv",
        ]
        source = UrlDataSource(urls)
        result = await source.get_data()
        assert len(result) == 4

    @pytest.mark.asyncio
    async def test_allowed_extensions_filter(self):
        """When allowed_extensions is set, only matching URLs are returned."""
        urls = [
            "https://example.com/doc.pdf",
            "https://example.com/doc.docx",
            "https://example.com/image.png",
        ]
        source = UrlDataSource(urls, allowed_extensions=[".pdf", ".docx"])
        result = await source.get_data()
        assert len(result) == 2
        assert "https://example.com/doc.pdf" in result
        assert "https://example.com/doc.docx" in result

    @pytest.mark.asyncio
    async def test_local_files_included(self):
        """local_files are added as local:// identifiers."""
        urls = ["https://example.com/doc.pdf"]
        local_files = [
            {"filename": "report.docx", "storage_path": "/tmp/uploads/report.docx"},
        ]
        source = UrlDataSource(urls, local_files=local_files)
        result = await source.get_data()
        assert len(result) == 2
        assert "https://example.com/doc.pdf" in result
        assert "local:///tmp/uploads/report.docx" in result

    @pytest.mark.asyncio
    async def test_local_files_filtered_by_extension(self):
        """Local files should also respect allowed_extensions."""
        urls = []
        local_files = [
            {"filename": "report.pdf", "storage_path": "/tmp/uploads/report.pdf"},
            {"filename": "style.css", "storage_path": "/tmp/uploads/style.css"},
        ]
        source = UrlDataSource(
            urls, allowed_extensions=[".pdf"], local_files=local_files
        )
        result = await source.get_data()
        assert len(result) == 1
        assert "local:///tmp/uploads/report.pdf" in result

    @pytest.mark.asyncio
    async def test_empty_urls_with_local_files(self):
        """Works with only local files and no URLs."""
        local_files = [
            {"filename": "doc.pdf", "storage_path": "/tmp/doc.pdf"},
            {"filename": "img.png", "storage_path": "/tmp/img.png"},
        ]
        source = UrlDataSource([], local_files=local_files)
        result = await source.get_data()
        assert len(result) == 2

    def test_name_property(self):
        source = UrlDataSource([])
        assert source.name == "File"


class TestUrlDataProcessorFormatAgnostic:
    """Tests that UrlDataProcessor processes all file formats via kreuzberg."""

    @pytest.mark.asyncio
    async def test_create_chunks_from_pdf_url(self):
        """PDF files should be processed through kreuzberg with correct MIME type."""
        from data_sync.processors.file_data_processor import UrlDataProcessor

        source = UrlDataSource(["https://example.com/report.pdf"])
        processor = UrlDataProcessor(source, {})

        mock_response = MagicMock()
        mock_response.content = b"fake-pdf-bytes"
        mock_response.raise_for_status = MagicMock()

        mock_result = MagicMock()
        mock_result.pages = [{"content": "Page 1 content"}]
        mock_result.content = "Full content"

        with (
            patch(
                "data_sync.processors.file_data_processor.httpx.AsyncClient"
            ) as mock_client_cls,
            patch(
                "data_sync.processors.file_data_processor.extract_bytes",
                new_callable=AsyncMock,
                return_value=mock_result,
            ) as mock_extract,
        ):
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.head = AsyncMock(return_value=MagicMock(headers={}))
            mock_client_cls.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            await processor.load_data()
            docs = await processor.create_chunks_from_doc(
                "https://example.com/report.pdf"
            )

            assert len(docs) == 1
            assert docs[0].content == "Page 1 content"
            # Verify kreuzberg was called with correct MIME type
            mock_extract.assert_called_once()
            call_args = mock_extract.call_args
            assert call_args[0][1] == "application/pdf"

    @pytest.mark.asyncio
    async def test_create_chunks_from_docx_url(self):
        """DOCX files should be processed through kreuzberg (not skipped)."""
        from data_sync.processors.file_data_processor import UrlDataProcessor

        source = UrlDataSource(["https://example.com/doc.docx"])
        processor = UrlDataProcessor(source, {})

        mock_response = MagicMock()
        mock_response.content = b"fake-docx-bytes"
        mock_response.raise_for_status = MagicMock()

        mock_result = MagicMock()
        mock_result.pages = None
        mock_result.content = "Document content from DOCX"

        with (
            patch(
                "data_sync.processors.file_data_processor.httpx.AsyncClient"
            ) as mock_client_cls,
            patch(
                "data_sync.processors.file_data_processor.extract_bytes",
                new_callable=AsyncMock,
                return_value=mock_result,
            ) as mock_extract,
        ):
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.head = AsyncMock(return_value=MagicMock(headers={}))
            mock_client_cls.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            await processor.load_data()
            docs = await processor.create_chunks_from_doc(
                "https://example.com/doc.docx"
            )

            # DOCX should NOT be skipped anymore
            assert len(docs) == 1
            assert docs[0].content == "Document content from DOCX"
            mock_extract.assert_called_once()
            call_args = mock_extract.call_args
            assert (
                call_args[0][1]
                == "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            )

    @pytest.mark.asyncio
    async def test_create_chunks_from_html_url(self):
        """HTML files should be processed through kreuzberg."""
        from data_sync.processors.file_data_processor import UrlDataProcessor

        source = UrlDataSource(["https://example.com/page.html"])
        processor = UrlDataProcessor(source, {})

        mock_response = MagicMock()
        mock_response.content = b"<html><body>Hello</body></html>"
        mock_response.raise_for_status = MagicMock()

        mock_result = MagicMock()
        mock_result.pages = None
        mock_result.content = "Hello"

        with (
            patch(
                "data_sync.processors.file_data_processor.httpx.AsyncClient"
            ) as mock_client_cls,
            patch(
                "data_sync.processors.file_data_processor.extract_bytes",
                new_callable=AsyncMock,
                return_value=mock_result,
            ),
        ):
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            mock_client.head = AsyncMock(return_value=MagicMock(headers={}))
            mock_client_cls.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            await processor.load_data()
            docs = await processor.create_chunks_from_doc(
                "https://example.com/page.html"
            )

            assert len(docs) == 1
            assert docs[0].content == "Hello"

    @pytest.mark.asyncio
    async def test_create_chunks_from_local_file(self):
        """Local files (local://) should be read from disk, not downloaded."""
        from data_sync.processors.file_data_processor import UrlDataProcessor

        local_files = [
            {"filename": "report.pdf", "storage_path": "/tmp/uploads/report.pdf"},
        ]
        source = UrlDataSource([], local_files=local_files)
        processor = UrlDataProcessor(source, {})

        mock_result = MagicMock()
        mock_result.pages = [{"content": "Local page 1"}]
        mock_result.content = "Full local content"

        with (
            patch(
                "data_sync.processors.file_data_processor.httpx.AsyncClient"
            ) as mock_client_cls,
            patch(
                "data_sync.processors.file_data_processor.extract_bytes",
                new_callable=AsyncMock,
                return_value=mock_result,
            ),
            patch(
                "data_sync.processors.file_data_processor.aiofiles.open"
            ) as mock_aio_open,
        ):
            # No HTTP calls should be made
            mock_client = AsyncMock()
            mock_client_cls.return_value.__aenter__ = AsyncMock(
                return_value=mock_client
            )
            mock_client_cls.return_value.__aexit__ = AsyncMock(return_value=False)

            # Mock aiofiles.open for reading local file
            mock_file = AsyncMock()
            mock_file.read = AsyncMock(return_value=b"local-pdf-bytes")
            mock_aio_open.return_value.__aenter__ = AsyncMock(return_value=mock_file)
            mock_aio_open.return_value.__aexit__ = AsyncMock(return_value=False)

            await processor.load_data()
            docs = await processor.create_chunks_from_doc(
                "local:///tmp/uploads/report.pdf"
            )

            assert len(docs) == 1
            assert docs[0].content == "Local page 1"
            # Should NOT have called httpx.get for local files
            mock_client.get.assert_not_called()


class TestFileUrlPlugin:
    """Tests for FileUrlPlugin configuration."""

    def test_plugin_description_not_pdf_only(self):
        from plugins.builtin.knowledge_source.file.plugin import FileUrlPlugin

        plugin = FileUrlPlugin()
        schema = plugin.metadata.config_schema
        description = schema["properties"]["file_url"]["description"]
        assert "PDF" not in description or "DOCX" in description
        assert "Only links to PDF" not in description

    def test_plugin_supports_uploaded_files_config(self):
        from plugins.builtin.knowledge_source.file.plugin import FileUrlPlugin

        plugin = FileUrlPlugin()
        schema = plugin.metadata.config_schema
        assert "uploaded_files" in schema["properties"]

    @pytest.mark.asyncio
    async def test_create_processor_with_urls(self):
        from plugins.builtin.knowledge_source.file.plugin import FileUrlPlugin

        plugin = FileUrlPlugin()
        processor = await plugin.create_processor(
            {"file_url": ["https://example.com/doc.pdf"]},
            {},
            None,
        )
        assert processor is not None

    @pytest.mark.asyncio
    async def test_create_processor_with_uploaded_files(self):
        from plugins.builtin.knowledge_source.file.plugin import FileUrlPlugin

        plugin = FileUrlPlugin()
        processor = await plugin.create_processor(
            {
                "uploaded_files": [
                    {"filename": "doc.pdf", "storage_path": "/tmp/doc.pdf"}
                ]
            },
            {},
            None,
        )
        assert processor is not None

    @pytest.mark.asyncio
    async def test_create_processor_raises_when_no_files(self):
        from plugins.builtin.knowledge_source.file.plugin import FileUrlPlugin
        from litestar.exceptions import ClientException

        plugin = FileUrlPlugin()
        with pytest.raises(ClientException):
            await plugin.create_processor({}, {}, None)

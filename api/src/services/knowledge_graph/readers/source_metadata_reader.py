from typing import Any


class SourceMetadataReader:
    """Content reader that extracts text from a named field in source metadata."""

    def __init__(self, reader_options: dict[str, Any] | None = None) -> None:
        options = reader_options or {}
        self._field_name: str = str(options.get("field_name", "")).strip()

    def extract_from_context(
        self, context: dict[str, Any]
    ) -> tuple[str, dict[str, Any]]:
        if not self._field_name:
            raise ValueError(
                "Source metadata reader requires a 'field_name' option "
                "specifying which metadata field to read content from."
            )

        source_metadata = context.get("source_metadata")
        if not isinstance(source_metadata, dict):
            # No metadata available -- return empty content so the document
            # is still created (title, external link, etc. are preserved).
            return "", {"source_field": self._field_name}

        value = source_metadata.get(self._field_name)
        text = str(value) if value is not None else ""

        return text, {"source_field": self._field_name}

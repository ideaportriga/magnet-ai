import asyncio
import math
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
from open_ai.utils_new import get_embeddings
from services.knowledge_graph.readers.kreuzberg_reader import mime_type_from_filename
from services.observability import observability_context, observe


class ParsePdfResponse(BaseModel):
    pages: list[str]


class ParseDocumentResponse(BaseModel):
    pages: list[str]
    metadata: dict[str, Any] = {}


class SimilarityScoresRequest(BaseModel):
    query: str
    candidates: list[str]
    embedding_model: str


class SimilarityScore(BaseModel):
    text: str
    score: float


class SimilarityScoresResponse(BaseModel):
    scores: list[SimilarityScore]


def _cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


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

    @observe(
        name="Calculate similarity scores",
        description="Compare one text against a list of texts using an embedding model.",
        channel="production",
    )
    @post("/similarity-scores", status_code=HTTP_200_OK)
    async def similarity_scores(
        self, data: Annotated[SimilarityScoresRequest, Body()]
    ) -> SimilarityScoresResponse:
        """Compute cosine similarity between a query and each candidate text
        using the embedding model identified by its system name."""
        if not data.query:
            raise ClientException("No query provided")
        if not data.candidates:
            raise ClientException("No candidates to compare against provided")

        observability_context.update_current_span(
            input={
                "Query": data.query,
                "Candidates": data.candidates,
                "Embedding model": data.embedding_model,
            }
        )

        try:
            query_vector, *candidate_vectors = await asyncio.gather(
                get_embeddings(data.query, data.embedding_model),
                *(
                    get_embeddings(candidate, data.embedding_model)
                    for candidate in data.candidates
                ),
            )
        except LookupError as e:
            raise ClientException(str(e)) from e

        scores = [
            SimilarityScore(text=text, score=_cosine_similarity(query_vector, vector))
            for text, vector in zip(data.candidates, candidate_vectors)
        ]

        observability_context.update_current_span(
            output={"Scores": [score.model_dump() for score in scores]},
        )

        return SimilarityScoresResponse(scores=scores)

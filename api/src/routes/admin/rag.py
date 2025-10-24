from typing import Any

from litestar import Controller, post
from pydantic import BaseModel, Field

from services.observability import observability_context, observe
from services.observability.models import FeatureType
from services.retrieve import retrieve
from services.utils.metadata_filtering import metadata_filter_to_filter_object
from validation.rag_tools import RetrieveConfig


class RagRetrieve(BaseModel):
    user_message: str
    metadata_filter: list[dict[str, Any]] | None = Field(default=None)
    collection_id: str
    collection_display_name: str
    similarity_score_threshold: float = Field(default=0.0, ge=0.0, le=1.0)
    limit: int = Field(default=15, ge=0, le=50)


class RagController(Controller):
    path = "/rag"
    tags = ["rag_deprecated"]

    @observe(name="Previewing knowledge source", channel="preview", source="preview")
    @post("/retrieve")
    async def retrieve_handler(self, data: RagRetrieve) -> dict:
        observability_context.update_current_trace(
            name=data.collection_display_name, type=FeatureType.KNOWLEDGE_SOURCE.value
        )

        results = await retrieve(
            user_message=data.user_message,
            retrieve_config=RetrieveConfig(
                collection_system_names=[data.collection_id],
                similarity_score_threshold=data.similarity_score_threshold,
                allow_metadata_filter=True,
                use_keyword_search=True,
            ),
            max_chunks_retrieved=data.limit,
            filter=metadata_filter_to_filter_object(data.metadata_filter),
        )

        return {"results": results}

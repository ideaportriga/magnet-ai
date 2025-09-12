from litestar import Controller, post
from pydantic import BaseModel, Field

from services.observability import observability_context, observe
from services.retrieve import retrieve


class RagRetrieve(BaseModel):
    user_message: str
    collection_id: str
    similarity_score_threshold: float = Field(default=0.0, ge=0.0, le=1.0)
    limit: int = Field(default=15, ge=0, le=50)


class RagController(Controller):
    path = "/rag"
    tags = ["rag"]

    @observe(name="Previewing knowledge source", channel="preview", source="preview")
    @post("/retrieve")
    async def retrieve_handler(self, data: RagRetrieve) -> dict:
        observability_context.update_current_trace(
            name=data.collection_id, type="knowledge-source"
        )

        results = await retrieve(
            user_message=data.user_message,
            collection_system_names=[data.collection_id],
            max_chunks_retrieved=data.limit,
            similarity_score_threshold=data.similarity_score_threshold,
        )

        return {"results": results}

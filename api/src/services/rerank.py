import time

from config.providers import Config
from models import DocumentSearchResult
from openai_model.utils import get_model_by_system_name
from services.ai_services.factory import get_ai_provider
from services.observability import observability_context
from services.observability.models import (
    FeatureType,
    LLMType,
    ObservationModelDetails,
    ObservedFeature,
)
from services.observability.utils import get_usage_and_cost_details
from stores import get_db_store

store = get_db_store()

DEFAULT_PROVIDER: str = "azure_open_ai"


async def rerank(
    documents: DocumentSearchResult, model_system_name: str, top_n: int, query: str
) -> DocumentSearchResult:
    llm = None
    provider = DEFAULT_PROVIDER
    top_n = top_n or 5

    observed_feature = ObservedFeature(
        type=FeatureType.RERANKING, system_name=FeatureType.RERANKING.value
    )

    # Prepare model details for traces and metrics
    call_model = ObservationModelDetails()
    if model_system_name:
        call_model.update(name=model_system_name)
        model_config = await get_model_by_system_name(model_system_name)
        if model_config:
            llm = model_config.get("ai_model")
            model_display_name = model_config.get("display_name")
            if model_display_name and isinstance(model_display_name, str):
                call_model.update(display_name=model_display_name)
            provider_from_config = model_config.get("provider")
            if provider_from_config and isinstance(provider_from_config, str):
                provider = provider_from_config

    if not llm:
        raise ValueError("Model configuration is missing or invalid.")

    # Prepare provider details for traces and metrics
    provider_config = Config.AI_PROVIDERS.get(provider)
    provider_display_name = provider
    if provider_config:
        provider_display_name = provider_config.get("label")
        call_model.update(otel_gen_ai_system=provider_config.get("otel_gen_ai_system"))
    call_model.update(provider=provider, provider_display_name=provider_display_name)

    # Prepare model parameters for traces and metrics
    call_model.update(parameters={"llm": llm, "top_n": top_n})

    with observability_context.observe_feature(observed_feature):
        # Call the LLM
        provider_instance = get_ai_provider(provider)
        call_start_time = time.time()
        rerank = await provider_instance.rerank(
            documents=documents,
            llm=llm,
            query=query,
            top_n=top_n,
            truncation=False,
        )
        call_end_time = time.time()
        call_duration = call_end_time - call_start_time

        # Prepare usage and cost details for traces and metrics
        call_usage, call_cost = await get_usage_and_cost_details(
            rerank.usage, model_system_name
        )

        # Prepare input and output for traces and metrics
        call_input = {
            "query": query,
            "documents": [
                {
                    "metadata": doc.metadata,
                    "content": doc.content,
                    "score": float(doc.score),
                }
                for doc in documents
            ],
        }
        call_output = (
            [
                {
                    "metadata": doc.metadata,
                    "content": doc.content,
                    "score": float(doc.score),
                    "original_index": doc.original_index,
                }
                for doc in rerank.data
            ],
        )

        # Update current span with usage, cost and output
        observability_context.update_current_span(
            name="Rerank documents",
            description=f"Asking LLM to rerank {len(documents)} documents.",
            model=call_model,
            usage_details=call_usage,
            cost_details=call_cost,
            input=call_input,
            output=call_output,
        )

        # Record chat completion metrics
        observability_context.record_llm_metrics(
            llm_type=LLMType.RERANKING,
            model=call_model,
            duration=call_duration,
            usage=call_usage,
            cost=call_cost,
        )

        # Sort documents by updated score
        rerank.data.sort(key=lambda doc: doc.score, reverse=True)

        return rerank.data

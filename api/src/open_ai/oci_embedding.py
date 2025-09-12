import oci

from config.providers import Config


def oci_embedding(texts: list[str], chunk_size: int | None = 0) -> list[list[float]]:
    provider_name = "oci"
    provider_config = Config.AI_PROVIDERS.get(provider_name)

    if not provider_config:
        raise ValueError(f"Provider '{provider_name}' is not supported.")

    config = provider_config["connection"]

    compartment_id = config["compartment_id"]
    endpoint = config["endpoint"]
    key_content = config["key_content"].replace("\\n", "\n")
    oci_config = {
        "user": config["user"],
        "fingerprint": config["fingerprint"],
        "tenancy": config["tenancy"],
        "region": config["region"],
        "key_content": key_content,
    }

    generative_ai_inference_client = (
        oci.generative_ai_inference.GenerativeAiInferenceClient(
            config=oci_config,
            service_endpoint=endpoint,
            retry_strategy=oci.retry.NoneRetryStrategy(),
            timeout=(10, 240),
        )
    )

    embed_text_detail = oci.generative_ai_inference.models.EmbedTextDetails()
    embed_text_detail.serving_mode = (
        oci.generative_ai_inference.models.OnDemandServingMode(
            model_id="cohere.embed-multilingual-v3.0"
        )
    )
    embed_text_detail.inputs = texts
    embed_text_detail.truncate = "NONE"
    embed_text_detail.compartment_id = compartment_id
    embed_text_response = generative_ai_inference_client.embed_text(embed_text_detail)

    return embed_text_response.data.embeddings

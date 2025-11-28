import asyncio
import time

import oci
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_message import ChatCompletionMessage

from services.ai_services.interface import AIProviderInterface
from services.ai_services.models import EmbeddingResponse, ModelUsage


class OCIProvider(AIProviderInterface):
    def __init__(self, config):
        self.config = config["connection"]
        self.compartment_id = self.config["compartment_id"]
        self.model_default = config["defaults"].get("model")
        self.temperature_default = config["defaults"].get("temperature")
        self.top_p_default = config["defaults"].get("top_p")
        self.max_tokens = config["defaults"].get("max_tokens")
        self.frequency_penalty = config["defaults"].get("frequency_penalty")
        self.top_k = config["defaults"].get("top_k")

        key_content = self.config["key_content"].replace("\\n", "\n")
        self.oci_config = {
            "user": self.config["user"],
            "fingerprint": self.config["fingerprint"],
            "tenancy": self.config["tenancy"],
            "region": self.config["region"],
            "key_content": key_content,
        }
        self.endpoint = self.config["endpoint"]

        self.client = oci.generative_ai_inference.GenerativeAiInferenceClient(
            config=self.oci_config,
            service_endpoint=self.endpoint,
            retry_strategy=oci.retry.NoneRetryStrategy(),
            timeout=(10, 240),
        )

    async def create_chat_completion(
        self,
        messages: list[ChatCompletionMessageParam],
        model: str | None = None,
        temperature: float | None = None,
        top_p: float | None = None,
        max_tokens: int | None = None,
        response_format: dict | None = None,
        tools: list[dict] | None = None,
        model_config: dict | None = None,
    ) -> ChatCompletion:
        model = model or self.model_default
        temperature = temperature or self.temperature_default
        top_p = top_p or self.top_p_default
        max_tokens = max_tokens or self.max_tokens

        message_content = next(
            (msg["content"] for msg in messages if msg["role"] == "user"),
            None,
        )
        preamble_override = next(
            (msg["content"] for msg in messages if msg["role"] == "system"),
            None,
        )

        chat_request = oci.generative_ai_inference.models.CohereChatRequest()
        chat_request.message = message_content
        chat_request.max_tokens = max_tokens
        chat_request.temperature = temperature
        chat_request.top_p = top_p
        chat_request.top_k = self.top_k
        chat_request.preamble_override = preamble_override
        chat_request.frequency_penalty = self.frequency_penalty

        chat_detail = oci.generative_ai_inference.models.ChatDetails()
        chat_detail.serving_mode = (
            oci.generative_ai_inference.models.OnDemandServingMode(
                model_id=model,
            )
        )

        chat_detail.chat_request = chat_request
        chat_detail.compartment_id = self.compartment_id

        loop = asyncio.get_running_loop()
        chat_response = await loop.run_in_executor(
            None,
            lambda: self.client.chat(chat_detail),
        )

        if not chat_response:
            raise Exception("No response from OCI for chat API")

        # Extract the relevant data from the response
        response_data = chat_response.data
        response_content = response_data.chat_response
        model_id = response_data.model_id
        content = response_content.text

        # Construct the ChatCompletion object with the correct types
        return ChatCompletion(
            id="oci_completion",
            object="chat.completion",
            created=int(time.time()),
            model=model_id,
            choices=[
                Choice(
                    message=ChatCompletionMessage(
                        role="assistant",
                        content=content,
                    ),
                    finish_reason="stop",
                    index=0,
                ),
            ],
        )

    async def get_embeddings(
        self,
        text: str,
        llm: str | None = None,
    ) -> EmbeddingResponse:
        compartment_id = self.config["compartment_id"]
        endpoint = self.config["endpoint"]
        key_content = self.config["key_content"].replace("\\n", "\n")
        oci_config = {
            "user": self.config["user"],
            "fingerprint": self.config["fingerprint"],
            "tenancy": self.config["tenancy"],
            "region": self.config["region"],
            "key_content": key_content,
        }

        # Call the OCI API to get the embeddings
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
            oci.generative_ai_inference.models.OnDemandServingMode(model_id=llm)
        )
        embed_text_detail.inputs = [text]
        embed_text_detail.truncate = "NONE"
        embed_text_detail.compartment_id = compartment_id

        loop = asyncio.get_running_loop()
        embed_text_response = await loop.run_in_executor(
            None,
            lambda: generative_ai_inference_client.embed_text(embed_text_detail),
        )

        if not embed_text_response:
            raise Exception("No response from OCI for embeddings API")

        # Usage in OCI for embed models is simply the number of characters
        usage_in_characters = len(text)

        return EmbeddingResponse(
            data=embed_text_response.data.embeddings,
            usage=ModelUsage(
                input_units="characters",
                input=usage_in_characters,
                total=usage_in_characters,
            ),
        )

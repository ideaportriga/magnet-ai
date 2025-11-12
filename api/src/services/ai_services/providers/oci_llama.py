import asyncio
import time

import oci
from openai.types.chat import ChatCompletion, ChatCompletionMessageParam
from openai.types.chat.chat_completion import Choice
from openai.types.chat.chat_completion_message import ChatCompletionMessage

from services.ai_services.interface import AIProviderInterface


class OCILlamaProvider(AIProviderInterface):
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
        system_message = next(
            (msg["content"] for msg in messages if msg["role"] == "system"),
            None,
        )

        oci_messages = []

        system_content = oci.generative_ai_inference.models.TextContent(
            text=system_message,
        )
        system_message_obj = oci.generative_ai_inference.models.Message(
            role="SYSTEM",
            content=[system_content],
        )
        oci_messages.append(system_message_obj)
        user_content = oci.generative_ai_inference.models.TextContent(
            text=message_content,
        )
        user_message = oci.generative_ai_inference.models.Message(
            role="USER",
            content=[user_content],
        )
        oci_messages.append(user_message)

        chat_request = oci.generative_ai_inference.models.GenericChatRequest(
            api_format=oci.generative_ai_inference.models.BaseChatRequest.API_FORMAT_GENERIC,
            messages=oci_messages,
            max_tokens=max_tokens,
            temperature=temperature,
            top_p=top_p,
            top_k=self.top_k,
            presence_penalty=0,
            frequency_penalty=self.frequency_penalty,
        )

        chat_detail = oci.generative_ai_inference.models.ChatDetails(
            serving_mode=oci.generative_ai_inference.models.OnDemandServingMode(
                model_id=model,
            ),
            chat_request=chat_request,
            compartment_id=self.compartment_id,
        )

        try:
            loop = asyncio.get_running_loop()
            chat_response = await loop.run_in_executor(
                None,
                lambda: self.client.chat(chat_detail),
            )
            print(vars(chat_response))
            data = chat_response.data
            response_content = data.chat_response.choices[0].message.content[0].text
            model_id = data.model_id

            return ChatCompletion(
                id="oci_completion",
                object="chat.completion",
                created=int(time.time()),
                model=model_id,
                choices=[
                    Choice(
                        message=ChatCompletionMessage(
                            role="assistant",
                            content=response_content,
                        ),
                        finish_reason="stop",
                        index=0,
                    ),
                ],
            )
        except oci.exceptions.ServiceError as e:
            # Handle error logging and return a safe response or re-raise
            print(f"OCI service error: {e}")
            raise

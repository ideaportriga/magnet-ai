# ROADMAP: LiteLLM Integration Improvement

> Дата: 2026-03-04  
> Статус: **In Progress** — Фазы 0-4, 6, 8-10 реализованы  
> Автор: AI-assisted analysis

---

## Содержание

1. [Текущее состояние](#1-текущее-состояние)
2. [Архитектурные проблемы](#2-архитектурные-проблемы)
3. [Roadmap по фазам](#3-roadmap-по-фазам)
   - [Фаза 0: Очистка и рефакторинг](#фаза-0-очистка-и-рефакторинг)
   - [Фаза 1: Консолидация провайдеров на LiteLLM](#фаза-1-консолидация-провайдеров-на-litellm)
   - [Фаза 2: Streaming](#фаза-2-streaming)
   - [Фаза 3: Расширенные capabilities](#фаза-3-расширенные-capabilities)
   - [Фаза 4: Observability через LiteLLM callbacks](#фаза-4-observability-через-litellm-callbacks)
   - [Фаза 5: Advanced Router features](#фаза-5-advanced-router-features)
   - [Фаза 6: Cost management и бюджетирование](#фаза-6-cost-management-и-бюджетирование)
   - [Фаза 7: Guardrails и безопасность](#фаза-7-guardrails-и-безопасность)
   - [Фаза 8: Speech-to-Text и Text-to-Speech](#фаза-8-speech-to-text-и-text-to-speech)
   - [Фаза 9: Responses API / Codex / Non-chat endpoints](#фаза-9-responses-api--codex--non-chat-endpoints)
   - [Фаза 10: Нативные провайдеры и CustomLLM](#фаза-10-нативные-провайдеры-и-customllm)
4. [Детали по каждому предложению](#4-детали-по-каждому-предложению)

---

## 1. Текущее состояние

### Архитектура `ai_services`

```
AIProviderInterface (abstract)
├── BaseLiteLLMProvider          ← базовый класс для LiteLLM-based провайдеров
│   ├── OpenAIProvider           ← litellm_provider = "openai"
│   ├── AzureProvider            ← litellm_provider = "azure"
│   ├── AzureAIProvider          ← litellm_provider = "azure_ai"
│   ├── GroqProvider             ← litellm_provider = "groq"
│   ├── TmpLocalProvider         ← litellm_provider = "" (OpenAI-compatible)
│   └── LiteLLMProvider          ← Router mode + Direct mode
├── BaseOCIProvider              ← нативный OCI SDK (не LiteLLM)
│   ├── OCIProvider
│   └── OCILlamaProvider
```

### Сущности данных

**Provider** (endpoint + credentials):
- `system_name`, `name`, `type` (openai, azure_open_ai, azure_ai, groq, oci, litellm...)
- `endpoint` — API base URL
- `connection_config` — не-секретные настройки
- `secrets_encrypted` — ключи и креды (автодекрипт через EncryptedJsonB)
- `metadata_info` — defaults, router_config, otel_gen_ai_system

**AIModel** (настройки работы модели):
- `system_name`, `ai_model`, `display_name`, `type` (prompts, embeddings)
- `provider_system_name` — FK на Provider
- `routing_config` — rpm, tpm, fallback_models, cache, retries, timeout, litellm_params
- Capabilities: `json_mode`, `json_schema`, `tool_calling`, `reasoning`
- Pricing: `price_input`, `price_output`, `price_cached` + unit counts

### Паттерны вызовов

```
Application Code
    └── open_ai/utils_new.py  (wrappers: create_chat_completion, get_embeddings)
        └── factory.get_ai_provider(provider_system_name)
            ├── returns cached or new provider instance  
            └── provider.create_chat_completion(messages, model, ...)
                ├── BaseLiteLLMProvider._build_completion_params()
                ├── BaseLiteLLMProvider._execute_completion()
                │   ├── litellm.acompletion()  (direct mode)
                │   └── router.acompletion()   (fallback mode, global Router)
                └── LiteLLMProvider._execute_completion()
                    ├── self.router.acompletion()  (own Router)
                    └── litellm.acompletion()  (direct mode)
```

### Что хорошо

- ✅ Чёткое разделение Provider (credentials) и Model (config)
- ✅ `routing_config` на уровне модели — гибкая настройка per-model
- ✅ `BaseLiteLLMProvider` с поддержкой `get_supported_openai_params()` — автоматическая адаптация параметров
- ✅ Global Router с fallback_models — cross-model failover
- ✅ Кэширование provider instances с TTL
- ✅ Observability через OpenTelemetry spans + метрики
- ✅ Поддержка reasoning models (reasoning_effort)
- ✅ Secret placeholder resolution (`{api_key}` → actual value)

---

## 2. Архитектурные проблемы

### 2.1 Дублирование провайдеров ← Критическое

**Проблема**: `OpenAIProvider`, `AzureProvider`, `AzureAIProvider`, `GroqProvider` — это практически пустые наследники `BaseLiteLLMProvider`, отличающиеся только строкой `litellm_provider`. LiteLLM сам знает, как работать с 100+ провайдерами.

**Текущий код** `GroqProvider`:
```python
class GroqProvider(BaseLiteLLMProvider):
    litellm_provider = "groq"
```

**Проблема**: При добавлении Anthropic, Gemini, Bedrock, Mistral, Together AI и т.д. нужно каждый раз создавать новый файл `providers/anthropic.py` с одной строкой. Это не scale-ится.

### 2.2 Два Router-а ← Запутанная архитектура

1. **Global Router** (`router.py`) — инициализируется из ВСЕХ моделей в БД, используется для fallback в `BaseLiteLLMProvider._execute_completion()`
2. **Provider-level Router** (`LiteLLMProvider`) — инициализируется из `router_config.model_list` в метаданных конкретного провайдера

Они работают параллельно и потенциально конфликтуют. Когда модель с `fallback_models` вызывается через обычный `OpenAIProvider`, она идёт через Global Router. Когда через `LiteLLMProvider` с `model_list` — через Provider Router.

### 2.3 Нет streaming ← Функциональный пробел 

`AIProviderInterface` не определяет streaming метод. Все вызовы — `await provider.create_chat_completion()` возвращают полный `ChatCompletion`. Для UX чат-ботов и агентов это критическое ограничение.

### 2.4 Ручное управление capability моделей 

Поля `json_mode`, `json_schema`, `tool_calling`, `reasoning` в AIModel заполняются вручную. LiteLLM имеет `get_model_info()` и `supports_*()` для автоматического определения capabilities 1000+ моделей.

### 2.5 Собственный cost tracking вместо LiteLLM built-in

Pricing хранится в AIModel (`price_input`, `price_output`), а LiteLLM имеет `completion_cost()` с актуальной базой цен для 1000+ моделей (обновляется с каждым релизом).

### 2.6 Dead code 

- `get_provider_by_model()` в `utils.py` — нигде не вызывается
- `is_model_in_router()` — экспортируется, но не используется
- `router_completion()` / `router_embedding()` — не используются из application code
- `build_litellm_model_entry()` в `utils.py` — дублирует логику `_build_router_config()` в `router.py`

### 2.7 Модель кэша устарела для LiteLLM

`ResponseCache` в `cache.py` — самописный in-memory кэш с TTL. LiteLLM имеет встроенный кэш (`litellm.cache = Cache(type="local")`) с поддержкой Redis, S3, и семантического кэшинга.

### 2.8 OCI не через LiteLLM

`BaseOCIProvider` использует нативный OCI SDK с `run_in_executor`. LiteLLM [поддерживает OCI GenAI](https://docs.litellm.ai/docs/providers/oci_generative_ai) нативно.

---

## 3. Roadmap по фазам

### Фаза 0: Очистка и рефакторинг
> Приоритет: 🔴 High | Сложность: Low | Время: 1-2 дня

**Цель**: Удалить dead code, упростить текущую структуру без изменения поведения.

| # | Задача | Файлы |
|---|--------|-------|
| 0.1 | Удалить `get_provider_by_model()` из `utils.py` — не используется | `utils.py` |
| 0.2 | Удалить `build_litellm_model_entry()` из `utils.py` — дублирует `router.py` | `utils.py` |
| 0.3 | Убрать `is_model_in_router` из `__all__` в `factory.py` (или использовать) | `factory.py` |
| 0.4 | Убрать `router_completion` / `router_embedding` из `__all__` если не нужны | `factory.py` |
| 0.5 | Объединить `RoutingConfig` — сейчас есть 2 класса: dataclass в `models.py` и Pydantic в `schemas.py` | `models.py`, `schemas.py` |

---

### Фаза 1: Консолидация провайдеров на LiteLLM
> Приоритет: 🔴 High | Сложность: Medium | Время: 3-5 дней

**Цель**: Заменить отдельные провайдеры (OpenAI, Azure, Groq и т.д.) единым LiteLLM-based провайдером. Добавить поддержку 100+ провайдеров без нового кода.

#### 1.1 Унифицированный `UniversalLiteLLMProvider`

Вместо N провайдеров — один класс, который определяет `litellm_provider` из `provider.type`:

```python
# Маппинг type → litellm prefix
PROVIDER_TYPE_TO_LITELLM_PREFIX = {
    "openai": "openai",
    "azure_open_ai": "azure",
    "azure_ai": "azure_ai",
    "groq": "groq",
    "anthropic": "anthropic",
    "gemini": "gemini",
    "bedrock": "bedrock",
    "together_ai": "together_ai",
    "mistral": "mistral",
    "ollama": "ollama",
    "deepseek": "deepseek",
    "fireworks_ai": "fireworks_ai",
    "cohere": "cohere",
    "litellm": "",  # model already has prefix
    "datakom": "",  # custom OpenAI-compatible
}

class UniversalLiteLLMProvider(BaseLiteLLMProvider):
    """Single provider class supporting all LiteLLM-backed providers."""
    
    def __init__(self, config: dict):
        # Determine litellm prefix from provider type
        provider_type = config.get("type", "")
        self.litellm_provider = PROVIDER_TYPE_TO_LITELLM_PREFIX.get(provider_type, "")
        super().__init__(config)
```

#### 1.2 Backwards-compatible factory

```python
# factory.py — новый маппинг
provider_classes = {
    # Всё через UniversalLiteLLMProvider:
    "openai": UniversalLiteLLMProvider,
    "azure_open_ai": UniversalLiteLLMProvider,
    "azure_ai": UniversalLiteLLMProvider,
    "groq": UniversalLiteLLMProvider,
    "anthropic": UniversalLiteLLMProvider,
    "gemini": UniversalLiteLLMProvider,
    "bedrock": UniversalLiteLLMProvider,
    "together_ai": UniversalLiteLLMProvider,
    "mistral": UniversalLiteLLMProvider,
    "ollama": UniversalLiteLLMProvider,
    "deepseek": UniversalLiteLLMProvider,
    "litellm": LiteLLMProvider,  # Router mode остаётся
    "datakom": UniversalLiteLLMProvider,
    # OCI пока остаётся нативным:
    "oci": OCIProvider,
    "oci_llama": OCILlamaProvider,
}
```

#### 1.3 Миграция OCI на LiteLLM (отдельная sub-task)

LiteLLM поддерживает OCI GenAI. Можно мигрировать с нативного OCI SDK:

```python
# Старый способ:
"type": "oci"
# Новый способ:
"type": "oci_genai"  # litellm prefix: "oci_genai"  
# connection_config: {"oci_config_profile": "DEFAULT", "region_name": "us-chicago-1"}
```

**Миграция данных**: обновить `type` в таблице providers, обновить `connection_config` формат.

#### 1.4 Новые провайдеры «из коробки»

После консолидации добавление нового провайдера = одна запись в БД:

```sql
INSERT INTO providers (system_name, name, type, endpoint, secrets_encrypted)
VALUES ('anthropic-main', 'Anthropic Claude', 'anthropic', NULL, '{"api_key": "sk-ant-..."}');

INSERT INTO ai_models (system_name, ai_model, provider_system_name, type, display_name)
VALUES ('claude-sonnet', 'claude-sonnet-4-20250514', 'anthropic-main', 'prompts', 'Claude Sonnet 4');
```

Никаких изменений в коде. Поддерживаемые новые провайдеры:

| Provider | type | Требует endpoint? | Примечания |
|----------|------|-------------------|------------|
| Anthropic | `anthropic` | Нет | Claude 3.5/4 |
| Google Gemini | `gemini` | Нет | Gemini 2.0 |
| AWS Bedrock | `bedrock` | Нет | Требует AWS credentials |
| Mistral | `mistral` | Нет | |
| Together AI | `together_ai` | Нет | |
| Fireworks | `fireworks_ai` | Нет | |
| DeepSeek | `deepseek` | Нет | |
| Ollama | `ollama` | Да (local) | `http://localhost:11434` |
| Cohere | `cohere` | Нет | Также embeddings + rerank |
| Perplexity | `perplexity` | Нет | С web search |
| xAI (Grok) | `xai` | Нет | |
| AI21 | `ai21` | Нет | |

---

### Фаза 2: Streaming
> Приоритет: 🔴 High | Сложность: Medium-High | Время: 3-5 дней

**Цель**: Добавить поддержку streaming для chat completions — для UX чат-ботов и агентов.

#### 2.1 Обновить `AIProviderInterface`

```python
class AIProviderInterface(ABC):
    @abstractmethod
    async def create_chat_completion(self, ...) -> ChatCompletion:
        pass

    # Новый метод:
    @abstractmethod
    async def create_chat_completion_stream(
        self,
        messages: list[ChatCompletionMessageParam],
        model: str | None,
        temperature: float | None,
        top_p: float | None,
        max_tokens: int | None = None,
        response_format: dict | None = None,
        tools: list[dict] | None = None,
        tool_choice: str | dict | None = None,
        model_config: dict | None = None,
    ) -> AsyncIterator[ChatCompletionChunk]:
        pass
```

#### 2.2 Реализация в `BaseLiteLLMProvider`

```python
async def create_chat_completion_stream(self, ...) -> AsyncIterator:
    params = self._build_completion_params(...)
    params["stream"] = True
    params["stream_options"] = {"include_usage": True}  # usage в финальном chunk
    
    response = await litellm.acompletion(**params)
    async for chunk in response:
        yield chunk
```

#### 2.3 Обёртка в `open_ai/utils_new.py`

```python
async def create_chat_completion_stream(
    *,
    model_system_name: str,
    messages: list,
    ...
) -> AsyncIterator[ChatCompletionChunk]:
    provider = await get_ai_provider(provider_system_name)
    
    async for chunk in provider.create_chat_completion_stream(
        messages=messages,
        model=llm,
        ...
    ):
        yield chunk
    
    # После завершения стрима — записать observability
```

#### 2.4 SSE endpoint в API

```python
@router.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    async def event_generator():
        async for chunk in create_chat_completion_stream(...):
            yield f"data: {chunk.model_dump_json()}\n\n"
        yield "data: [DONE]\n\n"
    
    return StreamingResponse(event_generator(), media_type="text/event-stream")
```

---

### Фаза 3: Расширенные capabilities
> Приоритет: 🟡 Medium | Сложность: Medium | Время: 5-7 дней

#### 3.1 Auto-detect model capabilities

Использовать `litellm.get_model_info()` для автоматического определения capabilities вместо ручного задания:

```python
async def sync_model_capabilities(model: AIModel) -> dict:
    """Auto-detect and sync model capabilities from LiteLLM."""
    try:
        full_model = f"{litellm_prefix}/{model.ai_model}"
        info = litellm.get_model_info(full_model)
        
        return {
            "json_mode": info.get("supports_response_schema", False),
            "json_schema": info.get("supports_response_schema", False),
            "tool_calling": info.get("supports_function_calling", False),
            "reasoning": info.get("supports_reasoning", False),
            "supports_vision": info.get("supports_vision", False),
            "supports_audio_input": info.get("supports_audio_input", False),
            "supports_audio_output": info.get("supports_audio_output", False),
            "supports_pdf_input": info.get("supports_pdf_input", False),
            "supports_prompt_caching": info.get("supports_prompt_caching", False),
            "supports_web_search": info.get("supports_web_search", False),
            "max_input_tokens": info.get("max_input_tokens"),
            "max_output_tokens": info.get("max_output_tokens"),
        }
    except Exception:
        return {}  # fallback to manual config
```

**Применение**: 
- Вызывать при создании/обновлении модели через API
- Добавить кнопку "Auto-detect" в UI
- При startup — background sync для всех моделей

#### 3.2 Расширить AIModel schema

Добавить новые поля в `AIModel`:

```python
class AIModelFieldsMixin(BaseModel):
    # ... existing fields ...
    
    # New capability fields:
    supports_vision: bool = False
    supports_audio_input: bool = False
    supports_audio_output: bool = False
    supports_pdf_input: bool = False
    supports_prompt_caching: bool = False
    supports_web_search: bool = False
    supports_streaming: bool = True  # most models support it
    
    # Context window info (auto-populated from litellm):
    max_input_tokens: int | None = None
    max_output_tokens: int | None = None
```

#### 3.3 Vision support

LiteLLM прозрачно поддерживает multi-modal messages:

```python
messages = [{
    "role": "user",
    "content": [
        {"type": "text", "text": "What's in this image?"},
        {"type": "image_url", "image_url": {"url": "data:image/png;base64,..."}}
    ]
}]
```

**Что нужно**: Убедиться, что `create_chat_completion` не трансформирует/фильтрует `content` когда это list. Текущий код уже передаёт `messages` as-is → ✅ должно работать.

#### 3.4 Prompt caching (Anthropic / OpenAI)

Добавить поддержку `cache_control` в messages для Anthropic prompt caching:

```python
messages = [{
    "role": "system",
    "content": [{
        "type": "text",
        "text": "Very long system prompt...",
        "cache_control": {"type": "ephemeral"}  # Anthropic prompt caching
    }]
}]
```

**Что нужно**: 
- Уровень провайдера — ничего, LiteLLM пробрасывает `cache_control`
- Уровень `prompt_templates` — добавить опцию `enable_prompt_caching`
- Уровень cost tracking — учитывать `cache_creation_input_tokens` и `cache_read_input_tokens`

#### 3.5 Structured output (Pydantic models)

LiteLLM принимает `response_format=MyPydanticModel`:

```python
from pydantic import BaseModel

class ExtractedInfo(BaseModel):
    name: str
    date: str
    summary: str

response = await litellm.acompletion(
    model="openai/gpt-4o",
    messages=[...],
    response_format=ExtractedInfo  # LiteLLM handles the conversion
)
```

**Что нужно**:
- Обновить `AIProviderInterface.create_chat_completion()` — добавить `response_format: dict | type[BaseModel] | None`
- В `BaseLiteLLMProvider._transform_response_format()` — пропускать Pydantic классы без трансформации (litellm обработает сам)
- В `open_ai/utils_new.py` — пробрасывать `response_format` as-is

#### 3.6 Reasoning / Extended Thinking

Текущая поддержка `reasoning_effort` — хорошая, но неполная. LiteLLM поддерживает:

```python
# Anthropic extended thinking
response = await litellm.acompletion(
    model="anthropic/claude-3-7-sonnet-20250219",
    messages=[...],
    thinking={"type": "enabled", "budget_tokens": 10000}
)

# OpenAI reasoning_effort  
response = await litellm.acompletion(
    model="openai/o3-mini",
    messages=[...],
    reasoning_effort="high"
)
```

**Что нужно**:
- Добавить `thinking` параметр в `create_chat_completion` для Anthropic
- Или через `routing_config.litellm_params` — уже работает

---

### Фаза 4: Observability через LiteLLM callbacks
> Приоритет: 🟡 Medium | Сложность: Medium | Время: 2-3 дня

**Цель**: Использовать LiteLLM callback system для более rich observability вместо ручного инструментирования в `utils_new.py`.

#### 4.1 Custom callback для observability

```python
from litellm.integrations.custom_logger import CustomLogger

class MagnetAILogger(CustomLogger):
    """LiteLLM callback that integrates with our observability system."""
    
    async def async_log_success_event(self, kwargs, response_obj, start_time, end_time):
        # Автоматически получаем:
        # - kwargs["model"] — actual model used
        # - kwargs["messages"] — input
        # - response_obj — full response
        # - response_obj._hidden_params["response_cost"] — cost from LiteLLM
        # - start_time, end_time — timing
        
        duration = (end_time - start_time).total_seconds()
        model = kwargs.get("model")
        cost = response_obj._hidden_params.get("response_cost", 0)
        
        # Integrate with existing observability
        observability_context.record_llm_metrics(
            model=model,
            duration=duration,
            cost=cost,
        )
    
    async def async_log_failure_event(self, kwargs, response_obj, start_time, end_time):
        # Log errors with full context
        pass

# Регистрация при startup:
litellm.callbacks = [MagnetAILogger()]
```

**Преимущества**:
- Автоматический tracking ВСЕХ LiteLLM вызовов (completion, embedding, rerank)
- Встроенный cost calculation от LiteLLM
- Tracking fallback events
- Не нужно вручную оборачивать каждый вызов

#### 4.2 Интеграция с OpenTelemetry

LiteLLM имеет встроенную интеграцию с OTEL:

```python
litellm.callbacks = ["otel"]  # OpenTelemetry integration

# Или кастомная конфигурация
from litellm.integrations.opentelemetry import OpenTelemetry
otel = OpenTelemetry(tracer_provider=my_tracer_provider)
litellm.callbacks = [otel]
```

**Что нужно решить**: Совместить с текущим `observability_context.observe_feature()` — либо заменить, либо дополнить.

---

### Фаза 5: Advanced Router features
> Приоритет: 🟡 Medium | Сложность: Medium | Время: 3-5 дней

#### 5.1 Упростить до одного глобального Router

**Проблема**: Два Router-а (global + provider-level) создают путаницу.

**Предложение**: Использовать только Global Router, убрать provider-level Router из `LiteLLMProvider`.

```python
# Единый Router при старте приложения
router = Router(
    model_list=all_models_from_db,
    routing_strategy="simple-shuffle",
    fallbacks=fallback_map_from_db,
    num_retries=0,
    enable_pre_call_checks=True,
)
```

Все вызовы идут через `router.acompletion(model=system_name)`.

#### 5.2 Advanced routing strategies

Текущая стратегия: `simple-shuffle`. LiteLLM поддерживает:

| Стратегия | Когда использовать |
|-----------|-------------------|
| `simple-shuffle` | Default, random distribution |
| `least-busy` | Минимизация latency при высокой нагрузке |
| `latency-based-routing` | Автоматический выбор самого быстрого deployment |
| `cost-based-routing` | Минимизация стоимости |
| `usage-based-routing` | Равномерное распределение по использованию |

**Предложение**: Сделать `routing_strategy` настраиваемым через конфиг приложения или даже per-model.

#### 5.3 Context window fallbacks

LiteLLM Router поддерживает автоматический fallback при превышении context window:

```python
router = Router(
    model_list=[...],
    context_window_fallbacks=[
        {"gpt-4o-mini": ["gpt-4o"]},  # если mini не вместит — fallback на полную модель
    ],
    content_policy_fallbacks=[
        {"gpt-4o": ["claude-sonnet"]},  # если OpenAI отклонит — fallback на Claude
    ],
)
```

**Что нужно**: Добавить `context_window_fallbacks` и `content_policy_fallbacks` в `routing_config` модели.

#### 5.4 Tag-based routing

LiteLLM может маршрутизировать по тегам:

```python
# В model_list:
{"model_name": "gpt-4", "litellm_params": {...}, "model_info": {"tags": ["eu", "production"]}}

# При вызове:
response = await router.acompletion(
    model="gpt-4",
    messages=[...],
    metadata={"tags": ["eu"]}  # только EU deployments
)
```

**Применение**: разделение по регионам, environments (prod/staging), compliance requirements.

#### 5.5 Provider budget config

LiteLLM Router поддерживает бюджетирование по провайдерам:

```python
router = Router(
    model_list=[...],
    provider_budget_config={
        "openai": {"budget_limit": 100.0, "time_period": "1d"},
        "azure": {"budget_limit": 200.0, "time_period": "1d"},
    }
)
```

---

### Фаза 6: Cost management и бюджетирование
> Приоритет: 🟢 Low-Medium | Сложность: Low | Время: 2-3 дня

#### 6.1 Использовать `litellm.completion_cost()` 

Вместо хранения цен в AIModel — использовать LiteLLM built-in cost calculation:

```python
response = await provider.create_chat_completion(...)

# LiteLLM автоматически вычисляет стоимость:
cost = response._hidden_params.get("response_cost", 0)

# Или явно:
cost = litellm.completion_cost(completion_response=response)
```

**Преимущества**:
- Автоматически актуальные цены (обновляются с каждым релизом litellm)
- Учитываются спецтокены: cached, reasoning, audio
- Не нужно вручную вводить цены для каждой модели

**Что сохранить**: Поля `price_input/price_output` в AIModel — для override/custom pricing. Использовать LiteLLM как fallback.

#### 6.2 Custom pricing override

```python
async def get_response_cost(response, model_system_name: str) -> float:
    """Get cost: custom pricing from DB, fallback to LiteLLM."""
    model_config = await get_model_by_system_name(model_system_name)
    
    if model_config.get("price_input") and model_config.get("price_output"):
        # Use custom pricing from DB
        usage = response.usage
        input_cost = float(model_config["price_input"]) * usage.prompt_tokens
        output_cost = float(model_config["price_output"]) * usage.completion_tokens
        return input_cost + output_cost
    
    # Fallback to LiteLLM's built-in pricing
    return litellm.completion_cost(completion_response=response)
```

#### 6.3 Auto-populate pricing from LiteLLM

При создании модели — автоматически заполнять цены:

```python
info = litellm.get_model_info(full_model_name)
price_input = info.get("input_cost_per_token")
price_output = info.get("output_cost_per_token")
```

---

### Фаза 7: Guardrails и безопасность
> Приоритет: 🟢 Low | Сложность: Medium | Время: 3-5 дней

#### 7.1 Content moderation

```python
litellm.callbacks = [
    MagnetAILogger(),  # наш observability
]

# Глобальный модерационный фильтр:
litellm.openai_moderations_model_name = "text-moderation-latest"
```

#### 7.2 Custom guardrail

```python
from litellm.integrations.custom_guardrail import CustomGuardrail

class PIIGuardrail(CustomGuardrail):
    """Block PII in inputs/outputs."""
    
    def __init__(self):
        super().__init__(
            guardrail_name="pii_filter",
            event_hook=GuardrailEventHooks.pre_call,
        )
    
    async def async_pre_call_hook(self, data, call_type):
        # Check for PII patterns
        messages = data.get("messages", [])
        for msg in messages:
            if contains_pii(msg.get("content", "")):
                raise litellm.exceptions.RejectedRequestError(
                    message="PII detected in input"
                )
```

#### 7.3 Banned keywords / max budget per user

```python
litellm.banned_keywords_list = ["sensitive_topic_1", "sensitive_topic_2"]
litellm.max_budget = 1000.0  # Global budget limit
```

---

### Фаза 8: Speech-to-Text и Text-to-Speech
> Приоритет: 🟡 Medium-High | Сложность: Medium | Время: 5-7 дней

**Цель**: Унифицировать STT/TTS через `AIProviderInterface` и `litellm.atranscription()` / `litellm.aspeech()`, сохраняя возможность нативных реализаций для неподдерживаемых провайдеров.

#### 8.1 Текущее состояние STT в приложении

Сейчас STT реализован как отдельная подсистема `speech_to_text/transcription/` со своей иерархией:

```
BaseTranscriber (abc)          ← base.py
├── WhisperHttpTranscriber     ← whisper_http/ (вызов внешнего models-service)
├── MistralVoxtralTranscriber  ← mistral_transcribe/ (прямой HTTP к Mistral API)
├── ElevenLabsTranscriber      ← elevenlabs_transcribe/ (ElevenLabs SDK)
├── AzureWhisperTranscriber    ← azure_whisper/
├── OciWhisperTranscriber      ← oci_whisper/
├── OracleTranscriber          ← oracle_transcribe/
└── MockTranscriber            ← mock_transcribe/
```

Также есть `BaseDiarization` с аналогичной иерархией (OCI Speech, Pyannote, Mistral, Azure Conversation, ElevenLabs, мок).

**Проблемы:**
- STT провайдеры не интегрированы с `ai_services` — у них свои credentials (через env vars), свой caching, свой error handling
- Нет единого `provider.transcribe()` интерфейса — credentials от Mistral STT (`MISTRAL_API_KEY`) хардкодятся через `os.getenv()`, а не из Provider entity
- Нельзя переключить STT провайдер через БД — нужно менять конфиг/код
- TTS вообще не реализован в проекте

#### 8.2 Что поддерживает LiteLLM для STT

| Provider | Функция | Примечание |
|----------|---------|------------|
| OpenAI Whisper | `litellm.atranscription(model="whisper-1")` | Полная поддержка |
| OpenAI GPT-4o Audio | `litellm.atranscription(model="gpt-4o-transcribe")` | Новые модели |
| Azure Whisper | `litellm.atranscription(model="azure/whisper-1")` | Через Azure OpenAI |
| Groq Whisper | `litellm.atranscription(model="groq/whisper-large-v3")` | OpenAI-compatible path |
| Deepgram | `litellm.atranscription(model="deepgram/nova-2")` | Dedicated config |
| ElevenLabs | `litellm.atranscription(model="elevenlabs/...")` | ✅ Supported |
| Fireworks AI | `litellm.atranscription(model="fireworks_ai/...")` | Dedicated config |
| vLLM (hosted Whisper) | `litellm.atranscription(model="hosted_vllm/...")` | Self-hosted |
| **Mistral Voxtral** | ❌ **НЕ поддерживается** | Нужен CustomLLM |
| OCI Speech | ❌ **НЕ поддерживается** | Нужен CustomLLM |

#### 8.3 Что поддерживает LiteLLM для TTS

| Provider | Модель | Примечание |
|----------|--------|------------|
| OpenAI | `litellm.aspeech(model="tts-1")` | tts-1, tts-1-hd |
| Azure OpenAI | `litellm.aspeech(model="azure/tts-1")` | Deployment-based |
| Azure Speech Service | `litellm.aspeech(model="azure/speech/...")` | AVA/Cognitive |
| ElevenLabs | `litellm.aspeech(model="elevenlabs/eleven_multilingual_v2")` | ✅ Полная поддержка |
| Vertex AI / Gemini | `litellm.aspeech(model="vertex_ai/...")` | Google Cloud |
| AWS Polly | `litellm.aspeech(model="aws_polly/...")` | AWS |
| MiniMax | `litellm.aspeech(model="minimax/...")` | — |
| RunwayML | `litellm.aspeech(model="runwayml/...")` | — |

#### 8.4 Расширение `AIProviderInterface`

```python
class AIProviderInterface(ABC):
    # ... existing methods ...
    
    # Optional: Implement for STT support
    async def transcribe(
        self,
        file: BinaryIO,
        model: str | None = None,
        language: str | None = None,
        prompt: str | None = None,
        response_format: str | None = None,  # json, text, srt, verbose_json, vtt
        timestamp_granularities: list[str] | None = None,
    ) -> TranscriptionResponse:
        raise NotImplementedError("transcribe is optional for this provider")
    
    # Optional: Implement for TTS support
    async def speech(
        self,
        input: str,
        model: str | None = None,
        voice: str | None = None,
        response_format: str | None = None,  # mp3, opus, aac, flac, wav, pcm
        speed: float | None = None,
    ) -> bytes:
        raise NotImplementedError("speech is optional for this provider")
```

#### 8.5 Реализация STT в `BaseLiteLLMProvider`

```python
async def transcribe(
    self,
    file: BinaryIO,
    model: str | None = None,
    language: str | None = None,
    prompt: str | None = None,
    response_format: str | None = None,
    timestamp_granularities: list[str] | None = None,
) -> TranscriptionResponse:
    """Transcribe audio using LiteLLM."""
    model = model or self.config.get("defaults", {}).get("stt_model")
    if not model:
        raise ValueError("STT model must be specified")
    
    full_model = self._get_model_name(model)
    params = self._build_litellm_params()
    params["model"] = full_model
    params["file"] = file
    
    if language:
        params["language"] = language
    if prompt:
        params["prompt"] = prompt
    if response_format:
        params["response_format"] = response_format
    if timestamp_granularities:
        params["timestamp_granularities"] = timestamp_granularities
    
    response = await litellm.atranscription(**params)
    return response
```

#### 8.6 Реализация TTS в `BaseLiteLLMProvider`

```python
async def speech(
    self,
    input: str,
    model: str | None = None,
    voice: str | None = None,
    response_format: str | None = None,
    speed: float | None = None,
) -> bytes:
    """Generate speech using LiteLLM."""
    model = model or self.config.get("defaults", {}).get("tts_model")
    if not model:
        raise ValueError("TTS model must be specified")
    
    full_model = self._get_model_name(model)
    params: dict = {
        "model": full_model,
        "input": input,
    }
    
    if self.api_key:
        params["api_key"] = self.api_key
    if self.endpoint:
        params["api_base"] = self.endpoint
    if voice:
        params["voice"] = voice
    if response_format:
        params["response_format"] = response_format
    if speed:
        params["speed"] = speed
    
    response = await litellm.aspeech(**params)
    # response is HttpxBinaryResponseContent
    return response.read()
```

#### 8.7 Стратегия миграции существующего STT

**Этап 1 — Adapter pattern (не ломаем существующий код)**:

```python
class LiteLLMTranscriberAdapter(BaseTranscriber):
    """Adapter: wraps AIProviderInterface.transcribe() into BaseTranscriber API."""
    
    def __init__(self, storage: PgDataStorage, cfg: TranscriptionCfg, 
                 provider_system_name: str, model: str):
        super().__init__(storage, cfg)
        self._provider_system_name = provider_system_name
        self._model = model
    
    async def _transcribe(self, file_id: str) -> dict:
        provider = await get_ai_provider(self._provider_system_name)
        buf = await self._storage.get_file(file_id)
        
        response = await provider.transcribe(
            file=buf,
            model=self._model,
            language=self._cfg.internal_cfg.get("language"),
        )
        
        return {
            "text": response.text,
            "segments": response.segments or [],
        }
```

Так можно постепенно заменять `WhisperHttpTranscriber` → `LiteLLMTranscriberAdapter`, `AzureWhisperTranscriber` → `LiteLLMTranscriberAdapter` и т.д., не ломая остальную логику diarization pipeline.

**Этап 2 — Мигрировать credentials в Provider entity**:
- Убрать `os.getenv("MISTRAL_API_KEY")` из `MistralVoxtralTranscriber`
- Использовать Provider entity `type: "mistral"` с `secrets_encrypted: {"api_key": "..."}`

**Этап 3 — Нативные STT (Mistral, OCI) через CustomLLM** (см. Фазу 10)

#### 8.8 Настройка through Provider + Model entities

**Provider для TTS/STT:**
```json
{
  "system_name": "elevenlabs-main",
  "name": "ElevenLabs",
  "type": "elevenlabs",
  "secrets_encrypted": { "api_key": "el-..." }
}
```

**Model для STT:**
```json
{
  "system_name": "elevenlabs-stt",
  "ai_model": "scribe_v1",
  "provider_system_name": "elevenlabs-main",
  "type": "stt",
  "display_name": "ElevenLabs Scribe v1 (STT)"
}
```

**Model для TTS:**
```json
{
  "system_name": "elevenlabs-tts",
  "ai_model": "eleven_multilingual_v2",
  "provider_system_name": "elevenlabs-main",
  "type": "tts",
  "display_name": "ElevenLabs Multilingual v2 (TTS)",
  "configs": { "default_voice": "alloy", "voices": ["alloy", "echo", "fable"] }
}
```

Тип модели (`type`) расширяется: `"prompts"` | `"embeddings"` | `"rerank"` | `"stt"` | `"tts"`.

---

### Фаза 9: Responses API / Codex / Non-chat endpoints
> Приоритет: 🟢 Low-Medium | Сложность: Medium | Время: 3-5 дней

**Цель**: Поддержать модели, которые работают через API отличный от `/chat/completions` — OpenAI Responses API, Codex (GPT-5), будущие endpoint-ы.

#### 9.1 Проблема

Текущий `AIProviderInterface.create_chat_completion()` предполагает, что все модели используют Chat Completions API. Но:
- **OpenAI Responses API** (`/v1/responses`) — новый формат с `input`/`instructions` вместо `messages`, поддержкой tool use, web search, file search
- **GPT-5 Codex** — использует Responses API с `background=True` для длительных задач
- **Realtime API** — WebSocket-based для real-time voice
- **Image Generation** (`/v1/images/generations`) — DALL-E и т.д.
- **OCR** — Mistral и другие

#### 9.2 Что поддерживает LiteLLM

LiteLLM поддерживает **12 типов endpoints**:

| Endpoint type | LiteLLM функция | Поддержанные провайдеры |
|---------------|-----------------|------------------------|
| Chat Completion | `litellm.acompletion()` | 100+ провайдеров |
| Responses API | `litellm.aresponses()` | OpenAI, Azure, xAI, Perplexity, Databricks, OpenRouter |
| Embedding | `litellm.aembedding()` | 40+ провайдеров |
| Image Generation | `litellm.aimage_generation()` | OpenAI, Azure, Vertex AI, Bedrock |
| Audio Speech (TTS) | `litellm.aspeech()` | OpenAI, Azure, ElevenLabs, AWS Polly, Vertex AI |
| Audio Transcription (STT) | `litellm.atranscription()` | OpenAI, Azure, Groq, Deepgram, ElevenLabs |
| Rerank | `litellm.arerank()` | Cohere, Azure AI, Jina, Together |
| OCR | через completion | Mistral, Azure |
| Realtime | WebSocket | OpenAI |
| Batch | `litellm.create_batch()` | OpenAI, Azure |
| Moderation | `litellm.amoderation()` | OpenAI |
| Completion (legacy) | `litellm.atext_completion()` | OpenAI (davinci), Anthropic |

#### 9.3 Лёгкое решение: Responses API через LiteLLM translation

LiteLLM умеет **транслировать** Responses API вызовы в Chat Completions для провайдеров, которые нативно не поддерживают Responses API (через `LiteLLMCompletionTransformationHandler`). Это значит, что можно использовать Responses API как единый интерфейс:

```python
# Responses API call — LiteLLM транслирует в chat/completions для Claude
response = await litellm.aresponses(
    model="anthropic/claude-sonnet-4-20250514",
    input="Explain quantum computing",
    instructions="You are a physics professor",
)
```

#### 9.4 Расширение `AIProviderInterface` (опционально)

```python
class AIProviderInterface(ABC):
    # ... existing ...
    
    # Optional: For Responses API / Codex
    async def create_response(
        self,
        input: str | list,
        model: str | None = None,
        instructions: str | None = None,
        tools: list | None = None,
        max_output_tokens: int | None = None,
        temperature: float | None = None,
        stream: bool = False,
        background: bool = False,  # For GPT-5 Codex
        **kwargs,
    ) -> ResponseObject:
        raise NotImplementedError("create_response is optional")
    
    # Optional: For image generation
    async def generate_image(
        self,
        prompt: str,
        model: str | None = None,
        size: str | None = None,
        quality: str | None = None,
        n: int = 1,
    ) -> ImageResponse:
        raise NotImplementedError("generate_image is optional")
```

#### 9.5 Рекомендация

**Не торопиться с Responses API** — сейчас Chat Completions API покрывает 99% use cases. Responses API имеет смысл, когда:
- Нужен built-in web search / file search
- Нужен background mode (GPT-5 Codex для длительных задач)
- Нужна стейтфулная multi-turn conversation (через `previous_response_id`)

Когда потребуется — добавить `create_response()` метод в интерфейс и реализовать через `litellm.aresponses()`.

---

### Фаза 10: Нативные провайдеры и CustomLLM
> Приоритет: 🟡 Medium | Сложность: Medium | Время: 3-5 дней

**Цель**: Определить правильную стратегию для моделей/провайдеров, которые НЕ поддерживаются LiteLLM, но нужны в приложении.

#### 10.1 Текущая проблема

Пример: Mistral STT (Voxtral) — не поддерживается `litellm.atranscription()`. Сейчас реализован через прямой HTTP в `MistralVoxtralTranscriber` с хардкоженным `os.getenv("MISTRAL_API_KEY")`. То же для OCI Speech diarization — нативный OCI SDK.

ElevenLabs STT — **уже поддерживается LiteLLM** (`ElevenLabsAudioTranscriptionConfig`), но в проекте реализован нативно через ElevenLabs SDK. Можно мигрировать.

#### 10.2 Три стратегии для нативных провайдеров

##### Стратегия A: LiteLLM `CustomLLM` (рекомендуется для новых нативных)

LiteLLM позволяет регистрировать кастомных провайдеров через `litellm.custom_provider_map`. После регистрации они работают через `litellm.acompletion()`, `litellm.atranscription()` и т.д. со всеми плюшками (callbacks, cost tracking, retry).

```python
from litellm.llms.custom_llm import CustomLLM
from litellm.types.utils import ModelResponse

class MistralSTTCustomProvider(CustomLLM):
    """Custom LiteLLM provider for Mistral Voxtral STT."""
    
    async def acompletion(self, model, messages, api_base, api_key, **kwargs):
        """Called by litellm when model has 'mistral_stt/' prefix."""
        # Extract audio file from messages or kwargs
        file = kwargs.get("file")
        language = kwargs.get("language")
        
        # Call Mistral STT API directly
        async with httpx.AsyncClient() as client:
            headers = {"Authorization": f"Bearer {api_key}"}
            endpoint = f"{api_base}/v1/audio/transcriptions"
            
            response = await client.post(
                endpoint,
                headers=headers,
                data={"model": model, "diarize": "true"},
                files={"file": file},
            )
            data = response.json()
        
        # Return in LiteLLM's standard format
        return ModelResponse(
            id="mistral-stt-" + str(uuid.uuid4()),
            choices=[{"message": {"content": data["text"]}}],
            model=model,
        )

# Регистрация при startup приложения:
import litellm

litellm.custom_provider_map.append({
    "provider": "mistral_stt",
    "custom_handler": MistralSTTCustomProvider(),
})
litellm._custom_providers.append("mistral_stt")

# Теперь можно вызывать:
response = await litellm.acompletion(
    model="mistral_stt/voxtral-mini-latest",
    api_key="...",
    api_base="https://api.mistral.ai",
)
```

**Плюсы**: Вписывается в litellm экосистему, работают callbacks/observability/retries.  
**Минусы**: Ограничения — `CustomLLM` поддерживает `completion`, `streaming`, `embedding`, `image_generation`, но **не** `transcription` или `speech` напрямую. Для STT/TTS нужен workaround через `acompletion`.

##### Стратегия B: Нативный провайдер внутри `ai_services` (текущий подход)

Сохранить отдельную реализацию, но интегрировать с Provider entity вместо env vars:

```python
class NativeMistralSTTProvider(AIProviderInterface):
    """Native Mistral STT implementation for features not supported by LiteLLM."""
    
    def __init__(self, config: dict):
        connection = config.get("connection", {})
        self.api_key = connection.get("api_key")
        self.endpoint = connection.get("endpoint", "https://api.mistral.ai")
        self.default_model = config.get("defaults", {}).get("model", "voxtral-mini-latest")
    
    async def create_chat_completion(self, *args, **kwargs):
        raise NotImplementedError("Use transcribe() for STT models")
    
    async def transcribe(self, file, model=None, language=None, **kwargs):
        """Mistral Voxtral STT with diarization support."""
        model = model or self.default_model
        async with httpx.AsyncClient(timeout=3600) as client:
            headers = {"Authorization": f"Bearer {self.api_key}"}
            data = {"model": model, "diarize": "true"}
            if language:
                data["language"] = language
                
            response = await client.post(
                f"{self.endpoint}/v1/audio/transcriptions",
                headers=headers,
                data=data,
                files={"file": file},
            )
            return response.json()
```

**Плюсы**: Полный контроль, поддержка уникальных фич (diarization).  
**Минусы**: Вне экосистемы litellm — нет автоматического cost tracking, callbacks, retries.

##### Стратегия C: Hybrid (рекомендуемая)

Использовать **LiteLLM для всего, что поддерживается**, и **нативные провайдеры для остального**, с единым `AIProviderInterface`:

```python
# factory.py — обновлённый маппинг
provider_classes = {
    # LiteLLM-based (100+ провайдеров):
    "openai": UniversalLiteLLMProvider,
    "azure_open_ai": UniversalLiteLLMProvider,
    "anthropic": UniversalLiteLLMProvider,
    "groq": UniversalLiteLLMProvider,
    "elevenlabs": UniversalLiteLLMProvider,  # tts + stt через litellm
    "deepgram": UniversalLiteLLMProvider,     # stt через litellm
    ...
    
    # Нативные (уникальные фичи):
    "mistral_stt": NativeMistralSTTProvider,   # diarization не в litellm
    "oci": OCIProvider,                         # native SDK
    "oci_speech": NativeOCISpeechProvider,      # diarization не в litellm
}
```

#### 10.3 Как правильно добавить нативный провайдер

**Шаг 1**: Проверить, поддерживает ли LiteLLM нужную операцию для провайдера.

```python
# Быстрая проверка
import litellm

# Для chat completion:
try:
    params = litellm.get_supported_openai_params("mistral/model-name")
    print("Supported via litellm")
except:
    print("Not supported — need native")

# Для STT — проверить наличие config:
from litellm.utils import ProviderConfigManager
config = ProviderConfigManager.get_provider_audio_transcription_config(
    model="mistral/voxtral-mini-latest",
    provider=litellm.LlmProviders.MISTRAL,
)
# config is None → не поддерживается
```

**Шаг 2**: Если НЕ поддерживается → создать нативный провайдер:

```
api/src/services/ai_services/providers/
  native/
    __init__.py
    mistral_stt.py        ← NativeMistralSTTProvider
    oci_speech.py          ← NativeOCISpeechProvider  
    base_native.py         ← BaseNativeProvider (shared HTTP logic)
```

```python
# base_native.py
class BaseNativeProvider(AIProviderInterface):
    """Base for providers that bypass LiteLLM."""
    
    def __init__(self, config: dict):
        connection = config.get("connection", {})
        self.api_key = connection.get("api_key")
        self.endpoint = connection.get("endpoint")
        defaults = config.get("defaults", {})
        self.default_model = defaults.get("model")
    
    async def create_chat_completion(self, *args, **kwargs):
        raise NotImplementedError(
            f"{self.__class__.__name__} does not support chat completion. "
            "Use the appropriate method (transcribe, speech, etc.)"
        )
```

**Шаг 3**: Зарегистрировать в factory:

```python
# factory.py
from services.ai_services.providers.native.mistral_stt import NativeMistralSTTProvider

provider_classes = {
    ...
    "mistral_stt": NativeMistralSTTProvider,
}
```

**Шаг 4**: Создать Provider + Model в БД:

```sql
-- Provider
INSERT INTO providers (system_name, name, type, endpoint, secrets_encrypted)
VALUES ('mistral-stt', 'Mistral STT', 'mistral_stt', 
        'https://api.mistral.ai', '{"api_key": "..."}');

-- Model
INSERT INTO ai_models (system_name, ai_model, provider_system_name, type, display_name)
VALUES ('voxtral-mini', 'voxtral-mini-latest', 'mistral-stt', 'stt', 'Mistral Voxtral Mini');
```

#### 10.4 Дерево решений: LiteLLM vs Native

```
Нужна модель/операция
│
├─ Поддерживается litellm?
│  ├─ ДА → UniversalLiteLLMProvider (Фаза 1) ✅
│  └─ НЕТ → Нужны ли уникальные фичи (diarization, custom params)?
│     ├─ НЕТ, стандартный STT/TTS/chat → Стратегия A: CustomLLM для litellm
│     └─ ДА, уникальные фичи → Стратегия B: Native provider
│        └─ Наследует BaseNativeProvider, регистрируется в factory
```

#### 10.5 Контрибьюция в LiteLLM

Если нативный провайдер оказался полезным, можно контрибьютить поддержку обратно в LiteLLM:
- LiteLLM — open source (MIT license)
- Provider config добавляется через `BaseLLMHTTPHandler` + `BaseConfig`
- Структура: `litellm/llms/{provider_name}/{operation}/transformation.py`
- Пример: ElevenLabs (`litellm/llms/elevenlabs/text_to_speech/transformation.py`)

После принятия PR — переключить с Native на UniversalLiteLLMProvider.

---

## 4. Детали по каждому предложению

### Матрица приоритетов

| Фаза | Приоритет | Сложность | Время | Зависимости | Impact | Статус |
|------|-----------|-----------|-------|-------------|--------|--------|
| 0. Очистка | 🔴 High | Low | 1-2д | — | Чистота кода | ✅ Done |
| 1. Консолидация провайдеров | 🔴 High | Medium | 3-5д | Фаза 0 | +100 провайдеров, -5 файлов | ✅ Done |
| 2. Streaming | 🔴 High | Medium-High | 3-5д | — | UX чат-ботов | ✅ Done |
| 8. STT / TTS | 🟡 Medium-High | Medium | 5-7д | Фаза 1 | Единый audio pipeline | ✅ Done |
| 3. Capabilities | 🟡 Medium | Medium | 5-7д | Фаза 1 | Vision, audio, structured output | ✅ Done |
| 4. Observability | 🟡 Medium | Medium | 2-3д | — | Упрощение кода, rich metrics | ✅ Done |
| 10. Native providers | 🟡 Medium | Medium | 3-5д | Фаза 1 | Mistral STT, OCI, custom | ✅ Done |
| 6. Cost management | 🟢 Low-Med | Low | 2-3д | — | Актуальные цены | ✅ Done |
| 5. Advanced Router | 🟡 Medium | Medium | 3-5д | Фаза 1 | Reliability, cost optimization | 🔲 Todo |
| 9. Responses API | 🟢 Low-Med | Medium | 3-5д | Фаза 1 | Codex, web search | ✅ Done |
| 7. Guardrails | 🟢 Low | Medium | 3-5д | — | Безопасность | 🔲 Todo |

### Рекомендуемый порядок

```
Фаза 0 (1-2д) → Фаза 1 (3-5д) → Фаза 2 (3-5д) → Фаза 10 (3-5д) → Фаза 8 (5-7д) → Фаза 4 (2-3д) → Фаза 6 (2-3д) → Фаза 3 (5-7д) → Фаза 5 (3-5д) → Фаза 9 (3-5д) → Фаза 7 (3-5д)
```

Общее время: ~35-50 рабочих дней (7-10 недель).

### Compatibility layer для старых провайдеров

При миграции на `UniversalLiteLLMProvider` (Фаза 1) — обратная совместимость обеспечивается через factory pattern:

```python
# factory.py — provider_classes mapping
# Старые типы ("openai", "azure_open_ai", "groq") → UniversalLiteLLMProvider
# Новые типы ("anthropic", "gemini", "bedrock") → UniversalLiteLLMProvider  
# Специальные ("litellm" с Router) → LiteLLMProvider
# Legacy ("oci", "oci_llama") → OCIProvider (пока не мигрированы)
```

**Никаких изменений для вызывающего кода** — `get_ai_provider()` возвращает тот же `AIProviderInterface`. Все текущие call sites (`utils_new.py`, `rerank.py`, controllers) продолжают работать.

### Миграция данных

При Фазе 1 миграция данных **не требуется**:
- `provider.type` остаётся прежним ("openai", "azure_open_ai", etc.)
- `provider.connection_config` и `secrets_encrypted` — формат не меняется
- `provider.metadata_info` — формат не меняется
- `model.routing_config` — формат не меняется

Единственное изменение — в Python коде: `provider_classes` mapping в `factory.py`.

### Рекомендации по `routing_config` структуре

Текущая структура `routing_config` хорошая. Рекомендуемые дополнения:

```python
class RoutingConfig(BaseModel):
    # Existing:
    rpm: int | None = None
    tpm: int | None = None
    fallback_models: list[str] = []
    cache_enabled: bool = False
    cache_ttl: int = 3600
    num_retries: int | None = None
    retry_after: int | None = None
    timeout: int | None = None
    priority: int | None = None
    weight: float | None = None
    litellm_params: dict = {}
    
    # New (Фаза 5):
    context_window_fallbacks: list[str] | None = None
    content_policy_fallbacks: list[str] | None = None
    routing_strategy: str | None = None  # override global strategy for this model
    tags: list[str] | None = None  # for tag-based routing
    
    # New (Фаза 3):
    enable_prompt_caching: bool = False  # Anthropic/OpenAI prompt caching
```

---

## Приложение: Текущие call-site паттерны

### Основной flow (90% вызовов)

```
Agent/PromptTemplate/RAGTool code
  → create_chat_completion_from_prompt_template()    [open_ai/utils_new.py]
    → create_chat_completion()                        [open_ai/utils_new.py]
      → get_model_by_system_name(model_system_name)   [openai_model/utils.py]
      → get_ai_provider(provider_system_name)          [factory.py]
      → provider.create_chat_completion(model_config=model_config)
        → BaseLiteLLMProvider._build_completion_params()
        → BaseLiteLLMProvider._execute_completion()
          → litellm.acompletion() OR router.acompletion()
```

### Embedding flow

```
KnowledgeGraph / DocumentSearch
  → get_embeddings(text, model_system_name)    [open_ai/utils_new.py]
    → get_ai_provider(provider_system_name) 
    → provider.get_embeddings(text, llm)
      → litellm.aembedding()
```

### Rerank flow

```
RAGTools
  → rerank(documents, model_system_name, ...)  [services/rerank.py]
    → get_ai_provider(provider_system_name)
    → provider.rerank(query, documents, llm, ...)
      → litellm.arerank()
```

### STT flow (текущий, standalone)

```
Note-Taker / Transcription Job
  → TranscriberFactory.create(model="elevenlabs")   [speech_to_text/transcription/]
    → ElevenLabsTranscriber._transcribe(file_id)     [elevenlabs_transcribe/models.py]
      → ElevenLabs SDK (или httpx)                    ← собственные credentials через env vars
```

### STT flow (целевой, через ai_services)

```
Note-Taker / Transcription Job
  → transcribe(file, model_system_name)              [open_ai/utils_new.py — новый wrapper]
    → get_ai_provider(provider_system_name)           [factory.py]
    → provider.transcribe(file, model)                [BaseLiteLLMProvider или Native]
      → litellm.atranscription() OR native HTTP
```

При реализации Фаз 1-10 основные chat/embedding/rerank flow остаются **неизменными** для вызывающего кода. STT/TTS мигрируются через adapter pattern (Фаза 8.7) без breaking changes.

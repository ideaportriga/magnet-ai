# Agent System — Architecture

> Описание модульной архитектуры кода агентов после рефакторинга.
> Дата: март 2026.

---

## Обзор

Система агентов обрабатывает пользовательские сообщения через трёхступенчатый конвейер:

```
User Message
     │
     ▼
┌─────────────────┐
│  Classification  │  — определение intent + выбор topic
└────────┬────────┘
         │ intent = "topic"
         ▼
┌─────────────────┐
│ Topic Execution  │  — цикл LLM ↔ Actions (до 5 итераций)
└────────┬────────┘
         │
         ▼
  Assistant Message
```

Если intent ≠ `topic` (greeting, farewell, off_topic, request_not_clear, other), цикл обработки topic пропускается и сразу возвращается `assistant_message` из classification.

---

## Структура модулей

```
services/agents/
├── __init__.py              # Public API: execute_agent, get_agent_by_system_name
├── services.py              # Оркестратор (241 строк)
├── classification.py        # Классификация intent и topic (178 строк)
├── topic_execution.py       # Основной цикл агента (343 строки)
├── confirmation.py          # Обработка user confirmation (75 строк)
├── tool_schema.py           # Генерация ChatCompletionTool из actions (394 строки)
├── message_builder.py       # Конвертация истории → ChatCompletion messages (126 строк)
├── memory.py                # Стратегии управления контекстом (43 строки)
├── exceptions.py            # Иерархия кастомных исключений (33 строки)
├── models.py                # Pydantic-модели данных (614 строк)
│
├── actions/
│   ├── execute.py                       # Роутер action → executor (86 строк)
│   ├── action_execute_api_tool.py       # API action executor
│   ├── action_execute_rag.py            # RAG action executor
│   ├── action_execute_retrieval.py      # Retrieval action executor
│   ├── action_execute_prompt_template.py# Prompt Template action executor
│   ├── action_execute_mcp_tool.py       # MCP Tool action executor
│   └── action_execute_knowledge_graph.py# Knowledge Graph action executor
│
├── conversations/           # CRUD для бесед (отдельная подсистема)
├── post_process/            # Пост-обработка ответов
├── slack/                   # Slack-интеграция
├── teams/                   # Teams-интеграция
├── whatsapp/                # WhatsApp-интеграция
└── utils/                   # Вспомогательные утилиты
```

---

## Описание модулей

### `services.py` — Оркестратор

Точка входа. Содержит функцию `execute_agent()`, которая:

1. Загружает конфигурацию агента (из БД или `config_override`)
2. Определяет тип текущего запроса:
   - **Confirmation flow** — пользователь подтверждает/отклоняет action call → делегирует в `confirmation.py`
   - **PASS mode** — экспериментальный: пропуск classification, берётся первый topic
   - **Обычный flow** — делегирует classification в `classification.py`
3. Запускает `execute_topic()` из `topic_execution.py`
4. Собирает финальный `AgentConversationMessageAssistant`

Также содержит `get_agent_by_system_name()` для загрузки агента из БД.

Все функции из подмодулей **реэкспортируются** через `services.py` для обратной совместимости — внешний код может продолжать импортировать из `services.agents.services`.

### `classification.py` — Классификация

Функция `classify_conversation()`:

- Вызывает LLM через prompt template для определения intent и topic
- **3 попытки** с инъекцией ошибки парсинга в контекст ретрая
- Обработка JSON-галлюцинаций LLM: trailing commas, `//` comments, markdown code fences
- Валидация: если intent = "topic", проверяет что topic существует
- **Graceful fallback**: при исчерпании попыток возвращает `REQUEST_NOT_CLEAR` вместо краша

Вспомогательная функция `_extract_json_string()` — извлечение JSON из произвольного LLM-ответа.

### `topic_execution.py` — Основной цикл

Функция `execute_topic()`:

```
while iteration < MAX_ITERATIONS (5):
    1. Собрать context messages (через MemoryStrategy)
    2. Вызвать LLM с tools
    3. Если есть tool calls с requires_confirmation → вернуть для подтверждения
    4. Если есть assistant_message → вернуть результат
    5. Если есть tool calls → выполнить actions → добавить в steps → следующая итерация
```

Защитные механизмы:
- **Topic-level timeout**: `AGENT_TOPIC_TIMEOUT_SECONDS` (по умолчанию 120с, через env)
- **Action-level timeout**: `AGENT_ACTION_TIMEOUT_SECONDS` (по умолчанию 30с, через env)
- **Sanitized errors**: внутренние ошибки actions не утекают в ответ пользователю
- **Graceful degradation**: при исчерпании итераций возвращает последний доступный `assistant_message` вместо exception

Также содержит `create_action_call_requests()` — парсинг tool calls из LLM-ответа в `AgentActionCallRequest`.

### `confirmation.py` — Подтверждение Actions

Функция `create_action_call_steps()`:

- Принимает список action requests + user confirmations
- Для подтверждённых — выполняет action
- Для отклонённых — возвращает сообщение об отклонении
- Ошибки выполнения sanitized через `_sanitize_action_error()`

### `tool_schema.py` — Генерация Tool-схем

Конвертирует `AgentAction` → `ChatCompletionToolParam` для OpenAI API:

| Action Type       | Источник параметров                              |
|-------------------|--------------------------------------------------|
| `API`             | ApiServer → tool → `parameters.input`            |
| `MCP_TOOL`        | MCPServer → tool → `inputSchema`                 |
| `RAG`             | Metadata fields из коллекций RAG-тула            |
| `RETRIEVAL`       | Metadata fields из коллекций Retrieval-тула      |
| `PROMPT_TEMPLATE` | Фиксированная схема `{userMessage: string}`      |
| `KNOWLEDGE_GRAPH` | Из `get_agent_tool_specs()` или fallback-схема   |

Для actions с `requires_confirmation` добавляет параметр `_magnetActionMessage`.

### `message_builder.py` — Построение сообщений

Функция `generate_completion_messages()`:

- Конвертирует `AgentConversationMessage[]` → `ChatCompletionMessageParam[]`
- Обрабатывает все типы шагов: classification, topic_completion, topic_action_call
- Параметр `max_messages` для обрезки контекста

Функция `create_tool_calls_from_topic_completion_step()`:

- Конвертирует action requests из шага → `ChatCompletionMessageToolCallParam[]`

### `memory.py` — Стратегии памяти

Протокол `MemoryStrategy` и реализация `LastNMessagesStrategy`:

```python
class MemoryStrategy(Protocol):
    def select_messages(self, messages: list[AgentConversationMessage]) -> list[AgentConversationMessage]: ...

class LastNMessagesStrategy:
    def __init__(self, n: int = 10): ...
```

По умолчанию `n=10` (`DEFAULT_LAST_N_MESSAGES`). Стратегия подключается в `execute_topic()`.

### `exceptions.py` — Иерархия исключений

```
AgentError (base)
├── AgentNotFoundError         — агент не найден
├── AgentConfigurationError    — невалидная конфигурация
├── ClassificationError        — ошибка классификации
├── ActionExecutionError       — ошибка выполнения action
├── AgentLoopExhaustedError    — цикл исчерпан без результата
└── AgentTimeoutError          — таймаут выполнения topic
```

### `models.py` — Модели данных

Ключевые модели:

| Модель                             | Назначение                                        |
|------------------------------------|---------------------------------------------------|
| `Agent`                            | Конфигурация агента (multi-variant entity)        |
| `AgentTopic`                       | Topic с описанием и списком actions                |
| `AgentAction`                      | Описание action (тип, tool, function name и т.д.) |
| `ConversationIntent`               | Enum: greeting, farewell, topic, off_topic, ...   |
| `AgentConversationClassification`  | Результат классификации (intent + topic + reason) |
| `AgentConversationRun`             | Набор шагов (steps) одного прогона агента         |
| `AgentConversationRunStep*`        | Типизированные шаги: Classification, TopicCompletion, ActionCall |
| `AgentConversationExecuteTopicResult` | Результат execute_topic                        |
| `AgentVariantValue`                | Вариант конфигурации: topics + prompt_templates   |
| `AgentSettings`                    | Настройки: welcome_message, sample_questions, ...  |

### `actions/execute.py` — Роутер Actions

Маппинг `AgentActionType` → функция-исполнитель:

```python
# Простые actions (tool_system_name + arguments)
EXECUTE_AGENT_ACTION_FUNCTION_MAP = {
    RAG:             action_execute_rag,
    RETRIEVAL:       action_execute_retrieval,
    PROMPT_TEMPLATE: action_execute_prompt_template,
}

# Actions с провайдером (tool_provider + tool_system_name + arguments)
EXECUTE_AGENT_PROVIDED_ACTION_FUNCTION_MAP = {
    MCP_TOOL:        action_execute_mcp_tool,
    API:             action_execute_api_tool,
    KNOWLEDGE_GRAPH: action_execute_knowledge_graph,
}
```

---

## Конфигурация через переменные окружения

| Переменная                         | По умолч. | Описание                                |
|------------------------------------|-----------|-----------------------------------------|
| `AGENT_TOPIC_TIMEOUT_SECONDS`      | `120`     | Таймаут на весь цикл execute_topic      |
| `AGENT_ACTION_TIMEOUT_SECONDS`     | `30`      | Таймаут на одно выполнение action       |
| `ACTION_MESSAGE_DEFAULT_LLM_DESCRIPTION` | (встроен.) | LLM-инструкция для `_magnetActionMessage` |

---

## Потоки данных

### Основной flow

```
execute_agent()                              [services.py]
  │
  ├─ get_agent_by_system_name()              [services.py]  — загрузка из БД
  │
  ├─ classify_conversation()                 [classification.py]
  │    ├─ execute_prompt_template()           — вызов LLM
  │    ├─ _extract_json_string()              — парсинг ответа
  │    └─ AgentConversationClassification     — результат
  │
  └─ execute_topic()                         [topic_execution.py]
       ├─ LastNMessagesStrategy.select_messages()  [memory.py]
       ├─ generate_completion_messages()            [message_builder.py]
       ├─ create_chat_completion_tools()            [tool_schema.py]
       ├─ create_chat_completion_from_prompt_template()  — вызов LLM
       ├─ create_action_call_requests()             [topic_execution.py]
       └─ execute_agent_action()                    [actions/execute.py]
            └─ action_execute_*()                   [actions/action_execute_*.py]
```

### Confirmation flow

```
execute_agent()                              [services.py]
  │
  └─ create_action_call_steps()              [confirmation.py]
       └─ execute_agent_action()             [actions/execute.py]
```

---

## Принципы

1. **Единственная ответственность** — каждый модуль отвечает за одну задачу
2. **Graceful degradation** — система предпочитает вернуть неполный ответ, а не упасть
3. **Sanitized errors** — внутренние ошибки и трейсы не попадают к пользователю
4. **Явные исключения** — кастомная иерархия вместо `assert` / generic `ValueError`
5. **Pluggable memory** — стратегия контекста заменяема через Protocol
6. **Обратная совместимость** — все публичные символы реэкспортируются из `services.py`

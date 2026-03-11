# ROADMAP: Улучшение системы агентов (Agent / Topics / Actions)

> Дата создания: 10 марта 2026
> Основано на аудите кодовой базы: `api/src/services/agents/`

---

## Текущая архитектура

```
User Message
    │
    ▼
execute_agent()
    │
    ├─ [confirmation flow] → create_action_call_steps() → execute actions
    │
    ├─ [PASS mode] → skip classification, use first topic
    │
    └─ [normal flow] → classify_conversation()
                            │
                            ├─ intent ≠ TOPIC → return assistant_message
                            │
                            └─ intent = TOPIC → select topic
                                                    │
                                                    ▼
                                              execute_topic()  (agent loop)
                                                    │
                                              ┌─────┴─────┐
                                              │  iteration │ (max 5, timeout 120s)
                                              │  ┌────────┐│
                                              │  │ LLM    ││
                                              │  │ call   ││
                                              │  └───┬────┘│
                                              │      │     │
                                              │  tool_calls?│
                                              │   ├─ yes → execute_agent_action() (sequential)
                                              │   │         → добавить результат в steps
                                              │   │         → следующая итерация
                                              │   │
                                              │   ├─ assistant_message → return
                                              │   │
                                              │   └─ ничего → retry (следующая итерация)
                                              │            │
                                              └────────────┘
```

**Ключевые файлы:**
- `api/src/services/agents/services.py` (1125 строк) — основная логика
- `api/src/services/agents/models.py` — модели данных
- `api/src/services/agents/actions/execute.py` — маршрутизация выполнения actions
- `api/src/services/agents/actions/action_execute_*.py` — конкретные реализации
- `api/src/services/agents/conversations/services.py` — управление разговорами
- `api/src/services/agents/post_process/utils.py` — пост-обработка
- `api/tests/services/agents/` — тесты

---

## Найденные проблемы и план улучшений

### ФАЗА 1: Критические исправления (надёжность)

#### 1.1 Замена `assert` на корректную обработку ошибок
**Файлы:** `services.py`, `actions/action_execute_*.py`
**Проблема:** По всей production-кодовой базе используются `assert` для валидации. При запуске Python с флагом `-O` (optimized) все assert-ы полностью отключаются, что приведёт к непредсказуемому поведению.
**Примеры:**
```python
# services.py
assert agent_config, "Agent not found"
assert topic, "Topic is not defined"

# action_execute_rag.py 
assert query, "Cannot call RAG Tool - user's query is missing"
```
**Решение:** Заменить все `assert` на `if not ...: raise ValueError(...)` или кастомные исключения.
**Приоритет:** 🔴 Высокий

#### 1.2 Баг с shadowing переменной в `classify_conversation()`
**Файл:** `services.py`, строки ~607-618
**Проблема:** Переменная цикла `topics` перекрывает параметр функции `topics`:
```python
topic_definitions = [
    {
        "system_name": topics.system_name,  # ← здесь topics = элемент из цикла
        "name": topics.name,
        "description": topics.description,
    }
    for topics in topics  # ← shadow: topics (loop var) перекрывает topics (parameter)
]
```
**Решение:** Переименовать переменную цикла в `topic`:
```python
for topic in topics
```
**Приоритет:** 🔴 Высокий

#### 1.3 Graceful degradation при исчерпании итераций в `execute_topic()`
**Файл:** `services.py`, строка ~549
**Проблема:** При достижении лимита итераций бросается `ValueError("Max iteration count reached")`, что приводит к 500-ой ошибке для пользователя. Нет graceful fallback.
**Решение:**
- Вернуть пользователю корректный ответ с извинением вместо crash-а
- Добавить structured logging для анализа причин исчерпания итераций
- Сохранить собранные steps для post-mortem анализа
**Приоритет:** 🔴 Высокий

#### 1.4 Таймауты и ошибки при выполнении actions
**Файл:** `services.py` (execute_topic loop), `actions/execute.py`
**Проблема:**
- Нет таймаута на выполнение отдельной action (только общий 120s на весь цикл)
- Если одна action зависла — блокируется весь цикл
- Ошибки action-ов возвращаются как текст LLM — включая внутренние детали (f"Error executing tool: {e}")
**Решение:**
- Добавить per-action timeout (настраиваемый, напр. 30s)
- Santize error messages — не показывать внутренние стектрейсы пользователю
- Добавить retry policy для transient errors (network timeouts, 5xx)
**Приоритет:** 🔴 Высокий

---

### ФАЗА 2: Улучшение классификации (качество)

> **Примечание:** json_schema уже используется через prompt templates. Проблема в том, что некоторые модели hallucinate и возвращают невалидный JSON несмотря на schema.

#### 2.1 Повышение устойчивости к невалидному JSON от LLM
**Файл:** `services.py`, `classify_conversation()` и `_extract_json_string()`
**Проблема:**
- Некоторые модели hallucinate и возвращают невалидный JSON даже при наличии json_schema
- Всего 2 попытки retry, но без изменения prompt-а (та же ошибка повторяется)
- При фейле — fallback на `REQUEST_NOT_CLEAR`, пользователь получает невнятный ответ
**Решение:**
- При retry — добавлять ошибку парсинга и ожидаемую schema в контекст для LLM, чтобы он корректировал формат
- Улучшить `_extract_json_string()` — добавить обработку типичных hallucination-паттернов (trailing comma, unescaped quotes, comments внутри JSON)
- Увеличить количество retry до 3 и добавить exponential backoff
- Добавить метрику частоты невалидных JSON-ов per model для мониторинга
**Приоритет:** 🟡 Средний

#### 2.2 Добавить confidence score к классификации
**Файл:** `models.py` — `AgentConversationClassification`
**Проблема:** Классификация бинарная — либо topic определён, либо нет. Нет порога уверенности.
**Решение:**
- Добавить поле `confidence: float` в `AgentConversationClassification`
- Если confidence < threshold — запросить уточнение у пользователя вместо ошибки
- Логировать confidence для мониторинга качества классификации
**Приоритет:** 🟡 Средний

#### 2.3 Поддержка переключения между топиками
**Проблема:** В текущей реализации классификация определяет один топик на сообщение. Если пользователь в середине разговора переключает тему, контекст предыдущего топика теряется. Agent loop не умеет работать с несколькими топиками одновременно.
**Решение:**
- Добавить механизм обнаружения смены топика в agent loop
- Сохранять контекст предыдущих топиков для возможности возврата
- Добавить intent `TOPIC_SWITCH` в `ConversationIntent`
**Приоритет:** 🟡 Средний

---

### ФАЗА 3: Память и управление контекстом

#### 3.1 Система управления памятью агента (Memory Management)
**Файл:** `services.py`, `generate_completion_messages()`, новый модуль `memory/`
**Проблема:** Функция `generate_completion_messages()` конвертирует ВСЕ сообщения в completion messages без ограничений. При длинных разговорах можно превысить контекстное окно модели, а лишние сообщения ухудшают качество ответов и увеличивают стоимость.

**Решение — архитектура со стратегиями:**

Создать абстракцию `MemoryStrategy` с подключаемыми стратегиями:

```python
class MemoryStrategy(Protocol):
    def select_messages(
        self,
        messages: list[AgentConversationMessage],
    ) -> list[AgentConversationMessage]: ...
```

**Стратегия 1 (реализовать сейчас): `LastNMessages`**
- Использовать последние N сообщений для контекста
- **По умолчанию: N = 10**
- Настраиваемый параметр в `AgentSettings`
- Всегда включать system prompt + текущее сообщение пользователя

```python
class LastNMessagesStrategy:
    def __init__(self, n: int = 10):
        self.n = n
    
    def select_messages(self, messages):
        return messages[-self.n:] if len(messages) > self.n else messages
```

**Стратегии на будущее (не реализовывать сейчас):**
- `SummaryStrategy` — сжатие старых сообщений в summary через LLM, последние K сообщений сохраняются полностью
- `RelevantInfoStrategy` — выбор релевантных сообщений по векторному поиску или ключевым словам
- `HybridStrategy` — комбинация: summary + relevant + last N

**Интеграция:**
- Добавить `memory_strategy` и `memory_last_n_messages` в `AgentSettings`
- Применять стратегию в `generate_completion_messages()` перед формированием массива completion messages
- По умолчанию: `LastNMessages(n=10)`

**Приоритет:** 🟡 Средний

---

### ФАЗА 4: Рефакторинг и качество кода

#### 4.1 Разбиение `services.py` (1125 строк)
**Проблема:** Один файл содержит всю бизнес-логику: классификацию, agent loop, tool schema generation, completion message generation, API/MCP server loading, etc.
**Решение:** Выделить в отдельные модули:
```
services/agents/
├── classification.py       # classify_conversation, _extract_json_string
├── topic_execution.py      # execute_topic, execute_agent_action loop
├── tool_schema.py          # create_chat_completion_tools, create_chat_completion_tool_parameters
├── message_builder.py      # generate_completion_messages, create_tool_calls_from_topic_completion_step  
├── confirmation.py         # create_action_call_steps, confirmation flow
└── services.py             # execute_agent (orchestrator), get_agent_by_system_name
```
**Приоритет:** 🟡 Средний

#### 4.2 Создание кастомных исключений
**Проблема:** Используются generic `ValueError`, `LookupError`, `AssertionError` повсюду. Сложно различить типы ошибок в обработчиках.
**Решение:**
```python
class AgentNotFoundError(Exception): ...
class ClassificationError(Exception): ...
class ActionExecutionError(Exception): ...
class AgentLoopExhaustedError(Exception): ...
class AgentTimeoutError(Exception): ...
```
**Приоритет:** 🟡 Средний

#### 4.3 Исправить f-string logging
**Проблема:** Используется `logger.info(f"Agent config: {agent_config}")` — f-string вычисляется всегда, даже если log level выше чем INFO.
**Решение:** Использовать lazy formatting: `logger.info("Agent config: %s", agent_config)`
**Приоритет:** 🟢 Низкий

---

### Следующий этап (Backlog)

Следующие задачи запланированы, но будут реализованы после завершения фаз 1-4:

#### Расширение тестового покрытия
- Тесты для action executors (`action_execute_api_tool.py`, `action_execute_mcp_tool.py`, `action_execute_knowledge_graph.py`)
- Integration-тесты для полного цикла агента (замоканный LLM, реальная orchestration логика)
- Тесты на edge cases классификации (невалидный JSON, несуществующий topic, timeout)

#### Новые возможности
- **Streaming-ответы** — SSE/WebSocket streaming для agent loop
- **Настраиваемые параметры agent loop** — `max_iterations`, `timeout_seconds` per agent
- **Agent-to-agent handoff** — передача управления между агентами
- **Параллельное выполнение actions** — `asyncio.gather()` для одновременных tool calls
- **Кеширование tool schemas** — TTL-кеш для API/MCP server configs
- **Мониторинг и метрики** — Prometheus/OpenTelemetry metrics, dashboard, алерты
- **Дополнительные стратегии памяти** — `SummaryStrategy`, `RelevantInfoStrategy`, `HybridStrategy`

---

## Порядок выполнения

```
ФАЗА 1 (Критические)       ████████████ 
  1.1 Замена assert          ██████
  1.2 Баг shadowing          ██
  1.3 Graceful degradation   ████
  1.4 Action timeouts        ████████

ФАЗА 2 (Классификация)             ████████████
  2.1 JSON hallucination fix         ████████
  2.2 Confidence score               ████
  2.3 Topic switching                    ████████

ФАЗА 3 (Память)                           ████████
  3.1 Memory strategy arch.               ████
      LastNMessages (N=10)                ████

ФАЗА 4 (Рефакторинг)                         ████████
  4.1 Split services.py                       ████████
  4.2 Custom exceptions                       ████
  4.3 f-string logging                        ██

─── Backlog (следующий этап) ────────────────────
  Тесты, Streaming, Agent handoff, 
  Parallel actions, Мониторинг, и т.д.
```

---

## Быстрые победы (Quick Wins)

Задачи, которые можно решить за 1-2 дня и которые сразу повысят надёжность:

1. **Баг shadowing переменной** (1.2) — 10 минут, одна строка
2. **Замена assert на if/raise** (1.1) — 2-3 часа, механическая работа
3. **Graceful fallback при max iterations** (1.3) — 1 час
4. **Sanitize error messages** (часть 1.4) — 1 час
5. **f-string → lazy logging** (4.3) — 30 минут

---

## Резюме

Текущая реализация агентов функциональна и имеет хорошую основу (observability, разделение на actions, модели данных). Основные риски:
- **Надёжность**: `assert` в production, отсутствие graceful degradation, утечка деталей ошибок
- **Качество классификации**: hallucination некоторых моделей при генерации JSON, нет confidence scoring
- **Управление контекстом**: нет ограничения на количество сообщений, нет стратегий памяти
- **Maintainability**: монолитный services.py, generic exceptions

Фазы 1-4 составляют текущий этап работы. Остальные задачи вынесены в backlog.

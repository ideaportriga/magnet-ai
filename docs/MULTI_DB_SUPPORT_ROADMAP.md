# Multi-Database Support Roadmap

## Цель

Обеспечить возможность работы основной БД на PostgreSQL, Oracle и MSSQL без регрессии существующего функционала.

## Текущее состояние

Кодовая база **тесно связана с PostgreSQL**. Найдено ~29 отдельных raw SQL запросов в 6 сервисных файлах + 2 filter compiler-а, которые используют PG-specific синтаксис.

### Классификация PG-зависимостей

**Тип A** — простой доступ к JSON полям. SQLAlchemy поддерживает "из коробки":
```python
Model.column['key'].astext           # PG: ->>'key'   Oracle: JSON_VALUE(col,'$.key')
Model.column['a']['b'].astext        # PG: ->'a'->>'b' Oracle: JSON_VALUE(col,'$.a.b')
Model.column['key'].as_boolean()     # PG: (->>'key')::boolean
Model.column['key'].as_float()       # PG: (->>'key')::float
Model.column['key'].as_integer()     # PG: (->>'key')::int
```
Также: `#>>` (nested path) заменяется на chained `['a']['b'].astext`.

**Тип B — Application layer** — сложные JSONB операции, которые проще перенести в Python:
- `jsonb_build_object()` + `||` (JSONB merge) → загрузить объект, изменить в Python, сохранить
- `jsonb_set()` с `WITH ORDINALITY` → аналогично
- `COALESCE(col, '{}'::jsonb) || CAST(:data AS jsonb)` → аналогично

**Тип B — Custom compilers** — сложные операции, требующие `@compiles` для каждого диалекта:
- `jsonb_array_elements_text()` → `OPENJSON()` (MSSQL) / `JSON_TABLE()` (Oracle)
- `column ? 'key'` (key exists) → `JSON_EXISTS()` / `JSON_VALUE() IS NOT NULL`
- `@>` (containment) → varies
- `ILIKE` → `func.lower().like(func.lower())`

### Карта зависимостей по файлам

| Файл | ORM-таблица | Тип A | Тип B (app layer) | Тип B (compilers) |
|------|-------------|-------|--------------------|--------------------|
| `agents/whatsapp/services.py` | `agents` | 1 запрос | — | — |
| `agents/slack/runtime.py` | `agents` | 1 запрос | — | — |
| `agents/teams/services.py` | `agents` | 1 запрос | — | — |
| `core/domain/traces/service.py` | `traces` | 1 запрос | — | — |
| `core/domain/jobs/service.py` | `jobs` | 1 запрос | — | — |
| `scheduler/job_executor.py` | `jobs` | 1 запрос | — | — |
| `observability/services.py` | `metrics` | ~18 запросов | — | 2 (`jsonb_array_elements_text`) |
| `telemetry/services.py` | `metrics` | — | 2 (`jsonb_build_object`, `\|\|`) | — |
| `evaluation/services.py` | `evaluations` | — | 3 (`jsonb_set`, `\|\|`, `jsonb_array_elements`) | 1 (CTE + `jsonb_array_elements`) |
| `utils/filter_compiler.py` | (dynamic) | — | — | all (`ILIKE`, `@>`, `jsonb_array_elements_text`) |
| `kg/entity_filter_compiler.py` | (dynamic) | — | — | all (`::text`, `ILIKE`, EXISTS) |
| KG document service | (dynamic) | — | 5 (`CAST AS jsonb`, `\|\|`, `RETURNING`) | — |
| KG entity service | (dynamic) | — | — | 2 (`?`, `-` operators) |

---

## Принципы миграции

1. **Сначала Тип A** — 70% работы, нулевые зависимости, SQLAlchemy генерирует тот же SQL для PostgreSQL
2. **По одному функциональному блоку за PR** — каждая фаза = один PR с изолированным regression scope
3. **Тип B (app layer)** — переносим вычисления в Python; проще, надёжнее, тестируемее
4. **Тип B (compilers) — последними** — требуют инфраструктуры (`json_ops.py`), сложнее тестировать

---

## Part 1: Тип A — SQLAlchemy ORM замена (нет зависимостей, низкий риск)

> Все фазы Part 1 независимы друг от друга и могут выполняться параллельно.
> Каждая — прямая замена `text()` на SQLAlchemy column expressions.
> SQLAlchemy генерирует **идентичный** SQL для PostgreSQL, поэтому поведение не меняется.

### Phase 1: Agent channel queries (3 файла, 3 запроса) ✅ DONE

**Effort**: XS×3 | **Риск**: Минимальный

#### 1.1 `services/agents/whatsapp/services.py` (lines 19-29)

| Было (PG-only) | Станет (кросс-диалектно) |
|----------------|--------------------------|
| `a.channels #>> '{whatsapp,token}'` | `Agent.channels['whatsapp']['token'].astext` |
| `a.channels -> 'whatsapp' ->> 'phone_number_id'` | `Agent.channels['whatsapp']['phone_number_id'].astext` |
| `(a.channels -> 'whatsapp' -> 'enabled')::boolean` | `Agent.channels['whatsapp']['enabled'].as_boolean()` |

**Regression scope**: WhatsApp webhook handler

#### 1.2 `services/agents/slack/runtime.py` (lines 122-135)

Аналогичная замена для 7 полей Slack credentials (`client_id`, `client_secret`, `signing_secret`, `token`, `scopes`) + `enabled` boolean check.

**Regression scope**: Slack bot discovery при startup

#### 1.3 `services/agents/teams/services.py` (lines 19-29)

Аналогичная замена для MS Teams (`tenant_id`, `secret_value`, `client_id`, `enabled`).

**Regression scope**: Teams webhook handler

---

### Phase 2: Jobs & Traces JSONB filtering (3 файла, 3 запроса) ✅ DONE

**Effort**: S+S+XS | **Риск**: Средний (jobs service имеет SQL injection risk — фиксим заодно)

#### 2.1 `core/domain/traces/service.py` (lines 25-47)

Custom `JsonbPathFilter` генерирует raw SQL: `extra_data->'params'->>'system_name' = :value`

| Было | Станет |
|------|--------|
| `extra_data->'params'->>'system_name'` | `Trace.extra_data['params']['system_name'].astext` |
| `extra_data->>'{key}'` | `Trace.extra_data[key].astext` |

**Regression scope**: Trace listing / filtering в admin UI

#### 2.2 `core/domain/jobs/service.py` (lines 39-95)

String concatenation для JSONB filtering — **SQL injection risk** в текущем коде.

| Было | Станет |
|------|--------|
| `f"definition->'run_configuration'->>'type' = '{value}'"` | `Job.definition['run_configuration']['type'].astext == value` |
| `f"definition->>'{json_key}' = '{value}'"` | `Job.definition[json_key].astext == value` |
| Raw `SELECT * FROM jobs WHERE ...` | `select(Job).where(...)` |

**Regression scope**: Job listing, duplicate system job check

#### 2.3 `scheduler/job_executor.py` (lines 45-52)

| Было | Станет |
|------|--------|
| `text("...definition->'run_configuration'->>'type' = :type...")` | `Job.definition['run_configuration']['type'].astext == run_config_type` |
| `definition->'run_configuration'->'params'->>'is_system'` | `Job.definition['run_configuration']['params']['is_system'].astext == 'true'` |

**Regression scope**: Scheduler job creation

---

### Phase 3: Observability — options и simple breakdowns (1 файл, ~18 запросов) ✅ DONE

**Effort**: M | **Риск**: Средний — большой файл, но запросы шаблонные

`services/observability/services.py` — самый большой файл с raw SQL. ~18 запросов из ~20 используют только `->>` и `->`, что покрывается SQLAlchemy.

#### 3.1 Options queries (lines 204-375) — 10 запросов

Все однотипные: `SELECT DISTINCT column->>'field' FROM metrics WHERE ... ORDER BY ...`

```python
# Шаблон замены (один для всех 10):
field_expr = Metric.extra_data['topic'].astext  # или conversation_data, x_attributes
stmt = (
    select(field_expr.distinct().label('value'))
    .where(Metric.feature_type == feature_type)
    .where(Metric.status == 'success')
    .where(field_expr.is_not(None))
    .order_by('value')
)
```

Запросы:
- RAG: topics, languages, consumer_names, organizations (`x_attributes->>'org-id'`)
- LLM: consumer_names, organizations
- Agent: tools, consumer_names, languages

**Regression scope**: Filter dropdowns в analytics dashboard

#### 3.2 Simple aggregation queries (lines 399-500) — 6 запросов

GROUP BY на JSONB полях: `extra_data->>'topic'`, `extra_data->'answer_feedback'->>'type'`, etc.

```python
topic_expr = Metric.extra_data['topic'].astext
stmt = (
    select(topic_expr.label('topic'), func.count().label('count'))
    .where(...)
    .group_by(topic_expr)
)
```

**Regression scope**: Breakdown charts (topics, languages, feedback, resolution)

#### 3.3 Count & pagination queries (lines 939-980) — 2 запроса

Простые `COUNT(*)` + `SELECT ... LIMIT/OFFSET`.

```python
# Count:
stmt = select(func.count()).select_from(Metric).where(...)
# Paginated list:
stmt = select(Metric).where(...).order_by(...).limit(limit).offset(offset)
```

**Regression scope**: Metrics table pagination

#### 3.4 Get by ID (lines 1177-1202) — 1 запрос

```python
stmt = select(Metric).where(Metric.id == analytics_id)
```

**Regression scope**: Analytics detail view

---

### Phase 4: Observability — complex aggregations with type casts (1 файл, ~5 запросов) ✅ DONE

**Effort**: L | **Риск**: Средний

Эти запросы используют `(column->>'field')::float` и `(column->>'field')::int`, что SQLAlchemy поддерживает через `.as_float()` / `.as_integer()`.

#### 4.1 General metrics summaries (lines 399-408, 537-547)

```python
stmt = select(
    func.count().label('count'),
    func.avg(Metric.latency).label('avg_latency'),
    func.sum(Metric.cost).label('total_cost'),
    func.count(Metric.user_id.distinct()).label('unique_user_count'),
)
```

**Regression scope**: Summary cards на dashboard

#### 4.2 Agent metrics with JSONB casts (lines 582-599)

Самый сложный запрос Part 1: 15 columns с `.as_float()`, `.as_integer()`, `case()`.

```python
stmt = select(
    func.count().label('count'),
    func.avg(Metric.latency).label('avg_duration'),
    func.avg(Metric.conversation_data['avg_tool_call_latency'].as_float()).label('avg_tool_call_latency'),
    func.sum(Metric.conversation_data['likes'].as_integer()).label('total_likes'),
    func.sum(Metric.conversation_data['dislikes'].as_integer()).label('total_dislikes'),
    func.avg(Metric.conversation_data['messages_count'].as_float()).label('avg_messages_count'),
    func.sum(case(
        (Metric.conversation_data['resolution_status'].astext == 'resolved', 1),
        else_=0,
    )).label('total_status_resolved'),
    func.sum(case(
        (Metric.extra_data['answer_copy'].as_boolean().is_(True), 1),
        else_=0,
    )).label('copy_count'),
).where(...)
```

**Regression scope**: Agent analytics dashboard

#### 4.3 Top metrics queries (lines 750-871) — 3 запроса

GROUP BY с множественными агрегатами (аналогично 4.2, но с GROUP BY).

**Regression scope**: Top agents/RAG/LLM tables

---

### Итого Part 1

| Phase | Файлы | Запросов | Effort | Риск |
|-------|-------|----------|--------|------|
| 1 | 3 (agent channels) | 3 | XS×3 | Минимальный | ✅ DONE |
| 2 | 3 (jobs, traces, scheduler) | 3 | S+S+XS | Средний | ✅ DONE |
| 3 | 1 (observability simple) | ~19 | M | Средний | ✅ DONE |
| 4 | 1 (observability casts) | ~5 | L | Средний | ✅ DONE |
| **Итого Part 1** | **8 файлов** | **~30 запросов** | | | **✅ ALL DONE** |

**Part 1 завершена.** ~70% кодовой базы работает кросс-диалектно. Agent integrations, job management, trace filtering, основной analytics dashboard — всё на SQLAlchemy ORM.

---

## Part 2: Тип B — Application layer (нет зависимостей, средний риск)

> Переносим вычисления из SQL в Python. Загружаем JSON-объект, модифицируем, сохраняем.
> Не нужна инфраструктура (`json_ops.py`) — просто Python код.

### Phase 5: Telemetry — JSONB merge (1 файл, 2 запроса) ✅ DONE

**Effort**: S | **Риск**: Низкий

`services/telemetry/services.py` — 2 UPDATE с `jsonb_build_object` + `||`:

```sql
-- Текущий (PG-only):
UPDATE metrics SET extra_data = COALESCE(extra_data, '{}'::jsonb) ||
    jsonb_build_object('answer_feedback', CAST(:feedback AS jsonb))
WHERE id = :analytics_id
```

```python
# Целевой (кросс-диалектный):
metric = await session.get(Metric, analytics_id)
if metric:
    extra = dict(metric.extra_data or {})
    extra['answer_feedback'] = feedback
    metric.extra_data = extra
    flag_modified(metric, 'extra_data')
```

**Regression scope**: Feedback и copy tracking в analytics

---

### Phase 6: Evaluation service (1 файл, 4 запроса)

**Effort**: M | **Риск**: Высокий — самый PG-специфичный код в проекте

#### 6.1 List evaluations with aggregations (lines 18-119)

CTE с 7 subqueries, каждый использует `jsonb_array_elements()` для подсчёта avg latency, score, tokens.

```python
# Целевой: загрузить evaluations через ORM, агрегировать в Python
evaluations = await evaluation_service.list_and_count(...)
for eval_obj in evaluations:
    results = eval_obj.results or []
    valid = [r for r in results if isinstance(r, dict)]
    eval_obj.records_count = len(valid)
    eval_obj.average_latency = _safe_avg(r.get('latency') for r in valid)
    eval_obj.average_score = _safe_avg(r.get('score') for r in valid)
    # ... etc
```

**Regression scope**: Evaluation list page

#### 6.2 Update score in JSONB array (lines 158-192) ✅ DONE

`jsonb_set()` с `array_append(array(SELECT ordinality FROM jsonb_array_elements WITH ORDINALITY))` — **самый сложный PG-специфичный запрос** в кодовой базе.

```python
# Целевой: load-modify-save
evaluation = await session.get(Evaluation, UUID(evaluation_id))
results = list(evaluation.results or [])
for r in results:
    if r.get('id') == result_id:
        r['score'] = score
        r['score_comment'] = score_comment
        break
evaluation.results = results
flag_modified(evaluation, 'results')
```

**Regression scope**: Evaluation score update API

#### 6.3 Verify score update (lines 208-217) ✅ DONE (merged into 6.2)

Проверка встроена в `update_evaluation_score()` — функция возвращает `True/False` на основании Python-логики (найден ли result_id в массиве).

**Regression scope**: Score update verification

#### 6.4 Append results (lines 239-256) ✅ DONE

`COALESCE(results, '[]'::jsonb) || CAST(:new_results AS jsonb)`

```python
# Целевой:
evaluation = await session.get(Evaluation, UUID(evaluation_id))
evaluation.results = (evaluation.results or []) + new_results
if errors:
    evaluation.errors = errors
flag_modified(evaluation, 'results')
```

**Regression scope**: Evaluation result recording

---

### Phase 7: KG document JSONB merge (1 файл, ~5 запросов)

**Effort**: L | **Риск**: Средний

`core/domain/knowledge_graph/services/knowledge_graph_document_service.py` — INSERT и UPDATE с:
- `COALESCE(metadata, '{}'::jsonb) || CAST(:metadata_json AS jsonb)`
- `RETURNING id::text`
- `CAST(:toc_json AS jsonb)`

```python
# Целевой: использовать кешированные Table objects + SQLAlchemy Core insert/update
docs_tbl = get_cached_docs_table(docs_table_name(graph_id))

# INSERT:
stmt = docs_tbl.insert().values(
    name=name, type=doc_type, status='pending',
    metadata=json.loads(metadata_json) if metadata_json else {},
    toc=json.loads(toc_json) if toc_json else None,
    ...
).returning(docs_tbl.c.id)

# UPDATE metadata merge (application layer):
row = (await session.execute(select(docs_tbl.c.metadata).where(docs_tbl.c.id == doc_id))).scalar_one()
merged = {**(row or {}), **new_metadata}
await session.execute(docs_tbl.update().where(docs_tbl.c.id == doc_id).values(metadata=merged))
```

**Regression scope**: KG document CRUD (create, update metadata, upsert)

---

### Итого Part 2

| Phase | Файлы | Запросов | Effort | Риск |
|-------|-------|----------|--------|------|
| 5 | 1 (telemetry) | 2 | S | Низкий | ✅ DONE |
| 6 | 1 (evaluation) | 4 | M | Высокий | 6.2 ✅, 6.3 ✅, 6.4 ✅, 6.1 pending |
| 7 | 1 (KG documents) | ~5 | L | Средний | pending |
| **Итого Part 2** | **3 файла** | **~11 запросов** | | | **~75% done** |

**Part 2 статус**: Telemetry — done. Evaluation — 3 из 4 done (осталась 6.1 list с CTE). KG documents — pending.

---

## Part 3: Тип B — Custom compilers (требует инфраструктуры)

> Эти задачи требуют создания `json_ops.py` с `@compiles` декораторами.
> Phase 0 — prerequisite для всех остальных фаз Part 3.

### Phase 0: Инфраструктура — `core/db/json_ops.py`

**Effort**: M | **Риск**: Низкий (новый код, ничего не меняет)

Custom SQLAlchemy functions с реализацией для каждого диалекта:

| Функция | PostgreSQL | Oracle | MSSQL |
|---------|-----------|--------|-------|
| `json_array_elements_text(col)` | `jsonb_array_elements_text(col)` | `JSON_TABLE(col, '$[*]' COLUMNS(...))` | `OPENJSON(col)` |
| `json_key_exists(col, key)` | `col ? key` | `JSON_EXISTS(col, '$.key')` | `JSON_VALUE(col, '$.key') IS NOT NULL` |
| `json_remove_key(col, key)` | `col - key` | `JSON_TRANSFORM(col, REMOVE '$.key')` | custom |

---

### Phase 8: Observability — topics from JSONB array (1 файл, 2 запроса) ✅ DONE

**Выполнено в рамках Phase 3+4** — `jsonb_array_elements_text()` заменён на application-level (Python set/defaultdict).

**Effort**: M | **Риск**: Средний | **Зависит от**: ~~Phase 0~~ (не потребовался — решено через app layer)

`services/observability/services.py` (lines 313-317, 666-673):
```sql
SELECT DISTINCT jsonb_array_elements_text(conversation_data->'topics') as topic FROM metrics
```

**Два варианта решения:**

**Вариант A — Custom compiler** (если нужна SQL-level performance):
```python
from core.db.json_ops import json_array_elements_text
stmt = select(json_array_elements_text(Metric.conversation_data['topics']).label('topic').distinct())
```

**Вариант B — Application layer** (проще, рекомендуемый):
```python
rows = await session.execute(
    select(Metric.conversation_data['topics'])
    .where(Metric.conversation_data['topics'].is_not(None))
    .where(...)
)
topics = set()
for (topics_json,) in rows:
    if isinstance(topics_json, list):
        topics.update(topics_json)
```

**Regression scope**: Topics filter dropdown + topic breakdown chart

---

### Phase 9: Filter compilers (2 файла)

**Effort**: L | **Риск**: Высокий | **Зависит от**: Phase 0

#### 9.1 `services/utils/filter_compiler.py`

Генерирует raw SQL WHERE с:
- `jsonb_array_elements_text()` → custom compiler или application layer
- `ILIKE '%' || :param || '%'` → `func.lower(col).like(func.lower(pattern))`
- `@>` (containment) → `col.contains(value)` (SQLAlchemy JSON type)

**Regression scope**: Все KG entity/document фильтрации

#### 9.2 `services/knowledge_graph/entity_filter_compiler.py`

Наследует base + добавляет:
- `::text` casts → `cast(col, String)`
- EXISTS subqueries → `exists(select(...).where(...))`

**Regression scope**: KG entity filtering в admin UI

---

### Phase 10: KG entity pipeline_state operators (1 файл, 2 запроса)

**Effort**: S | **Риск**: Низкий | **Зависит от**: Phase 0

`knowledge_graph_entity_service.py` (lines 284-292):
```sql
UPDATE docs SET pipeline_state = pipeline_state - 'entity_extraction'
WHERE pipeline_state ? 'entity_extraction'
```

```python
# С custom compilers:
from core.db.json_ops import json_remove_key, json_key_exists
stmt = (
    docs_tbl.update()
    .where(json_key_exists(docs_tbl.c.pipeline_state, 'entity_extraction'))
    .values(pipeline_state=json_remove_key(docs_tbl.c.pipeline_state, 'entity_extraction'))
)
```

**Regression scope**: KG entity extraction cleanup

---

### Итого Part 3

| Phase | Файлы | Effort | Риск | Зависимости |
|-------|-------|--------|------|-------------|
| 0 | 1 (новый json_ops.py) | M | Низкий | — | pending |
| 8 | 1 (observability topics) | M | Средний | ~~Phase 0~~ | ✅ DONE (app layer) |
| 9 | 2 (filter compilers) | L | Высокий | Phase 0 | pending |
| 10 | 1 (KG entity ops) | S | Низкий | Phase 0 | pending |
| **Итого Part 3** | **5 файлов** | | | | **1/4 done** |

**После Part 3**: 100% кодовой базы работает кросс-диалектно.

---

## Сводная таблица

```
Part 1: SQLAlchemy ORM (Type A)          Part 2: App Layer (Type B)        Part 3: Custom Compilers (Type B)
─────────────────────────────────         ──────────────────────────        ─────────────────────────────────
Phase 1: Agent channels     [XS×3]       Phase 5: Telemetry     [S]       Phase 0: json_ops.py infra  [M]
Phase 2: Jobs/Traces        [S+S+XS]     Phase 6: Evaluation    [M]       Phase 8: Topics array       [M]
Phase 3: Observability easy [M]          Phase 7: KG doc merge  [L]       Phase 9: Filter compilers   [L]
Phase 4: Observability cast [L]                                           Phase 10: KG entity ops     [S]
```

| Группа | Phases | Запросов | Effort | Покрытие | Зависимости |
|--------|--------|----------|--------|----------|-------------|
| **Part 1** | 1-4 | ~30 | | 70% | Нет | **✅ ALL DONE** |
| **Part 2** | 5-7 | ~11 | | 90% | Нет | 5 ✅, 6.2-6.4 ✅, 6.1+7 pending |
| **Part 3** | 0, 8-10 | ~6 + compilers | | 100% | Phase 0 → 9,10 | 8 ✅, 0+9+10 pending |
| **Итого** | **11 phases** | **~47** | | | | **~80% done** |

### Что работает кросс-диалектно после каждой Part

| После | Функциональность |
|-------|-----------------|
| Part 1 ✅ | Agent integrations (WhatsApp, Slack, Teams), Job management, Trace filtering, Analytics dashboard (options, breakdowns, summaries, pagination, top metrics) |
| Part 2 (75%) | + Telemetry feedback ✅, Evaluation score/append ✅, **pending**: Evaluation list aggregations (6.1), KG document CRUD (7) |
| Part 3 (25%) | Topics from arrays ✅, **pending**: json_ops.py (0), Filter compilers (9), KG entity ops (10) → **полная кросс-диалектность** |

---

*Создано: 2026-03-29*
*Обновлено: 2026-03-29 — v2: перегруппированы фазы (Type A first)*
*Обновлено: 2026-03-29 — v3: отмечен прогресс (~80% выполнено)*
*Статус: In Progress*

### Оставшиеся задачи

| Phase | Задача | Effort | Блокер |
|-------|--------|--------|--------|
| 6.1 | Evaluation list with CTE aggregations → app layer | M | — |
| 7 | KG document JSONB merge → SQLAlchemy Core | L | — |
| 0 | `json_ops.py` custom compilers infra | M | — |
| 9 | Filter compilers refactor | L | Phase 0 |
| 10 | KG entity pipeline_state operators | S | Phase 0 |

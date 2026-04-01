# Database Optimization Roadmap

## Архитектурный обзор (as-is)

### Основная БД (PostgreSQL via SQLAlchemy + advanced-alchemy)
- **Async engine**: `create_async_engine()` с драйвером `asyncpg`
- **Session management**: Litestar `SQLAlchemyAsyncConfig` с `before_send_handler="autocommit"`
- **Pool**: `pool_size=5`, `max_overflow=10`, `pool_timeout=30`, `pool_recycle=300`, `pool_use_lifo=True`
- **Дополнительные sync engines**: APScheduler jobstore (`psycopg2`), OTel span exporter (`psycopg2`), Slack OAuth state store (`psycopg2`)

### Векторная БД (PGVector via asyncpg напрямую)
- **Отдельный connection pool**: `asyncpg.create_pool()` — НЕ через SQLAlchemy
- **Pool**: `min_size=1`, `max_size=10` (по умолчанию), `command_timeout=60`
- **Поддержка других бэкендов**: Qdrant, Cosmos DB, MongoDB, Oracle (через factory `get_db_client()`)

### Карта engine/pool (5 штук на один PostgreSQL инстанс)

| # | Engine | Драйвер | Pool | Max conn | Используется для | Файл создания |
|---|--------|---------|------|----------|-----------------|---------------|
| 1 | SQLAlchemy AsyncEngine | `asyncpg` | QueuePool | 5+10=15 | ORM, миграции, KG chunk search | `core/config/base.py:210` |
| 2 | PGVector asyncpg pool | `asyncpg` (native) | asyncpg Pool | 10 | RAG collections, vector search | `stores/pgvector_db/client.py:77` |
| 3 | APScheduler sync engine | `psycopg2` | QueuePool | 10+20=30 | Job metadata CRUD | `scheduler/manager.py:234` |
| 4 | OTel span exporter | `psycopg2` | QueuePool | 5+10=15 | Trace/metric export | `observability/otel/exporters/sqlalchemy_sync_span_exporter.py:163` |
| 5 | Slack OAuth state store | `psycopg2` | QueuePool | 5+10=15 | OAuth state | `agents/slack/state_store.py:36` |
| | **TOTAL** | | | **~85** | | |

**PostgreSQL default `max_connections` = 100.** При 85 потенциальных соединениях от одного приложения — место остаётся только на 15 внешних подключений (alembic, psql, мониторинг, pgAdmin).

### Почему это плохо

1. **Connection exhaustion** — каждый pool резервирует connections независимо. PostgreSQL не знает, что это одно приложение. При пиковой нагрузке все ~85 slots могут быть заняты.
2. **Memory overhead** — каждое PostgreSQL соединение потребляет ~5-10 MB RAM на стороне сервера. 85 соединений = ~500-850 MB.
3. **Redundant health checks** — каждый pool независимо делает pre-ping / recycle, увеличивая idle traffic.
4. **Inconsistent lifecycle** — каждый pool создаётся и уничтожается по-своему, что усложняет graceful shutdown.
5. **Дублирование логики** — PGVector делает vector similarity search через raw asyncpg, а `KnowledgeGraphChunkService` делает **то же самое** через SQLAlchemy `db_session.execute()` с оператором `<=>`. Два разных пути к одной БД для одного типа операций.

### Целевая архитектура (to-be)

```
┌─────────────────────────────────────────────┐
│             PostgreSQL Instance              │
│         (основная БД + pgvector)             │
└──────────────┬──────────────────────────────┘
               │
    ┌──────────┴──────────┐
    │                     │
┌───┴────────┐    ┌───────┴──────────┐
│ AsyncEngine│    │ Shared SyncEngine│
│ (asyncpg)  │    │ (psycopg2)       │
│ pool=10+15 │    │ pool=3+5         │
│            │    │                  │
│ ● ORM     │    │ ● APScheduler    │
│ ● KG      │    │ ● OTel exporter  │
│ ● PGVector│    │ ● Slack OAuth    │
│ ● Sessions│    │                  │
└────────────┘    └──────────────────┘

Total: ~33 connections (вместо ~85)
```

**Два engine вместо пяти:**
1. **Один async engine** — для всего async кода (ORM + vector search + KG)
2. **Один shared sync engine** — для компонентов с sync-only API (APScheduler, OTel SDK, Slack SDK)

При подключении **отдельного** vector DB инстанса — добавляется третий engine через `DatabaseConnectionManager`. Но при работе на одном PostgreSQL — это один pool.

### Доказательство: vector search уже работает через SQLAlchemy

`KnowledgeGraphChunkService.search_chunks()` (`knowledge_graph_chunk_service.py:170-258`) уже выполняет pgvector similarity search через основной SQLAlchemy AsyncEngine:

```python
# Работает через db_session (SQLAlchemy AsyncEngine pool):
qvec = bindparam("qvec", type_=chunks_tbl.c.content_embedding.type)
distance_expr = chunks_tbl.c.content_embedding.op("<=>")(qvec)
score_expr = (1 - type_coerce(distance_expr, Float)).label("score")
rows = (await db_session.execute(stmt, {"qvec": query_vector})).mappings().all()
```

А `PgVectorStore` делает то же самое, но через **отдельный** asyncpg pool:

```python
# Работает через self.client (отдельный asyncpg pool):
sql = f"SELECT id, 1 - (embedding <=> $1) as score FROM {table_name} WHERE ... LIMIT $2"
rows = await self.client.execute_query(sql, vector, num_results)
```

Оба пути ведут к одному PostgreSQL. Разница — только в стиле параметров (`$1` vs `:param`) и в том, какой pool используется.

---

## Phase 1: CRITICAL — Исправление багов и устранение рисков (Sprint 1)

### 1.1 [CRITICAL] Race condition в инициализации PGVector pool
**Файл**: `api/src/stores/pgvector_db/client.py:57-60`

```python
async def _ensure_pool_initialized(self) -> None:
    if self.pool is None and not self._initialization_started:
        await self.init_pool()
```

**Проблема**: Нет защиты от concurrent calls. Два concurrent запроса могут оба пройти проверку `self.pool is None` до того, как первый установит `_initialization_started = True`. Результат — двойная инициализация pool или race condition.

**Решение**: Использовать `asyncio.Lock()` для защиты инициализации:
```python
_init_lock: asyncio.Lock = asyncio.Lock()

async def _ensure_pool_initialized(self) -> None:
    if self.pool is not None:
        return
    async with self._init_lock:
        if self.pool is None:
            await self.init_pool()
```

> **Примечание**: Этот fix — временный. При выполнении 2.3 (PGVector через SQLAlchemy) отдельный pool и race condition будут устранены полностью. Но до тех пор — fix необходим.

---

### 1.2 [CRITICAL] SQL Injection через f-string в динамических таблицах
**Файлы**:
- `api/src/services/knowledge_graph/sources/abstract_source.py:183, 612`
- `api/src/core/domain/knowledge_graph/services/knowledge_graph_source_service.py:249-259`
- `api/src/core/domain/knowledge_graph/services/knowledge_graph_document_service.py:683`
- `api/src/services/knowledge_graph/llm_metadata_extraction.py:368-592` (6+ мест)
- `api/src/services/knowledge_graph/sources/sync_pipeline.py:470-478`

**Проблема**: Имена таблиц подставляются через f-string в `text()` SQL. Хотя table names генерируются из graph_id (UUID), это:
- Нарушает принцип defense-in-depth
- Несовместимо с будущей поддержкой Oracle/MSSQL (разный escaping)

**Решение**: Использовать SQLAlchemy Core `Table()` объекты вместо raw SQL с f-string. Для динамических таблиц — валидация имени таблицы через whitelist pattern `^knowledge_graph_[a-f0-9-]+_(documents|chunks|entities|edges)$`.

---

### 1.3 [CRITICAL] Concurrent worker-ы без ограничения на pool exhaustion
**Файл**: `api/src/services/knowledge_graph/sources/sync_pipeline.py:221-232`

**Проблема**: SyncPipeline запускает N listing_workers + N content_fetch_workers + N document_processing_workers через `asyncio.create_task()`. Каждый worker открывает session через `async_session_maker()` (line 468). При дефолтном `pool_size=5 + max_overflow=10` и нескольких concurrent sync pipelines — pool exhaustion неизбежен.

**Решение**:
1. Добавить `asyncio.Semaphore` для ограничения concurrent DB операций в pipeline
2. Передавать session в worker-ы, а не создавать новые внутри

> **Примечание**: Pool_size будет пересчитан в Phase 2 (задача 2.5) после консолидации engine.

---

### 1.4 [CRITICAL] Отсутствие explicit rollback в exception handlers
**Файлы**:
- `api/src/core/domain/knowledge_graph/services/knowledge_graph_document_service.py:680-691`
- `api/src/services/knowledge_graph/llm_metadata_extraction.py:508-514, 622-629`

**Проблема**: В блоках `except` после `commit()` — нет `rollback()`. Если `commit()` выбросил исключение, session остаётся в inconsistent state. Следующая операция на этой session может упасть с `InvalidRequestError: This Session's transaction has been rolled back due to a previous exception`.

**Решение**: Добавить `await db_session.rollback()` в каждый except-блок, или использовать `begin()` context manager:
```python
async with db_session.begin():
    # операции
    # commit происходит автоматически при выходе из блока
```

---

## Phase 2: HIGH — Консолидация engine и session management (Sprint 2-3)

> Задачи этой фазы связаны между собой и выполняются в указанном порядке.

### 2.1 Shared sync engine: 3 sync pools → 1 (Effort: S)

Создать единый sync engine factory. Все 3 sync-компонента будут использовать один pool. Это также поглощает проблему завышенного APScheduler pool (ранее 1.4 в предыдущей версии roadmap — `SCHEDULER_POOL_SIZE=10, MAX_OVERFLOW=20` → теперь shared pool `size=3, overflow=5`).

**Новый файл**: `api/src/core/db/sync_engine.py`
```python
from functools import lru_cache
from sqlalchemy import Engine, create_engine
from core.config.base import get_settings, json_serializer_for_sqlalchemy

@lru_cache(maxsize=1)
def get_shared_sync_engine() -> Engine:
    """Single sync engine shared by APScheduler, OTel exporter, Slack OAuth.

    All three components need synchronous DB access but don't need
    separate connection pools — they all target the same PostgreSQL instance.
    """
    settings = get_settings()
    return create_engine(
        settings.db.sync_url,
        pool_size=3,
        max_overflow=5,
        pool_pre_ping=True,
        pool_recycle=3600,
        json_serializer=json_serializer_for_sqlalchemy,
        echo=False,
    )
```

**Изменения в компонентах**:

1. `scheduler/manager.py` — использовать `get_shared_sync_engine()` вместо создания engine из `engine_options`:
   ```python
   from core.db.sync_engine import get_shared_sync_engine
   scheduler.add_jobstore("sqlalchemy", "default", engine=get_shared_sync_engine())
   ```
   Удалить `SchedulerSettings.get_engine_options()` и связанные env vars (`SCHEDULER_POOL_SIZE`, `SCHEDULER_MAX_POOL_OVERFLOW`, и т.д.).

2. `observability/otel/exporters/sqlalchemy_sync_span_exporter.py:151-173` — заменить `_ensure_initialized()`:
   ```python
   def _ensure_initialized(self):
       if self._initialized:
           return
       from core.db.sync_engine import get_shared_sync_engine
       self._engine = get_shared_sync_engine()
       self._session_factory = sessionmaker(bind=self._engine)
       self._initialized = True
   ```

3. `agents/slack/state_store.py:33-42` — заменить `_get_sync_engine()`:
   ```python
   from core.db.sync_engine import get_shared_sync_engine
   # Удалить _get_sync_engine(), использовать get_shared_sync_engine()
   ```

**Результат**: 3 sync pool → 1 sync pool. Экономия ~52 потенциальных соединений.

---

### 2.2 Стандартизация async session factory (Effort: M)

**Проблема**: В проекте используются два разных способа получения async session:
1. `alchemy.get_session()` — через Litestar plugin (из `core/config/app.py`)
2. `async_session_maker()` — напрямую (из `core/db/session.py`)

Это разные session factories, потенциально с разными настройками. Сейчас это один и тот же engine, но при рефакторинге может разойтись.

**Файлы с `async_session_maker()`**:
- `sync_pipeline.py:468`
- `api_ingest_source.py:215`
- `salesforce_sync.py:208`
- `sharepoint_sync.py:213, 430`
- `confluence_sync.py:303`
- `file_upload_sync.py:99, 168`
- `fluid_topics_sync.py:369, 727`

**Решение**: Стандартизировать на `alchemy.get_session()` для всех случаев, удалить `async_session_maker` из `core/db/session.py`.

> **Важно**: Эта задача — prerequisite для 2.3 (PGVector через SQLAlchemy), т.к. PGVector store тоже должен будет получать sessions единообразно.

---

### 2.3 PGVector через SQLAlchemy AsyncEngine: 2 async pools → 1 (Effort: M-L)

> **Зависимости**: Выполняется после 2.2 (единая session factory).
> **Устраняет**: Issue 1.1 (race condition в PGVector pool) полностью.

Перевести `PgVectorStore` с отдельного asyncpg pool на основной SQLAlchemy AsyncEngine. Два варианта:

**Вариант A (рекомендуемый) — Рефакторинг на SQLAlchemy Core**:

Переписать raw asyncpg запросы PgVectorStore на SQLAlchemy Core, аналогично тому, как работает `KnowledgeGraphChunkService`. Вместо `self.client.execute_query(sql, $1)` — использовать `db_session.execute(stmt, params)`.

Преимущества:
- Один pool для всего async кода
- Dialect-agnostic SQL (совместимость с Oracle/MSSQL в будущем)
- Нет race condition при инициализации pool (полностью устраняет issue 1.1)
- Session management через Litestar DI (consistent lifecycle)

Недостатки:
- Объём рефакторинга (~30 методов в `PgVectorStore`, 1400 строк)
- Нужно перевести `$1, $2` параметры в `:param` стиль
- Нужно зарегистрировать pgvector type в SQLAlchemy engine

Пример миграции одного метода:
```python
# БЫЛО (native asyncpg, отдельный pool):
async def search_documents(self, collection_id, vector, num_results):
    table_name = self._get_documents_table_name(collection_id)
    sql = f"""
        SELECT id::text, content, metadata, 1 - (embedding <=> $1) as score
        FROM {table_name} WHERE embedding IS NOT NULL
        ORDER BY score DESC LIMIT $2
    """
    return await self.client.execute_query(sql, vector, num_results)

# СТАНЕТ (SQLAlchemy Core, общий pool):
async def search_documents(self, db_session: AsyncSession, collection_id, vector, num_results):
    tbl = self._get_table(collection_id)  # cached Table object
    score = (1 - tbl.c.embedding.op("<=>")(bindparam("vec"))).label("score")
    stmt = (
        select(tbl.c.id, tbl.c.content, tbl.c.metadata, score)
        .where(tbl.c.embedding.is_not(None))
        .order_by(score.desc())
        .limit(bindparam("lim"))
    )
    rows = (await db_session.execute(stmt, {"vec": vector, "lim": num_results})).mappings().all()
    return rows
```

**Вариант B (промежуточный) — Raw connection из SQLAlchemy engine**:

Если полный рефакторинг слишком объёмен, можно получить raw asyncpg connection из SQLAlchemy:
```python
async with engine.connect() as conn:
    raw = await conn.get_raw_connection()
    asyncpg_conn = raw.driver_connection  # asyncpg.Connection
    result = await asyncpg_conn.fetch("SELECT ... $1", param)
```

Преимущества:
- Минимальные изменения в существующем SQL
- Использует тот же pool

Недостатки:
- Привязка к asyncpg driver (не совместимо с Oracle/MSSQL)
- Обходит SQLAlchemy session management
- Нужно аккуратно возвращать connection обратно в pool

**Рекомендация**: Вариант A, выполняемый инкрементально (по 3-5 методов за PR).

**После завершения**: удалить `PgVectorClient`, `stores/pgvector_db/client.py`, связанный startup/shutdown код в `plugins/startup.py:167-171` и `plugins/shutdown.py:86-88`.

---

### 2.4 Background tasks — lifecycle management (Effort: M)

**Файлы**:
- `api/src/routes/user/agent_conversations.py:310, 348-356` — `asyncio.create_task()` без session scope
- `api/src/routes/admin/deep_research.py:184` — background workflow
- `api/src/core/domain/note_taker_jobs/controller.py:82-89, 138-149` — background jobs

**Проблема**: Background tasks, запущенные через `asyncio.create_task()`, создают свои session внутри. Request handler может завершиться и вернуть response, пока background task ещё работает с DB. При shutdown приложения — эти tasks могут быть killed без cleanup.

**Решение**:
1. Обеспечить graceful shutdown: отслеживать active background tasks
2. Каждый background task должен открывать session через `async with alchemy.get_session()` (большинство уже делают это)
3. Добавить timeout для background tasks

---

### 2.5 Расчёт оптимального pool_size после консолидации (Effort: S)

> **Зависимости**: Выполняется после 2.1 и 2.3.

**Текущая конфигурация** (5 отдельных pools, ~85 max connections):

| Component | pool_size | max_overflow | Total max |
|-----------|-----------|--------------|-----------|
| Async engine | 5 | 10 | 15 |
| PGVector asyncpg | 1-10 | N/A | 10 |
| APScheduler | 10 | 20 | 30 |
| OTel exporter | default (5) | default (10) | 15 |
| Slack state store | default (5) | default (10) | 15 |
| **TOTAL** | | | **~85** |

**Конфигурация после Phase 2** (2 pools):

| Component | pool_size | max_overflow | Total max |
|-----------|-----------|--------------|-----------|
| Async engine (ORM + PGVector + KG) | 10 | 15 | 25 |
| Shared sync engine (APScheduler + OTel + Slack) | 3 | 5 | 8 |
| **TOTAL** | | | **33** |

**Формула расчёта async pool_size:**
```
pool_size = max_concurrent_requests + background_workers + sync_pipeline_workers
         ≈ 8 (web) + 3 (background) + 4 (pipeline) = 15
max_overflow = pool_size  (для пиков)
```

+ Увеличить PostgreSQL `max_connections` до 150-200 в production (запас для мониторинга, миграций, psql).

---

### 2.6 `before_send_handler="autocommit"` + explicit commit = double commit (Effort: S)

**Файл**: `api/src/core/config/app.py:33`

**Проблема**: Litestar автоматически коммитит session перед отправкой response (`before_send_handler="autocommit"`). Но в route handlers часто вызывается explicit `await db_session.commit()`. Это приводит к двум commit-ам за один request — redundant I/O.

**Решение**: Выбрать одну стратегию:
- **Вариант A**: Убрать explicit commits из route handlers, полагаться на autocommit
- **Вариант B**: Сменить на `before_send_handler=None`, использовать explicit commits

Рекомендация: **Вариант A** для route handlers (autocommit), **explicit commits** только в background tasks и services.

---

### 2.7 Batch commits в LLM metadata extraction (Effort: S)

**Файл**: `api/src/services/knowledge_graph/llm_metadata_extraction.py:545, 665`

**Проблема**: `await db_session.commit()` вызывается внутри цикла `for row in batch`. Каждый commit — это network roundtrip к PostgreSQL. При 1000 документов — 1000 commits.

**Контекст**: Commits сделаны намеренно, чтобы освободить транзакцию перед вызовом LLM (который может занять секунды). Это правильный подход для избежания long-running transactions.

**Решение**: Группировать операции — commit один раз на batch, а не на каждый документ:
```python
for row in batch:
    # prepare data
    pass
# commit once per batch
await db_session.commit()
# then call LLM
```

---

## Phase 3: MEDIUM — Централизация управления и мониторинг (Sprint 3-4)

### 3.1 DatabaseConnectionManager (Effort: M)

> **Зависимости**: Выполняется после Phase 2 (engine уже консолидированы в 2 pool).

Создать единую точку управления всеми engine. Заменяет текущий паттерн, где engine создаются в разных местах (`DatabaseSettings.get_engine()`, `get_shared_sync_engine()`, etc.).

```python
class DatabaseConnectionManager:
    """Centralized connection management for all database engines.

    Principles:
    - Одна основная БД = один async engine (ORM + vector search если та же БД)
    - Один shared sync engine для всех sync-only компонентов
    - Дополнительные engine только для реально отдельных DB инстансов
    """

    def __init__(self, settings: DatabaseSettings):
        self._async_engine: AsyncEngine = self._create_async_engine(settings)
        self._sync_engine: Engine = self._create_sync_engine(settings)
        self._extra_engines: dict[str, AsyncEngine] = {}

    @property
    def async_engine(self) -> AsyncEngine:
        """Main async engine — для ORM и для default vector store (если на той же БД)."""
        return self._async_engine

    @property
    def sync_engine(self) -> Engine:
        """Shared sync engine — APScheduler, OTel, Slack."""
        return self._sync_engine

    def get_or_create_engine(self, name: str, url: str, **kwargs) -> AsyncEngine:
        """Get or create a named async engine for a separate DB instance.

        Used by VectorStoreRegistry when a vector store needs its own connection.
        If `url` matches the main engine — returns the main engine (no duplication).
        """
        if url == str(self._async_engine.url):
            return self._async_engine  # Same DB — reuse main engine
        if name not in self._extra_engines:
            self._extra_engines[name] = create_async_engine(url, **kwargs)
        return self._extra_engines[name]

    def get_pool_status(self) -> dict:
        """Health check for all pools."""
        result = {
            "main_async": self._pool_info(self._async_engine),
            "shared_sync": self._pool_info(self._sync_engine),
        }
        for name, engine in self._extra_engines.items():
            result[f"extra_{name}"] = self._pool_info(engine)
        return result

    async def close_all(self) -> None:
        """Graceful shutdown — close all engines."""
        await self._async_engine.dispose()
        self._sync_engine.dispose()
        for engine in self._extra_engines.values():
            await engine.dispose()
```

**Ключевой метод `get_or_create_engine()`**: если vector store указывает на тот же PostgreSQL — возвращается основной engine (без дополнительного pool). Отдельный engine создаётся только для реально другого инстанса.

---

### 3.2 pool_pre_ping — включить для основного async engine (Effort: XS)

**Файл**: `api/src/core/config/base.py:96-98`

**Текущее**: `POOL_PRE_PING=False`

**Проблема**: При `pool_recycle=300` (5 минут) — соединения могут быть закрыты PostgreSQL (например, по `idle_in_transaction_session_timeout`), но pool этого не узнает. Первый запрос после idle — получит broken connection.

**Решение**: Включить `POOL_PRE_PING=True` для async engine. Для asyncpg это не блокирующая операция (async SELECT 1). Overhead минимален.

---

### 3.3 Мониторинг connection pool (Effort: M)

**Текущее**: Мониторинг есть только для APScheduler pool (`get_scheduler_pool_info()`).

**Решение**: Использовать `DatabaseConnectionManager.get_pool_status()` (из 3.1) для мониторинга всех pools.

Экспортировать в Grafana через endpoint `/admin/health/db` или через metrics:
```python
@get("/admin/health/db")
async def db_health() -> dict:
    return connection_manager.get_pool_status()
```

---

## Phase 4: MEDIUM — Оптимизация запросов (Sprint 4-5)

### 4.1 N+1 в entity hydration
**Файл**: `api/src/core/domain/knowledge_graph/services/knowledge_graph_entity_service.py:396-398`

```python
rows = (await db_session.execute(stmt)).mappings().all()
records = [KnowledgeGraphEntityRecord.from_mapping(row) for row in rows]
await self._hydrate_entity_edges(db_session, graph_id=graph_id, records=records)
```

**Проблема**: `_hydrate_entity_edges` может выполнять отдельный запрос для каждого entity. При 100 entities — 100 запросов.

**Решение**: Batch-загрузка edges одним запросом с `WHERE entity_id IN (...)`, затем распределение по records в Python.

---

### 4.2 Scalar subquery в document listing
**Файл**: `api/src/core/domain/knowledge_graph/services/knowledge_graph_document_service.py:110-115`

**Проблема**: Scalar subquery для chunk count выполняется для каждой строки результата. При 1000 документов — 1000 subquery executions.

**Решение**: Заменить на LEFT JOIN с GROUP BY:
```sql
SELECT d.*, COUNT(c.id) as chunk_count
FROM docs d
LEFT JOIN chunks c ON c.document_id = d.id
GROUP BY d.id
```

---

### 4.3 Повторное создание MetaData() для динамических таблиц
**Файлы**: Все knowledge_graph services создают `Table()` объекты через функции типа `knowledge_graph_document_table()`, `knowledge_graph_chunk_table()`.

**Проблема**: Каждый вызов создаёт новый `MetaData()` + `Table()`. SQLAlchemy не кеширует это.

**Решение**: Добавить LRU-кеш для Table objects по graph_id:
```python
from functools import lru_cache

@lru_cache(maxsize=128)
def _get_docs_table(graph_id: str) -> Table:
    return knowledge_graph_document_table(UUID(graph_id))
```

---

### 4.4 Deferred loading для больших JSONB полей
**Хороший пример**: `Trace.spans` уже использует `defer()` — правильно.

**Нужно проверить**: Модели с большими JSONB полями (`variants`, `definition`, `tools`, `original_operation_definition`) — добавить `deferred=True` для полей, которые не всегда нужны при listing.

---

## Phase 5: LOW — Подготовка к multi-database (Sprint 5-6)

### 5.1 Абстракция engine factory для поддержки Oracle и MSSQL
**Текущее**: Engine creation в `DatabaseSettings.get_engine()` с if/elif по driver type.

**Проблема**: При добавлении MSSQL нужно будет добавить ещё одну ветку. Разные БД требуют разные pool настройки, типы данных, SQL dialect.

**Решение**: Вынести в strategy pattern:
```python
class DatabaseEngineFactory(ABC):
    @abstractmethod
    def create_engine(self, settings: DatabaseSettings) -> AsyncEngine: ...

class PostgresEngineFactory(DatabaseEngineFactory): ...
class OracleEngineFactory(DatabaseEngineFactory): ...
class MSSQLEngineFactory(DatabaseEngineFactory): ...
```

---

### 5.2 Поддержка нескольких vector DB одновременно (VectorStoreRegistry)

> **Зависимости**: Требует завершения Phase 2 (engine консолидация) и 3.1 (DatabaseConnectionManager).

#### Текущее ограничение

`get_db_store()` и `get_db_client()` в `stores/__init__.py` возвращают **один singleton** на всё приложение, выбранный по `VECTOR_DB_TYPE`. Нет механизма для одновременной работы с несколькими vector DB.

Все 15+ вызовов по проекту (`store = get_db_store()`) завязаны на один глобальный store.

#### Целевое видение

1. **Основная БД = векторная БД по умолчанию**: если основная БД поддерживает pgvector, она автоматически является "default" vector store и использует тот же engine (без отдельного pool)
2. **Несколько vector DB одновременно**: всегда можно подключить дополнительные vector backends (Qdrant, отдельный PG инстанс и т.д.)
3. **Каждый Knowledge Graph / Collection** может быть привязан к конкретному vector store

#### Архитектура: VectorStoreRegistry

```python
class VectorStoreRegistry:
    """Registry of named vector store instances.

    Default store uses the main DB engine (if pgvector available).
    Additional stores can be registered dynamically.
    """

    def __init__(self, connection_manager: DatabaseConnectionManager):
        self._stores: dict[str, DocumentStore] = {}
        self._connection_manager = connection_manager

    def register(self, name: str, store: DocumentStore) -> None:
        """Register a named vector store."""
        self._stores[name] = store

    def get(self, name: str = "default") -> DocumentStore:
        """Get a vector store by name. Returns default if not specified."""
        if name not in self._stores:
            raise KeyError(f"Vector store '{name}' not registered. Available: {list(self._stores.keys())}")
        return self._stores[name]

    @property
    def default(self) -> DocumentStore:
        """The default vector store (main DB with pgvector)."""
        return self._stores["default"]

    def list_stores(self) -> dict[str, str]:
        """List all registered stores with their types."""
        return {name: type(store).__name__ for name, store in self._stores.items()}

    async def close_all(self) -> None:
        """Close all vector store connections."""
        for name, store in self._stores.items():
            if hasattr(store, 'close'):
                await store.close()
```

**Конфигурация** (через env vars или admin UI):
```yaml
# Основная БД = default vector store (один engine)
VECTOR_STORES__default__type: "PGVECTOR"
VECTOR_STORES__default__use_main_engine: true  # НЕ создавать отдельный pool

# Дополнительный Qdrant кластер
VECTOR_STORES__qdrant_prod__type: "QDRANT"
VECTOR_STORES__qdrant_prod__host: "qdrant.prod.internal"
VECTOR_STORES__qdrant_prod__port: 6333

# Отдельный PG инстанс для архивных данных
VECTOR_STORES__archive__type: "PGVECTOR"
VECTOR_STORES__archive__use_main_engine: false
VECTOR_STORES__archive__host: "pg-archive.internal"
```

**Привязка к Knowledge Graph / Collection**:
```python
# В модели KnowledgeGraph / Collection — поле vector_store_name
class KnowledgeGraph(UUIDAuditEntityBase):
    vector_store_name: Mapped[str] = mapped_column(
        String(100), default="default", nullable=False
    )
```

**Миграция вызовов**:
```python
# БЫЛО (один глобальный store):
store = get_db_store()
results = await store.document_collections_similarity_search(...)

# СТАНЕТ (registry с выбором по имени):
store = vector_registry.get(collection.vector_store_name)
results = await store.document_collections_similarity_search(...)

# Или для backward compatibility:
store = vector_registry.default  # == get_db_store() для старого кода
```

**Инициализация при startup**:
```python
async def _initialize_vector_stores(self, registry: VectorStoreRegistry):
    conn_manager = get_connection_manager()

    # Default store — через main engine (если pgvector доступен)
    if await _check_pgvector_available(conn_manager.async_engine):
        default_store = PgVectorStore(engine=conn_manager.async_engine)
        registry.register("default", default_store)

    # Дополнительные stores из конфигурации
    for name, config in settings.vector_stores.items():
        if name == "default":
            continue
        store = await _create_vector_store(name, config, conn_manager)
        registry.register(name, store)
```

#### План миграции

| Шаг | Описание | Effort |
|-----|----------|--------|
| 1 | Создать `VectorStoreRegistry` с поддержкой "default" | S |
| 2 | `get_db_store()` → делегирует в `registry.default` (backward-compatible) | S |
| 3 | Добавить `vector_store_name` поле в KnowledgeGraph/Collection модели | S |
| 4 | Обновить services чтобы выбирали store по name | M |
| 5 | Добавить admin UI для управления vector stores | M |
| 6 | Поддержка hot-reload (добавление store без рестарта) | L |

#### Принцип работы с connections

```
Основная БД (PostgreSQL + pgvector)
├── AsyncEngine (один pool)
│   ├── ORM sessions
│   ├── KG chunk service (vector search)
│   └── VectorStoreRegistry["default"] (PgVectorStore через тот же engine)
└── Shared SyncEngine (один pool)
    ├── APScheduler
    ├── OTel exporter
    └── Slack OAuth

Внешний Qdrant
└── QdrantAsyncClient (свой pool)
    └── VectorStoreRegistry["qdrant-prod"]

Отдельный PG для архива
└── Отдельный AsyncEngine (свой pool, создаётся только если настроен)
    └── VectorStoreRegistry["archive"]
```

**Ключевой принцип**: если vector store использует ту же БД что и основная — он работает через **тот же engine**. Отдельный pool создаётся **только** для реально отдельных инстансов.

---

### 5.3 `idle_in_transaction_session_timeout` на уровне PostgreSQL (Effort: XS)
**Проблема**: Если session открыла транзакцию и "забыла" закрыть (bug, timeout, cancel) — соединение зависает в `idle in transaction` состоянии, блокируя pool slot.

**Решение**: Настроить на уровне PostgreSQL:
```sql
ALTER SYSTEM SET idle_in_transaction_session_timeout = '60s';
-- Для production: 120s
```
И обработать это в приложении через `pool_pre_ping=True` (3.2).

---

## Phase 6: LOW — Observability и alerting (Sprint 6)

### 6.1 Логирование pool events
Включить `ECHO_POOL=True` в development, настроить structured logging для pool events:
- connection checkout
- connection checkin
- pool overflow
- pool timeout (QueuePool limit reached)

### 6.2 Grafana dashboard для DB metrics
Создать dashboard с:
- Pool utilization (checked_out / pool_size)
- Query latency percentiles (p50, p95, p99)
- Active transactions count
- `idle in transaction` connections
- Connection errors rate

### 6.3 Alerting rules
- Pool utilization > 80% — warning
- Pool utilization > 95% — critical
- `idle in transaction` > 5 — warning
- Connection errors > 0 — warning
- Query latency p99 > 5s — warning

---

## Приоритезация и порядок выполнения

### Phase 1 — Sprint 1 (Critical fixes)
| # | Задача | Effort | Impact | Зависимости |
|---|--------|--------|--------|-------------|
| 1.1 | Race condition в PGVector pool init | S | Data corruption prevention | — (временный fix до 2.3) |
| 1.2 | SQL Injection в динамических таблицах | M | Security | — |
| 1.3 | Pool exhaustion от concurrent workers | M | Stability | — |
| 1.4 | Explicit rollback в exception handlers | S | Data integrity | — |

### Phase 2 — Sprint 2-3 (Engine consolidation + session management)
| # | Задача | Effort | Impact | Зависимости |
|---|--------|--------|--------|-------------|
| 2.1 | Shared sync engine (3→1 sync pool) | S | -52 connections | — |
| 2.2 | Стандартизировать async session factory | M | Maintainability | — |
| 2.3 | PGVector через SQLAlchemy (2→1 async pool) | M-L | -10 connections, устраняет 1.1 | 2.2 |
| 2.4 | Background task lifecycle | M | Reliability | — |
| 2.5 | Пересчёт pool_size | S | Performance | 2.1, 2.3 |
| 2.6 | Autocommit vs explicit commit strategy | S | Performance | — |
| 2.7 | Batch commits в LLM extraction | S | Performance | — |

### Phase 3 — Sprint 3-4 (Centralization + monitoring)
| # | Задача | Effort | Impact | Зависимости |
|---|--------|--------|--------|-------------|
| 3.1 | DatabaseConnectionManager | M | Единая точка управления | Phase 2 |
| 3.2 | Enable pool_pre_ping | XS | Reliability | — |
| 3.3 | Pool monitoring endpoint | M | Observability | 3.1 |

### Phase 4 — Sprint 4-5 (Query optimizations)
| # | Задача | Effort | Impact | Зависимости |
|---|--------|--------|--------|-------------|
| 4.1 | N+1 в entity hydration | S | Performance | — |
| 4.2 | Scalar subquery → JOIN | S | Performance | — |
| 4.3 | Cache MetaData/Table objects | S | Performance | — |
| 4.4 | Deferred loading для JSONB | S | Performance | — |

### Phase 5 — Sprint 5-6 (Multi-database)
| # | Задача | Effort | Impact | Зависимости |
|---|--------|--------|--------|-------------|
| 5.1 | Engine factory для Oracle/MSSQL | L | Future-proofing | 3.1 |
| 5.2 | VectorStoreRegistry (multi vector DB) | L | Multi-vector-DB support | 2.3, 3.1 |
| 5.3 | idle_in_transaction_session_timeout | XS | PostgreSQL safety net | 3.2 |

### Phase 6 — Sprint 6 (Observability)
| # | Задача | Effort | Impact | Зависимости |
|---|--------|--------|--------|-------------|
| 6.1-6.3 | Logging, Grafana dashboard, alerting | M | Operations | 3.1, 3.3 |

### Итоговая таблица миграции engine

| Метрика | Сейчас | После Phase 1 | После Phase 2 | После Phase 3 |
|---------|--------|---------------|---------------|---------------|
| Async pools | 2 | 2 | 1 | 1 |
| Sync pools | 3 | 3 | 1 | 1 |
| Total pools | 5 | 5 | 2 | 2 (managed) |
| Max connections | ~85 | ~85 | ~33 | ~33 |
| Race conditions | PGVector init | Fixed (lock) | Eliminated | Eliminated |
| Centralized management | No | No | No | Yes |
| Monitoring | Partial | Partial | Partial | Full |

---

*Создано: 2026-03-29*
*Обновлено: 2026-03-29 — v3: устранены противоречия, добавлены зависимости, перегруппированы фазы*
*Статус: Draft*

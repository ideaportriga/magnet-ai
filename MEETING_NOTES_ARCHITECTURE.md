# Meeting Notes — Architecture Discussion

> Дата встречи: _____
> Участники: _____
> Дата подготовки: 2026-04-29

Дискуссионные темы (исходный список):
1. Workspaces — уникальный ключ `WS Name + Object System Name`
2. Несколько контейнеров под разные нагрузки + Taskiq
3. БД: одна или несколько (per WS? config vs usage/traces?)
4. Admin Panel — роли/разделы
5. S2S vs End-User authentication

---

## 1. Workspaces

### Что есть сейчас
- Концепта workspace **нет**. Есть только `Groups` (`api/src/core/db/models/user/group.py`) — RBAC на уровне всей организации.
- В `UUIDAuditSimpleBase` (`api/src/core/db/models/base.py:39`) поле `system_name` объявлено как **глобально уникальное** (`unique=True`) — прямо конфликтует с предложенной схемой `(WS, system_name)`.
- API-ключи привязаны к пользователю, не к WS (`api/src/services/api_keys`).
- 30+ моделей (`agent`, `collection`, `prompt`, `rag_tool`, `api_server`, `knowledge_graph`, `trace`, `evaluation`…) — все придётся переводить на workspace-scope.

### Что предлагается
- Сделать `Workspace` first-class сущностью с `system_name` и `name`, а не просто префиксом.
- `system_name` на дочерних сущностях — уникальным **в паре** `(workspace_id, system_name)`. Снять глобальный `unique=True` с базового класса, добавить композитный constraint в подклассах.
- Решить, что **не** скоупится по WS:
  - `users` — глобально
  - SSO/IdP-конфиги — глобально
  - `ai_models` (provider catalog) — глобально, WS только подписывается на разрешённые
  - MCP-каталог — глобально
  - `api_keys` — per-WS (см. п.5)

### Поэтапная миграция
1. Миграция: создать `workspaces` table + `workspace_id` (nullable) на всех entity-таблицах.
2. Backfill: создать `default` WS, проставить всем существующим строкам.
3. Поменять `UUIDAuditSimpleBase` — убрать глобальный unique, добавить композитный в подклассах.
4. Middleware (`api/src/middlewares/auth.py`): инжектить `workspace_id` в auth-контекст. Источник:
   - из header `x-workspace` (для UI)
   - из API-ключа (S2S — ключ принадлежит WS)
5. Repositories: централизованный фильтр через SQLAlchemy event/mixin. **Не** добавлять `WHERE workspace_id = …` руками в каждый query — гарантированы утечки.
6. Включить `NOT NULL` на `workspace_id` после backfill.

### Открытые вопросы для встречи
- [ ] Может ли пользователь принадлежать нескольким WS? (если да — `user_workspace_membership` таблица + роль per WS)
- [ ] Глобальный `org_admin` нужен? (видит все WS)
- [ ] Что с уже существующими `system_name` — миграция переименовывает, или пускаем как есть в default WS?

### Заметки со встречи
- 

---

## 2. Несколько контейнеров + Taskiq

### Что есть — и хорошо
- Taskiq уже **полностью интегрирован**. Брокер на Postgres+asyncpg с `LISTEN/NOTIFY` (`api/src/tasks/broker.py`).
- Отдельные сервисы `worker` и `scheduler` в `docker-compose.taskiq.yml`.
- Конкурренси настраивается (`TASKIQ_WORKER_CONCURRENCY`, дефолт 8).
- Lifecycle хуки в `api/src/tasks/worker_lifecycle` — поднимают только нужное (без полного Litestar).
- Категории задач уже разделены: `definitions/{background,jobs,knowledge_sources,housekeeping,custom}` + `schedules/`.

### Что предлагается
- **Один брокер** (Postgres) — не плодить.
- Разделить **очереди по типу нагрузки**: `realtime` / `batch` / `video` / `default`.
- Поднимать **разные deployment'ы воркеров** под каждую очередь:
  - `realtime` — низкая latency, мало воркеров, low concurrency
  - `batch` — много воркеров, высокий concurrency
  - `video` — GPU node selector, малый concurrency
- Scheduler оставить **single-instance** (он уже Recreate strategy) — горизонтально не масштабируется.

### Реализация
1. Ввести enum `TaskQueue = {realtime, batch, video, default}` и помечать таски декоратором/labels.
2. Конфиг воркера: `WORKER_QUEUES=video` → подписка только на свой channel.
3. compose/k8s — три deployment'а с разными ресурсами + HPA по глубине очереди (`SELECT count(*) FROM taskiq_messages WHERE channel='...'`).
4. Добавить DLQ-таблицу + dashboard в Grafana (стек Loki+Grafana уже есть).

### Открытые вопросы
- [ ] Realtime workloads — что туда попадает? (chat streaming, RAG inference?)
- [ ] Video processing — какие инструменты (ffmpeg, whisper)? Нужен ли GPU?
- [ ] Нужен per-WS rate limiting на очередях?

### Заметки со встречи
- 

---

## 3. База данных

### Что есть
- **Один** Postgres + pgvector (`pgvector/pgvector:pg16`), всё через SQLAlchemy + Alembic (`api/src/core/db/migrations`).
- В одной БД лежит всё: config (agents, prompts, tools), runtime (traces, observations, jobs), vector embeddings, taskiq-сообщения.
- В `pyproject.toml` ещё висит `motor` 3.7.0 — наследие Mongo, есть скрипт `mongo_to_sqlalchemy_migration.py`. Mongo сейчас не активен.

### Предложение: разделение config / observability через bind keys

**Идея:** один физический Postgres, две логические БД, два SQLAlchemy engine'а. Observability модели (traces, observations, metrics, evaluation runs) пишутся в отдельную БД через отдельный pool.

#### Почему это работает
- SQLAlchemy нативно поддерживает **multiple binds**: `__bind_key__ = "observability"` на модели → она использует отдельный engine.
- Два разных URL в env, по умолчанию **оба смотрят на тот же сервер**, разные `dbname`:
  ```
  DATABASE_URL=postgresql+asyncpg://user:pw@db:5432/magnet_config
  OBSERVABILITY_DATABASE_URL=postgresql+asyncpg://user:pw@db:5432/magnet_observability
  ```
- Когда observability разрастётся — меняешь только URL (другой хост, другой инстанс) **без правки кода**.
- Migrations делаются двумя `alembic` env'ами (по одному на bind), это стандартный pattern.

#### Что нужно сделать
1. В `api/src/core/db/` ввести `engines.py` с двумя engine'ами и `async_sessionmaker`'ами.
2. Базовый класс `ObservabilityBase` с `__bind_key__ = "observability"`.
3. Перенести модели `trace/`, `observation/`, `metric/`, частично `evaluation/` на этот base.
4. Разделить миграции: `migrations/config/` и `migrations/observability/`.
5. DI: фабрика сессий выбирает pool по типу репозитория.

#### Минусы / на что обратить внимание
- **JOIN'ы между config и observability ломаются** на уровне БД (если БД разные). Если сейчас где-то есть `JOIN traces ON agents.id = traces.agent_id` — придётся делать в два запроса в коде. Нужна ревизия.
- Транзакции через две БД — нет (без 2PC). Запись trace при ошибке — fire-and-forget, и сейчас, скорее всего, так и есть.
- FK с `agents.id → traces.agent_id` останутся как «логические» — без `REFERENCES`. Это нормально для observability (telemetry data часто denormalized).

### TimescaleDB на том же сервере — да, можно

**Короткий ответ: да.** TimescaleDB — это **расширение Postgres**, не отдельная СУБД.

#### Как это работает
- Ставишь Docker образ `timescale/timescaledb-ha:pg16` (или `timescale/timescaledb:latest-pg16`) — это **обычный Postgres 16 + предустановленное расширение TimescaleDB**.
- В нужной БД делаешь `CREATE EXTENSION IF NOT EXISTS timescaledb;`
- Конкретные таблицы (только observability — `traces`, `observations`, `metrics`) превращаешь в hypertables:
  ```sql
  SELECT create_hypertable('traces', 'created_at', chunk_time_interval => INTERVAL '1 day');
  ```
- Все остальные таблицы (агенты, промпты, юзеры) остаются **обычными Postgres-таблицами**. Они не знают про timescale.
- Один сервер, один порт, один процесс — наружу это просто Postgres.

#### Совмещение с pgvector
- Образ `timescale/timescaledb-ha` уже включает **pgvector**. Можно держать `CREATE EXTENSION vector;` и `CREATE EXTENSION timescaledb;` в одной БД.
- Если нужен только базовый `timescaledb` — ставится отдельно через apt.

#### Бонусы для observability
- **Continuous aggregates** — материализованные view с автообновлением: «requests per minute per workspace per agent» считается без cron-джобы.
- **Compression** — старые chunks сжимаются 10–20× автоматически (старше 7 дней → compress).
- **Retention policies** — `SELECT add_retention_policy('traces', INTERVAL '90 days');` и БД сама дропает старые chunks.
- **Partitioning по времени из коробки** — без ручных partitions/triggers.

#### Что поменять в инфре
1. В `docker-compose.yml`: образ `pgvector/pgvector:pg16` → `timescale/timescaledb-ha:pg16` (включает и vector, и timescale).
2. Отдельная alembic-миграция: `CREATE EXTENSION timescaledb` в observability БД.
3. После создания таблиц `traces` / `observations` — `SELECT create_hypertable(...)`. Это **post-create migration step**, alembic это делает через `op.execute()`.
4. Retention/compression policies — отдельной миграцией.

#### Риск
- На managed Postgres (RDS, Cloud SQL) **TimescaleDB обычно недоступен**. Нужен либо self-hosted Postgres, либо Timescale Cloud, либо AWS-альтернатива (Aurora Postgres + partitions руками).
- В образе `timescaledb-ha` лицензия Apache 2 для core фич, TSL для compression/CAGGs — для коммерческого self-host обычно ок, но **проверить**.

### Открытые вопросы
- [ ] Разворачиваемся on-prem или в managed cloud? (определяет, доступен ли Timescale)
- [ ] Сейчас есть JOIN'ы config↔observability в репозиториях? (надо грепнуть)
- [ ] Retention policy — сколько хранить traces? (90 дней? 30?)

### Заметки со встречи
- 

---

## 4. Admin Panel — разделы

### Что есть в `web/apps/@ipr/magnet-admin/` (24 контроллера в `api/src/routes/admin/`)

| Раздел из обсуждения | Статус | Где |
|---|---|---|
| Connections: API | ✅ | `api_servers` |
| Connections: MCP | ✅ | `mcp` |
| Connections: KS/KG | ✅ частично | `knowledge_providers`, `collections` |
| Connections: LLM | ✅ | `model_providers` |
| Consumers (Keys) | ✅ | `api-keys` |
| Config: Prompts | ✅ | `prompts` |
| Config: KS/KG | ✅ | `collections`, `knowledge_providers` |
| Config: RAG/R Tools | ✅ | `rag-tools`, `retrieval_tools` |
| Config: Agents | ✅ | `agents`, `ai_apps` |
| Config: Evals | ✅ | `evaluation_jobs`, `evaluation_sets` |
| **Usage + Traces** | ❌ | модели в БД есть, UI — заглушка `observability/` |

### Что предлагается
- Сгруппировать существующие разделы в **4 верхних таба**: **Connections / Consumers / Config / Observability**. Существующий routing маппится напрямую — нужен только rename + sidebar grouping.
- **Observability** — главный gap. Не строить dashboard сами:
  - Подключить **Grafana iframe / deep-link** (стек Loki+Grafana уже есть).
  - В админке — только list/filter traces + drill-down в один trace.
  - Метрики и графики — в Grafana (по WS-фильтру).
- Роли админки привязать к Workspace (после п.1):
  - `org_admin` — глобальный, видит все WS, управляет SSO/IdP/global catalog
  - `ws_admin` — полный CRUD внутри одного WS
  - `ws_editor` — Config (Prompts, Agents, Tools), без Connections и Keys
  - `ws_viewer` — read-only + Observability

### Открытые вопросы
- [ ] Кто видит Observability? (всем editor'ам или отдельная роль `ws_observer`?)
- [ ] API-keys управляет ws_admin или нужна отдельная роль `ws_security`?
- [ ] Connections (API/MCP/LLM) — per-WS или глобальные с подпиской?

### Заметки со встречи
- 

---

## 5. S2S vs End-User auth

### Что есть — почти готово
- **S2S**: header `x-api-key`, mapping в `api/src/services/api_keys`, кэш в памяти.
- **End-User**: JWT в cookie/Authorization header, SSO через OIDC (`api/src/routes/auth_v2.py`), MFA, refresh tokens, session revocation.
- Оба пути сходятся в одном middleware (`api/src/middlewares/auth.py`) и заполняют один auth-context.

### Что предлагается
1. **API-ключи скоупить по Workspace + scopes**:
   - `(workspace_id, name, scopes[], expires_at)`
   - scopes как `agents:read`, `agents:invoke`, `traces:read`, `*:*`
   - сейчас org-wide и слишком широкие.
2. **Чётко разделить контракты в коде**:
   ```python
   class S2SAuthContext:
       workspace_id: UUID
       api_key_id: UUID
       scopes: list[str]

   class UserAuthContext:
       user_id: UUID
       workspace_ids: list[UUID]   # пользователь может быть в нескольких WS
       active_workspace_id: UUID    # выбрана в UI
       roles: dict[UUID, list[str]] # роли per WS
   ```
   Сейчас они слиты — источник багов прав доступа.
3. **На уровне роутов** — guards (`api/src/guards/`) явно: `@requires_s2s`, `@requires_user`, `@requires_either`. Не оставлять «всё, что прошло middleware».
4. Audit log на auth-события (login, key-use, MFA-fail) — отдельная таблица в observability БД.

### Открытые вопросы
- [ ] Нужны ли persistent API-keys или only short-lived (OAuth client credentials flow)?
- [ ] SSO config per-WS (свой Azure AD на WS) или org-wide?
- [ ] MFA обязательна для `org_admin`?

### Заметки со встречи
- 

---

## Приоритезация для встречи

| # | Тема | Приоритет | Зависит от |
|---|---|---|---|
| 1 | Workspaces | 🔴 P0 | — (фундамент) |
| 2 | DB-стратегия (split + Timescale) | 🟡 P1 | независимо от 1, но проще делать после |
| 3 | Auth-контракты (S2S/User split) | 🟡 P1 | 1 (для WS-scoped keys) |
| 4 | Containers/Taskiq queues | 🟢 P2 | — |
| 5 | Admin grouping | 🟢 P2 | 1 (для ролей per WS) |

**Рекомендация:** начинать с Workspaces — без него остальное «висит в воздухе». Параллельно можно делать DB-split (он независим).

---

## Action items со встречи

- [ ] 
- [ ] 
- [ ] 


По 5 пункту. 

Еще если я вызываю стороннюю систему из магнита, то он behalf of какого-то пользователя, который использует магнит. 


пункт 1: 
tennant_id - это жесткое разграничение всего
workspace_id - это что-то вроде organization id, которая повзовляет шерить одну
запись внутри 

по поводу tennant нужно подумать о том, чтобы можно было использовать разную авторизацию для разных tennant. (при этом нужно понять, как их создавать, и как привязывать к какому-то oidc)
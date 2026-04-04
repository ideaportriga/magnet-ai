f# Roadmap: Надёжность, БД, Перфоманс

Второй раунд аудита бэкенда. Фокус — **надёжность системы**, **работа с базой данных**, **производительность**.

---

## Контекст

Первый раунд (`ROADMAP_IMPROVEMENTS.md`) закрыл безопасность, унификацию исключений и базовую надёжность. Этот раунд идёт глубже: сессии, пулы, блокировки, блокирующие вызовы в async, утечки соединений, graceful shutdown.

---

## КРИТИЧЕСКИЕ (блокируют стабильную работу в prod)

### C1. Shutdown не закрывает основной async engine

**Проблема.** `ShutdownPlugin._close_database_connections()` закрывает только vector DB пулы (Oracle/PGVector), но НЕ вызывает `DatabaseConnectionManager.close_all()`. Основной async engine (ORM, все route handlers, все сервисы) не dispose-ится при shutdown. Это означает:
- Соединения с PostgreSQL остаются открытыми после остановки процесса
- При частых рестартах (k8s rolling update) — накопление "zombie" соединений на стороне БД
- PostgreSQL может достичь `max_connections` лимита

**Где.** `core/server/plugins/shutdown.py:65-71` — в `_close_database_connections()` нет вызова `get_connection_manager().close_all()`

**Severity:** CRITICAL

---

### C2. Oracle shutdown через atexit с async-функцией

**Проблема.** `_close_oracle_connections()` регистрирует async-функцию `close_connection_pool()` через `atexit.register()`. Но `atexit` выполняет callbacks синхронно — async-функция просто вернёт корутину, которую никто не await-ит. Пул Oracle **никогда не закроется** при shutdown.

**Где.** `core/server/plugins/shutdown.py:72-82`

```python
async def close_connection_pool():  # async!
    client = get_db_client()
    await client.close_pool()

atexit.register(close_connection_pool)  # atexit не умеет await
```

**Severity:** CRITICAL

---

### C3. Race condition при создании пользователя из OIDC

**Проблема.** `upsert_user_from_oidc()` делает `get_one_or_none(email=email)`, и если `None` — создаёт пользователя. Между SELECT и INSERT нет блокировки. При параллельных OIDC-логинах с одним email (например, два запроса после редиректа) оба получат `None` и оба попытаются создать пользователя. Второй получит `IntegrityError` на unique constraint email.

Глобальный exception handler вернёт HTTP 400 "A conflicting record already exists" вместо нормального логина.

**Где.** `services/users/service.py:55-75` — нет `ON CONFLICT` или `SELECT ... FOR UPDATE`

**Severity:** CRITICAL (проявляется при каждом первом логине пользователя, если есть retry/double-click)

---

## ВЫСОКИЙ ПРИОРИТЕТ (деградация производительности)

### H1. Argon2 хеширование блокирует event loop

**Проблема.** `hash_password()` и `verify_password()` — синхронные CPU-bound операции (Argon2 намеренно медленный, ~100-300ms). Вызываются из async route handlers напрямую. На время хеширования весь event loop заблокирован — ни один другой запрос не обрабатывается.

**Где.** `services/users/password.py:16-23` — синхронные функции. Вызываются из:
- `auth_service.py:88` (signup)
- `auth_service.py:139` (authenticate/login)
- `mfa_service.py:68` (backup codes — 8 хешей подряд!)
- `mfa_service.py:158` (verify backup code — до 8 verify подряд)

**Импакт.** При MFA setup: 8 backup codes * ~200ms = **~1.6 секунды** блокировки event loop.

**Решение.** Обернуть в `asyncio.to_thread()`.

**Severity:** HIGH

---

### H2. QR-код генерация блокирует event loop

**Проблема.** `qrcode.make()` — синхронная CPU-bound операция (генерация PNG-изображения). Вызывается из async-контекста (`setup_mfa()`).

**Где.** `services/users/mfa_service.py:45-50`

**Severity:** HIGH (менее критично чем H1, но на нагруженной системе заметно)

---

### H3. httpx.AsyncClient создаётся на каждый запрос

**Проблема.** В нескольких местах `httpx.AsyncClient()` создаётся внутри `async with` на каждый запрос. Это означает:
- Новый TCP-коннект на каждый вызов (нет connection reuse)
- TLS handshake на каждый вызов
- Overhead на создание/уничтожение пула

**Где.**
- `services/users/oauth_service.py:222-233` — Google/GitHub user info (2 клиента на один OAuth callback)
- `services/agents/teams/note_taker_files.py` — скачивание файлов
- `services/agents/teams/graph.py` — Graph API вызовы
- `data_sources/vitepress/source.py`

**Severity:** HIGH (latency + TLS overhead на каждый OAuth логин)

---

### H4. N+1 запросы из-за default lazy loading на моделях

**Проблема.** Несколько ключевых моделей не указывают `lazy=` на relationship, что означает дефолтное `lazy="select"` (lazy loading). При итерации по результатам каждый доступ к relationship делает отдельный SELECT.

**Где.**
- `KnowledgeGraph.sources` — `lazy` не указан (`knowledge_graph.py:36`)
- `KnowledgeGraph.discovered_metadata_fields` — `lazy` не указан (`:43`)
- `KnowledgeGraph.extracted_metadata_fields` — `lazy` не указан (`:52`)
- `Provider.ai_models` — `lazy` не указан (`provider.py:80`)
- `Provider.collections` — `lazy` не указан (`:88`)
- `Collection.provider_rel` — `lazy` не указан (`collection.py:31`)

**Импакт.** При загрузке списка knowledge graphs с sources — N+1 запросов.

**Severity:** HIGH (для KG-heavy workflows)

---

### H5. Кеш API-ключей обновляется без lock

**Проблема.** `refresh_api_keys_caches()` перезаписывает два глобальных словаря (`API_KEYS_ENTITIES_CACHE`, `API_KEYS_PERSISTED_BY_HASH_CACHE`) без `asyncio.Lock`. При конкурентном вызове (два API key создаются одновременно) один кеш может быть в промежуточном состоянии.

**Где.** `services/api_keys/services.py` — нет lock вокруг присвоения кешей

**Severity:** HIGH (может привести к временной невалидности API-ключа)

---

## СРЕДНИЙ ПРИОРИТЕТ

### M1. Подозрительный timeout у RightNow: 5000 секунд

**Проблема.** `timeout=5000.0` — это 83 минуты. Вероятно, опечатка (должно быть 5.0 или 50.0). Операция может зависнуть на 83 минуты, удерживая соединение.

**Где.** `data_sources/rightnow/source.py`

**Severity:** MEDIUM

---

### M2. Health check не проверяет основные компоненты

**Проблема.** `/health` возвращает только memory и background tasks count. `/health/db` возвращает pool status. Но не проверяются:
- Scheduler (работает ли, обрабатывает ли задачи)
- Storage service (доступен ли blob storage)
- Vector DB (доступен ли)
- Кеш API-ключей (загружен ли)

Для k8s readiness probe это критично — pod может быть "healthy" но не способен обрабатывать запросы.

**Где.** `routes/__init__.py` — health endpoints

**Severity:** MEDIUM

---

### M3. Нет retry для transient DB ошибок

**Проблема.** При transient ошибках PostgreSQL (connection reset, timeout) операция сразу падает. Нет retry с backoff. `pool_pre_ping=True` защищает от stale connections, но не от сетевых glitches.

**Severity:** MEDIUM

---

### M4. Background tasks не ретраятся при ошибке

**Проблема.** `background_tasks.py` логирует ошибки background tasks, но не ретраит. Fire-and-forget задача, которая упала (например, отправка уведомления) — потеряна навсегда.

**Где.** `core/server/background_tasks.py:44-61`

**Severity:** MEDIUM

---

### M5. Bulk KG операции держат connection слишком долго

**Проблема.** Knowledge Graph sync pipeline делает bulk insert/update/delete в одной сессии. Для больших коллекций (тысячи документов) сессия удерживает connection из пула на минуты, уменьшая доступность для других запросов.

**Severity:** MEDIUM

---

## НИЗКИЙ ПРИОРИТЕТ

### L1. `lru_cache` на settings не инвалидируется

**Проблема.** `get_settings()` использует `@lru_cache(maxsize=1)` — настройки кешируются на время жизни процесса. Если нужно изменить настройки — нужен рестарт.

**Severity:** LOW (для большинства deployments это нормально)

---

### L2. Finally-блоки глотают ошибки

**Проблема.** В некоторых местах `except Exception: pass` в finally/cleanup блоках маскирует оригинальную ошибку.

**Где.** `core/domain/providers/controller.py:418-422` — `storages.unregister_backend()` в finally

**Severity:** LOW

---

### L3. Pool pre_ping на sync engine добавляет latency

**Проблема.** `pool_pre_ping=True` на sync engine (APScheduler) добавляет `SELECT 1` на каждый checkout. Для scheduler с pool_size=3 это минимальный overhead, но стоит отметить.

**Severity:** LOW

---

## Не в скоупе

| Задача | Причина |
|--------|---------|
| Circuit breaker для внешних сервисов (LLM, data sources) | Требует выбора библиотеки и паттерна (pybreaker/tenacity), архитектурное решение |
| Redis-backed кеши | Инфраструктурное изменение |
| Streaming responses для больших списков | Требует изменений на фронтенде |
| Zero-downtime миграции | Требует deployment pipeline изменений |
| Celery/RQ для background tasks с retry | Инфраструктурное изменение |

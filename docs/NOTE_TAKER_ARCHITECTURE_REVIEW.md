# Note Taker — Architecture Review

Дата: 2026-04-29
Автор: synthesis from a deep code audit (api/src + web admin) + три недавно починенных production-бага.

Scope: вся подсистема Note Taker — admin preview UI, Teams-bot runtime, transcription pipeline, postprocessing, интеграции (Confluence / Salesforce / Knowledge Graph). Цель — описать **что есть**, **что болит**, **что чинить и в каком порядке**.

Это документ для архитектурного решения, не для merge: после согласования кусков превращаем в roadmap-задачи.

---

## TL;DR

1. **Note Taker — это не один модуль, а пять разных, втиснутых в одну папку** (`services/agents/teams/`): admin-preview pipeline, Teams-bot runtime, file storage, integrations, transcript postprocessing. Они взаимно вызывают друг друга, но ответственности у них разные.
2. **Два параллельных слоя данных**. `note_taker_jobs` и `note_taker_settings` идут через advanced-alchemy домен; `transcriptions` и `note_taker_pending_confirmation` — через сырой asyncpg в `PgVectorClient`. Отсюда последние три прод-бага (JSONB encoding, race на read, codec inconsistency).
3. **Settings — нетипизированный JSONB**. Pydantic-модель есть в коде, но в БД лежит свободный dict, валидируется только на write, мерджится с дефолтами на каждом чтении. Эволюция схемы делается «на глаз».
4. **Два пути исполнения для одного и того же действия**. `/run` (URL) → taskiq, `/run-upload` (файл) → `asyncio.create_task`. Если когда-нибудь поставить worker на отдельный процесс, upload-превью просто не будет работать.
5. **Process-local STT-кеши без TTL** в Mistral- и ElevenLabs-провайдерах. Дренируются только явным вызовом, на failure пути остаются жить до перезапуска.
6. **Двойная декларация схемы**: Pydantic в Python + интерфейсы в TypeScript. Любой новый field требует двух согласованных PR.
7. **Status — magic string в шести местах**, не enum.

Положительная сторона: pipeline-factory, BaseTranscriber, Pinia-store фронта и migration consolidation сделаны нормально. Ниже разберу всё по слоям и предложу 5-фазный план.

---

## Inventory: что есть

```
api/src/
├── core/db/models/
│   ├── teams/
│   │   ├── note_taker_job.py            ← ORM model, NoteTakerJob (advanced-alchemy)
│   │   ├── note_taker_settings.py       ← ORM model, NoteTakerSettings (config: JSONB)
│   │   └── teams_meeting.py             ← Teams meeting context (FK на settings.system_name)
│   └── transcription/
│       └── transcription.py             ← ORM model, Transcription (advanced-alchemy) — НИКТО НЕ ИСПОЛЬЗУЕТ
│
├── core/domain/
│   └── note_taker_jobs/
│       ├── controller.py                ← REST: list/get/run/run-upload/rerun
│       ├── schemas.py                   ← NoteTakerJobSchema, Create, Update
│       └── service.py                   ← SQLAlchemyAsyncRepositoryService[NoteTakerJob]
│   (note_taker_settings нет как домена — лезут через generic /settings.py CRUD)
│
├── core/db/migrations/versions/
│   ├── 2025-11-16_add_stt_table_*.py    ← creates `transcriptions` table
│   └── 2026-03-26_note_taker_consolidated_*.py  ← teams_user, settings, jobs, pending_confirmation
│
├── routes/
│   ├── __init__.py                      ← регистрирует NoteTakerJobsController
│   ├── admin/recordings.py              ← admin-side recordings endpoint
│   ├── admin/settings.py                ← generic settings CRUD includes "note_taker_settings"
│   └── user/agents.py                   ← Teams bot messaging endpoints
│
├── services/agents/teams/
│   ├── note_taker.py                    ← bot runtime, settings loading, superuser lookup
│   ├── note_taker_settings.py           ← Pydantic settings schema + preview pipeline
│   │                                       (_run_preview_job_background, _rerun_postprocessing_background)
│   ├── note_taker_files.py              ← file upload helpers (S3/blob streaming)
│   ├── note_taker_utils.py              ← format_transcript_segments, helpers
│   ├── note_taker_transcription.py      ← bot-side STT entry (run_transcription_pipeline)
│   ├── note_taker_meeting.py            ← Teams meeting metadata
│   ├── note_taker_people.py             ← invited people extraction
│   ├── note_taker_cards.py              ← adaptive card builders
│   ├── note_taker_pending_store.py      ← pending confirmations (24h TTL, raw asyncpg)
│   ├── note_taker_store.py              ← teams_meeting CRUD (mostly raw SQL)
│   ├── note_taker_confluence.py         ← Confluence integration
│   ├── note_taker_salesforce.py         ← Salesforce integration
│   ├── transcript_postprocess.py        ← parse LLM output (speaker_mapping, keyterms)
│   └── note_taker_handlers/
│       ├── conversation_updates.py
│       ├── events.py
│       ├── installation.py
│       ├── messages.py
│       └── state.py                     ← bot event handlers
│
├── speech_to_text/transcription/        ← STT pipeline (origin: external/standalone module)
│   ├── service.py                       ← submit, get_meta, get_transcription, _RUNNING dict
│   ├── pipeline.py                      ← orchestration (download → STT → diar → merge → store)
│   ├── pipeline_factory.py              ← build_pipeline by stt_model_system_name
│   ├── models.py                        ← FileData, TranscriptionCfg
│   ├── storage/
│   │   ├── postgres_storage.py          ← PgDataStorage (raw asyncpg, бьёт `transcriptions`)
│   │   └── pgvector_collections.py      ← pgvector for embeddings (likely future)
│   ├── transcribe/
│   │   ├── base.py                      ← BaseTranscriber abstract
│   │   ├── mistral_transcribe/models.py ← MistralVoxtralTranscriber + _MISTRAL_CACHE
│   │   ├── elevenlabs_transcribe/models.py ← + _ELEVEN_CACHE
│   │   ├── azure_speech_transcribe/, azure_whisper/, oracle_transcribe/, oci_whisper/, whisper_http/, mock_transcribe/
│   └── diarize/
│       ├── azure_conversation/, azure_speech_diarize/, elevenlabs_diarize/, mistral_diarize/, oci_speech/
│
└── tasks/definitions/background.py      ← note_taker_preview_bg_task, note_taker_rerun_bg_task

web/apps/@ipr/magnet-admin/src/
├── stores/noteTakerStore.ts             ← Pinia store, polling, normalization
└── components/NoteTaker/
    ├── Page.vue, Header.vue, Drawer.vue, details.vue, CreateNew.vue, NoteTakerProviders.vue
    └── tabs/
        ├── General.vue, Bot.vue, Transcription.vue
        ├── PostProcessing.vue, Prompts.vue
        ├── Embedding.vue, Integrations.vue, MSTeams.vue
```

**Краткая статистика поверхности:** 50+ Python-файлов, ~10 миграций касаются темы, 9 STT-провайдеров (3 диаризатора), 8 Vue-табов, 2 фоновых задачи taskiq, 1 раздельный pgvector-клиент.

---

## Текущая архитектура (data flow)

### Путь A: Admin Preview (то, что я чинил)

```
[Browser] frontend NoteTakerStore.runPreview(file)
   │
   │ POST /api/admin/note-taker/jobs/{settings_id}/run-upload
   ▼
[Litestar] NoteTakerJobsController.run_preview_upload()
   │ - jobs_service.create(NoteTakerJobCreate)        ← advanced-alchemy
   │ - asyncio.create_task(_run_preview_job_background(...))   ← НЕ taskiq, локальный таск
   │ - returns NoteTakerJobSchema (job_id)
   ▼
[in-process bg task]  _run_preview_job_background()
   │ - upload bytes → object storage (note_taker_files._upload_stream_to_object)
   │ - db_store.client.init_pool()                    ← legacy no-op
   │ - transcription_service.submit(name, ext, object_key, stt_model, keyterms)  ← global _RUNNING dict
   │ - poll status каждые 5..30s, timeout 900s
   │ - transcription = transcription_service.get_transcription(file_id)
   │ - format_transcript_segments(transcription)      ← страдает от JSONB-codec race
   │ - LLM postprocessing (STT_TRANSCRIPT_POSTPROCESSING template)
   │ - _update_preview_job_status(status='transcribed', result={...})
   ▼
[browser polls] GET /api/admin/note-taker/jobs/{settings_id}/{job_id}
   │ - jobs_service.get(job_id)                       ← advanced-alchemy
   │ - NoteTakerJobSchema.model_validate(job)         ← страдает от JSONB-codec race
```

### Путь B: Teams Bot

```
[Teams] meeting recording event → Azure Bot Service → /teams/note-taker/messages
   │
   ▼
[Litestar] handle_note_taker_message_by_name()
   │ - app.state.note_taker_registry / teams_note_taker_runtime
   │ - bot.dispatch(activity)
   ▼
[note_taker_handlers/*] process activity
   │ - _is_meeting_conversation, _resolve_meeting_details
   │ - _load_note_taker_settings_for_context() ← может триггерить Salesforce send (note_taker.py:231)
   ▼
[note_taker_transcription] run_transcription_pipeline
   │ - _build_transcription_keyterms (settings.keyterms + invited people)
   │ - _ensure_vector_pool_ready (бессмысленный legacy вызов)
   │ - _start_transcription_from_object_key
   ▼
[speech_to_text.service] submit(...) → же, что и Path A
```

### Путь C: Rerun postprocessing (после "transcribed")

```
[Browser] continue button → POST /api/admin/note-taker/jobs/{settings_id}/rerun
   │
   ▼
[Litestar] NoteTakerJobsController.rerun_postprocessing()
   │ - taskiq enqueue note_taker_rerun_bg_task.kiq(...)
   ▼
[Taskiq worker] _rerun_postprocessing_background()
   │ - postprocessing prompts (chapters, summary, insights)
   │ - update job.result with postprocessing dict
   │ - status='completed'
```

### Storage map

| Таблица | Доступ из | Слой |
|---|---|---|
| `note_taker_settings` | `routes/admin/settings.py` (generic CRUD) + service helpers | mixed (ORM session + raw via `note_taker_pending_store`) |
| `note_taker_jobs` | `core/domain/note_taker_jobs/service.py` | advanced-alchemy |
| `note_taker_pending_confirmation` | `services/agents/teams/note_taker_pending_store.py` | **raw asyncpg** |
| `transcriptions` | `speech_to_text/transcription/storage/postgres_storage.py` (`PgDataStorage`) | **raw asyncpg via PgVectorClient** |
| `teams_meeting` | `services/agents/teams/note_taker_store.py` | mixed (raw SQL + ORM upsert) |

**Корень всех трёх недавних production-багов — в правом столбце. Где «raw asyncpg», там JSONB type codec не зарегистрирован/гонщит, и ломается то serialization, то deserialization.**

---

## Что сделано хорошо (для контекста)

- **Pipeline factory** (`speech_to_text/pipeline_factory.py`). Разделение pipeline и провайдеров через abstract `BaseTranscriber` / `BaseDiarization` чистое: добавить новый STT — это один `class XTranscriber(BaseTranscriber)` плюс регистрация.
- **Pinia store фронта** (`noteTakerStore.ts`) корректно нормализует ответ (массив / paginated / single object), пуллинг через `setTimeout`-recursive (не `setInterval`) — без race на медленных запросах.
- **Миграция консолидации** (`2026-03-26_note_taker_consolidated_*`) — большая, но честная. Ничего «потеряно в истории» — все нужные ALTER TABLE собраны в одном файле.
- **Domain pattern для `note_taker_jobs`** (controller/service/schemas) — стандартный, минимальный, читается за минуту.
- **Pydantic-схемы settings** (`PromptSettingSchema`, `NoteTakerSettingsSchema`) — есть, проблема только в том, что они не валидируются на read.
- **Tasqueue presets** (`@observe()` декоратор, timeout=3600) — корректно для долгих STT-job.

Эти куски сохраняем как есть.

---

## Pain points: по приоритету

### Critical — активно ломает прод

#### C1. JSONB codec race в `PgVectorClient` (3 бага подряд)

`PgVectorClient._setup_connection_types` регистрирует JSONB codec на asyncpg-соединение и кеширует факт регистрации по `id(asyncpg_conn)`. Python переиспользует `id()` после gc → когда SQLAlchemy инвалидирует connection и создаёт новое с тем же id, кеш ложно говорит «уже зарегистрирован».

Фикс «снизу» (engine_factory `init=` callback) применён, но проблема — что **этот клиент вообще не должен использоваться для не-векторных таблиц**. `transcriptions` и `note_taker_pending_confirmation` — обычные JSONB-таблицы, для них есть ORM с правильным `json_serializer/json_deserializer` в engine.

> Файлы: `stores/pgvector_db/client.py:60-89`, `speech_to_text/transcription/storage/postgres_storage.py`, `services/agents/teams/note_taker_pending_store.py`.

#### C2. Inconsistent task enqueueing (URL vs upload)

`NoteTakerJobsController.run_preview` (URL):
```python
await note_taker_preview_bg_task.kiq(job_id=..., source_url=..., ...)   # taskiq
```

`NoteTakerJobsController.run_preview_upload` (file):
```python
asyncio.create_task(_run_preview_job_background(job_id=..., file_bytes=..., ...))   # in-process
```

Сейчас работает, потому что taskiq и API в одном процессе. Когда worker отделят (или при горизонтальном scale-out): URL-job выполнится у worker'а, upload-job останется висеть на API-инстансе и потеряется при рестарте.

> Файлы: `core/domain/note_taker_jobs/controller.py:81, 135`.

#### C3. Pending confirmation TTL leak

`note_taker_pending_confirmation` имеет 24h TTL, но проверка ленивая: только в `load_and_delete_pending`. Если запись никто не загружает (бот не получил confirmation от пользователя), она лежит вечно. Нет scheduled cleanup task.

> Файл: `services/agents/teams/note_taker_pending_store.py:25`.

#### C4. STT process-local caches без bound

```python
_MISTRAL_CACHE: dict[str, Dict[str, Any]] = {}  # mistral_transcribe/models.py:17
_ELEVEN_CACHE: dict[str, ...] = {}              # elevenlabs_transcribe/models.py:17
```

Дренируются только в `_drain_cached(file_id)`, который вызывается на **happy-path** перед записью результата. На failure / timeout / cancellation — запись остаётся. После 1000 неудачных STT-job в кеше 1000 payload'ов. Memory leak, проявится через 1-2 недели аптайма у активной инсталляции.

> Файлы: `speech_to_text/transcription/transcribe/{mistral,elevenlabs}_transcribe/models.py:17`.

#### C5. Status — magic string, дрейф в 6 местах

Значения `pending | running | rerunning | transcribed | completed | failed | timeout` определены implicitly:
- В `controller.py:164` — список разрешённых для rerun.
- В `note_taker_settings.py` — внутри `_run_preview_job_background` (около десятка ветвлений).
- В `transcribe/base.py:61` — pipeline переходы.
- Во фронт-компоненте `Drawer.vue` — `pipelineSteps` строит UI по статусу.
- В Pinia-store TS-интерфейсе.
- В DB как `String(50)`.

Любое добавление нового статуса (например, `cancelled`) — это 6 согласованных правок без compile-time гарантий.

### High — серьёзный долг, активный риск

#### H1. Два параллельных слоя данных

Уже разбирали в предыдущем review (`Почему PgDataStorage не использует advanced-alchemy`). Резюме:
- Модель `Transcription` лежит готовая в `core/db/models/transcription/transcription.py`.
- Сервиса `core/domain/transcriptions/` нет — никто не написал.
- `PgDataStorage` строит UPDATE через f-string + whitelist полей, дублируя `mapped_column`.
- Внешне это выглядит так, будто `speech_to_text/` — отдельный микросервис, который привинтили к Postgres через первый попавшийся client.

#### H2. `services/agents/teams/note_taker_*` смешивает 5 ответственностей в одной папке

| Группа файлов | Реальная ответственность | Где должно жить |
|---|---|---|
| `note_taker.py` (runtime), `note_taker_handlers/`, `note_taker_cards.py`, `note_taker_meeting.py`, `note_taker_people.py`, `note_taker_pending_store.py` | Teams-bot runtime | `services/agents/teams/note_taker/` (сабмодуль) |
| `note_taker_settings.py` (admin preview pipeline + Pydantic schema) | Admin-API + бизнес-логика preview | `core/domain/note_taker_settings/` |
| `note_taker_files.py` | Файловый storage helpers | `services/storage/audio_uploads.py` |
| `note_taker_transcription.py` | Bot-сторонний entrypoint в STT | `services/agents/teams/note_taker/transcription.py` |
| `note_taker_confluence.py`, `note_taker_salesforce.py` | Внешние интеграции | `services/integrations/{confluence,salesforce}/` |
| `transcript_postprocess.py`, `note_taker_utils.py` | Парсинг LLM-output, форматирование сегментов | `services/agents/teams/note_taker/postprocess.py` или общий `services/transcription/` |

Сейчас всё в одной плоской папке → циклические импорты («note_taker.py импортирует note_taker_files импортирует note_taker_settings импортирует note_taker_meeting»…), невозможность тестировать одну часть без поднятия всех остальных, и любой PR в Note Taker трогает 5+ файлов.

#### H3. Settings — нетипизированный JSONB

`NoteTakerSettings.config: JSONB` хранит произвольный dict. На read клиент мерджит с дефолтами через `_merge_note_taker_settings`. Pydantic-модель есть, но запускается только в `_validate_*_settings` при write — и то по подмножеству полей (Salesforce, Confluence, post_transcription валидируются, остальное — нет).

Последствия:
- **Schema drift**: обновили дефолты в Python, старые записи в БД остаются с пробелами.
- **No migration story**: переименование/удаление поля в config — это `UPDATE note_taker_settings SET config = config - 'old_key' || jsonb_build_object('new_key', config->'old_key')`, но никто такие миграции не пишет.
- **Type errors появляются в runtime** глубоко в pipeline, а не на boundary.

#### H4. Frontend ↔ Backend schema duplication

`NoteTakerSettings` определён:
- В Python: `services/agents/teams/note_taker_settings.py` (Pydantic).
- В TypeScript: `web/.../stores/noteTakerStore.ts:27` (interface).

Любое поле должно быть добавлено в обоих. Тесты этого не ловят. Код-ревью не ловит. Поймать может только баг в проде (фронт показал старое поле — `undefined` в `tab.Bot.vue`).

#### H5. Hidden side effects в settings-loading

`_load_note_taker_settings_for_context()` в `note_taker.py:166` помимо чтения настроек **может отправить Salesforce-сообщение** (через ветку `_send_stt_recording_to_salesforce` → `_send_expandable_section`). Никаких признаков этого в имени функции и сигнатуре.

Любой будущий разработчик вызовет «загрузить настройки» в новом месте — и неожиданно отправит письмо в Salesforce.

### Medium — архитектурный долг, нет прямого ущерба

#### M1. Validator key hardcoding

```python
# note_taker_settings.py:100, 114
def _validate_confluence_settings(integration):
    cfg = integration.get("confluence", {})  # hardcoded key
    if not isinstance(cfg.get("enabled"), bool):  # hardcoded key
        raise ValueError(...)

def _validate_salesforce_settings(integration):
    cfg = integration.get("salesforce", {})
    if not isinstance(cfg.get("send_transcript_to_salesforce"), bool):
        ...
```

Имена ключей встречаются в 4-5 местах: валидатор, дефолт, frontend-tab, формы, миграции. Если переименовать `enabled` на `is_active`, надо найти всё руками.

#### M2. Магическая строка `pipeline_id` = `stt_model_system_name`

В `note_taker_settings.py:34` стоит комментарий: `pipeline_id` в config — это на самом деле `stt_model_system_name`. Frontend пишет `pipeline_id`, backend читает `pipeline_id` и передаёт как `stt_model_system_name`. История переименования; устаревший термин остался.

#### M3. Tight coupling: bot → admin

Teams-бот не может работать без:
- Записи в `note_taker_settings` (`system_name = X`).
- Записи в `teams_meeting` с `note_taker_settings_system_name = X`.
- Связанной записи в `providers` с `superuser_id`.

Admin создаёт всё это вручную; нет lazy initialization. Если settings удалили — bot падает в `LookupError`. Нет fallback на дефолтные настройки.

#### M4. Provider keyterms variance

ElevenLabs обрезает keyterms: max 5 слов на фразу, max 100 фраз total (`elevenlabs_transcribe/models.py:46-61`). У Mistral — без ограничений. У Azure — третий контракт. `_build_transcription_keyterms` в `note_taker_transcription.py:58` строит общий список, но провайдеры обрабатывают его по-разному.

Лучше — нормализовать на boundary `BaseTranscriber.set_keyterms(list[str])` с общим контрактом и per-provider sanitizer.

#### M5. `_RUNNING: dict[str, asyncio.Task]` в `service.py:21`

Глобальный dict хранит все active STT-задачи. Никогда не очищается явно (`_run_pipeline_and_cleanup` нечётко документирован). Утечка памяти аналогично C4 на failure-путях.

#### M6. Inconsistent error handling

- `_load_note_taker_settings_by_system_name()` raise LookupError (note_taker.py:130).
- `_load_note_taker_settings_for_context()` catches и возвращает defaults (note_taker.py:178).
- `_validate_*_settings` raise ValueError.
- Pipeline.run catches everything, helpfully `update_status(file_id, 'failed', error=str(exc))`.

Нет единой стратегии: что считается «job failed» и должно быть видно пользователю vs «recoverable, retry», vs «программная ошибка, log + raise».

### Low — nice-to-have

#### L1. Dead-feeling code

- `_ELEVEN_CACHE` / `_MISTRAL_CACHE` дренируются только на happy-path → могут быть просто не нужны (payload и так попал в `transcriptions.transcription`).
- `personal_config_store` в `note_taker_people.py` — per-user settings override; неясно, есть ли реальный use-case.
- `MAGNET_SYNC_TIMEOUT=300s` — feature flag, дефолт off, никто не тестирует включенный путь.

#### L2. Pending confirmation = что это вообще?

Из имени файла и одной таблицы — это очередь подтверждений: бот спрашивает «отправить расшифровку в Confluence?», пользователь жмёт кнопку, бот достаёт `pending_confirmation` и выполняет. Но нигде это не документировано. Будущему разработчику придётся реверсить таблицу из миграции и ручного чтения handlers.

#### L3. Множество routes для одного субдомена

`/api/admin/note-taker/jobs/...`, `/api/admin/note-taker/settings/...` (через generic), `/teams/note-taker/messages`, `/teams/note-taker/{name}/messages`, `/admin/recordings/...` — пять разных префиксов, четыре разных контроллера. Лучше один `/note-taker` namespace с подпапками.

---

## Refactor proposals

Группирую от наибольшего эффекта/наименьшей сложности к меньшему.

### P1. Создать домен `core/domain/transcriptions/` (closes C1, H1)

Минимальный shim:

```python
# core/domain/transcriptions/service.py
from advanced_alchemy.extensions.litestar import repository, service
from core.db.models.transcription.transcription import Transcription


class TranscriptionsService(service.SQLAlchemyAsyncRepositoryService[Transcription]):
    class Repo(repository.SQLAlchemyAsyncRepository[Transcription]):
        model_type = Transcription
    repository_type = Repo
```

```python
# core/domain/transcriptions/schemas.py
from pydantic import BaseModel
from typing import Any, Optional

class TranscriptionRead(BaseModel):
    id: str
    file_id: str
    status: str
    error: Optional[str] = None
    transcription: Optional[dict[str, Any]] = None
    full_text: Optional[str] = None
    duration_seconds: Optional[float] = None
    # ... + те же string→dict валидаторы для transcription/participants как у note_taker_jobs
```

`PgDataStorage` остаётся как **adapter** для STT-pipeline (он опирается на старые публичные сигнатуры `save_audio`, `update_status`, `update_transcription`, `update_error`, `get_meta`, `get_transcription`, `get_audio_url`, `load_audio`, `delete_audio`), но методы делегируют в `TranscriptionsService`:

```python
class PgDataStorage:
    async def update_transcription(self, file_id: str, transcription: dict) -> None:
        async with async_session_maker() as session:
            svc = TranscriptionsService(session=session)
            rec = await svc.get_one_or_none(file_id=file_id)
            if rec is None:
                return
            await svc.update(
                {"status": "completed", "transcription": transcription},
                item_id=rec.id,
            )
            await session.commit()
```

Что уходит:
- `_update_fields` с whitelist'ом и f-string SQL.
- `_JSONB_FIELDS` constant.
- Зависимость на `PgVectorClient` для не-векторных операций.
- Race на JSONB codec (ORM использует `json_serializer/json_deserializer` engine'а).

Pgvector-клиент остаётся для `pgvector_collections.py` — это его настоящая зона ответственности.

**Объём:** ~200 строк нового кода, удаление ~150 строк raw-SQL. Один PR. Не ломает API.

### P2. Вычленить `core/domain/note_taker_settings/` (closes H2 частично)

Сейчас Pydantic-схема и admin-preview pipeline лежат в `services/agents/teams/note_taker_settings.py` — на 800+ строк.

Раздробить:

```
core/domain/note_taker_settings/
├── __init__.py
├── schemas.py                ← PromptSettingSchema, NoteTakerSettingsSchema, NoteTakerSettingsCreate/Update
├── service.py                ← NoteTakerSettingsService (advanced-alchemy)
├── controller.py             ← REST контроллер вместо generic CRUD из routes/admin/settings.py
├── preview/
│   ├── __init__.py
│   ├── runner.py             ← _run_preview_job_background (переименовать в run_preview_job)
│   ├── postprocess.py        ← _rerun_postprocessing_background
│   └── postprocess_schemas.py← speaker_mapping, suggested_keyterms parser DTOs
└── validators.py             ← _validate_salesforce/confluence/post_transcription
```

В `services/agents/teams/note_taker/` остаётся только **runtime**:

```
services/agents/teams/note_taker/
├── __init__.py
├── runtime.py                ← bot runtime (бывший note_taker.py: load_note_taker_runtime_from_env, NoteTakerRegistry)
├── settings_loader.py        ← _load_note_taker_settings_for_context (ТОЛЬКО загрузка, без send_*)
├── transcription.py          ← run_transcription_pipeline (бывший note_taker_transcription.py)
├── meeting.py
├── people.py
├── cards.py
├── pending_store.py          ← переписать на advanced-alchemy домен
├── handlers/
│   ├── conversation_updates.py
│   ├── events.py
│   ├── installation.py
│   ├── messages.py
│   └── state.py
└── postprocess.py            ← format_transcript_segments, transcript_postprocess
```

Интеграции — отдельный пакет, не лазит внутрь note_taker:

```
services/integrations/
├── confluence/note_taker.py  ← бывший note_taker_confluence.py
└── salesforce/note_taker.py  ← бывший note_taker_salesforce.py
```

Вызываются через event-bus или explicit dependency injection из preview-runner и handlers, не через cross-import.

**Объём:** значительный, делать постепенно, slice-by-slice. Один slice = один файл переехал и один import-fix. Roadmap pattern такой же, как у CUBE-миграции.

### P3. Settings: единый source of truth + версионирование (closes H3, H4)

**Шаг 1.** Перенести `NoteTakerSettingsSchema` в `core/domain/note_taker_settings/schemas.py`. Сделать его единственным источником правды.

**Шаг 2.** Добавить `NoteTakerSettings.settings_revision: int` колонку. На каждое изменение схемы инкрементируем — чтобы можно было писать миграции «прочитал config с revision < N, transformed, записал с revision = N».

**Шаг 3.** На read валидировать через Pydantic. Если падает → fall back на дефолты + log warning. Сейчас невалидный config молча работает с подмешиванием дефолтов, и обнаружится только в pipeline.

**Шаг 4.** Генерировать TypeScript-типы из Pydantic. Вариант:
- `datamodel-code-generator` → JSON Schema → `quicktype` / `json-schema-to-typescript` → `web/.../stores/types/noteTakerSettings.ts`.
- Или через Litestar OpenAPI + `openapi-typescript`.

Что уходит: рассинхрон фронт↔бэк-схемы, magic key drift в валидаторах.

### P4. Status enum (closes C5)

```python
# core/domain/note_taker_jobs/status.py
from enum import StrEnum

class JobStatus(StrEnum):
    PENDING = "pending"
    RUNNING = "running"
    TRANSCRIBED = "transcribed"  # waiting for user to confirm speakers
    RERUNNING = "rerunning"      # postprocessing in flight
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"

    @classmethod
    def is_terminal(cls, status: "JobStatus") -> bool:
        return status in {cls.COMPLETED, cls.FAILED, cls.TIMEOUT}

    @classmethod
    def can_rerun(cls, status: "JobStatus") -> bool:
        return status in {cls.COMPLETED, cls.FAILED, cls.TRANSCRIBED}
```

Использовать везде, генерировать TS:
```ts
// web/.../stores/types/jobStatus.ts (auto-generated)
export const JobStatus = { Pending: "pending", Running: "running", ... } as const;
export type JobStatus = typeof JobStatus[keyof typeof JobStatus];
```

### P5. Унифицировать пути исполнения (closes C2)

`run_preview_upload` сейчас делает: `await file.read()` → `asyncio.create_task(_run_preview_job_background(..., file_bytes=...))`.

Предлагается:
1. В контроллере — записать файл в object storage сразу (как `note_taker_files._upload_stream_to_object` делает уже сейчас, просто вынести наружу).
2. После заливки — `note_taker_preview_bg_task.kiq(job_id=..., source_url=None, object_key=...)`.
3. В taskiq-task: `_run_preview_job_background(..., object_key=...)`.

В таске не передавать `file_bytes` (как сейчас), а только `object_key`. Тогда тот же путь работает и для URL, и для upload, и для Teams-bot. Один code-path вместо трёх.

Также: добавить `note_taker_preview_bg_task` параметры `bytes_=None`, чтобы schema kwargs была совместима.

### P6. Pending confirmations: scheduled cleanup (closes C3)

```python
# tasks/definitions/housekeeping.py
@broker.task(timeout=60)
async def cleanup_expired_pending_confirmations() -> None:
    cutoff = datetime.now(tz=timezone.utc) - timedelta(hours=24)
    async with async_session_maker() as session:
        await session.execute(
            delete(NoteTakerPendingConfirmation).where(
                NoteTakerPendingConfirmation.created_at < cutoff
            )
        )
        await session.commit()
```

```python
# tasks/schedules/system.py
schedule_label_to_kicker[cleanup_expired_pending_confirmations] = labels(
    cron="0 */6 * * *",  # every 6h
)
```

Также — переписать `note_taker_pending_store.py` через `core/domain/note_taker_pending_confirmations/` (advanced-alchemy). После этого C1 закрывается ещё в одной точке.

### P7. Bound STT caches (closes C4, M5)

Самое простое — **удалить кеши вообще**. `_MISTRAL_CACHE`, `_ELEVEN_CACHE`, `_RUNNING` хранят payload-ы, которые либо уже записаны в `transcriptions`, либо не нужны после возврата `_transcribe()`.

Альтернатива — `cachetools.TTLCache(maxsize=128, ttl=600)`, дренирование при ошибке через `try/finally`.

`_RUNNING: dict[str, asyncio.Task]` — нужен только для `cancel(file_id)` или похожего админского действия. Сейчас никто не отменяет → можно убрать.

### P8. Validator-driven config keys (closes M1)

Заменить хардкод имён ключей на declarative описание:

```python
# core/domain/note_taker_settings/schemas.py
class IntegrationConfluenceSchema(BaseModel):
    enabled: bool = False
    base_url: Optional[str] = None
    space_key: Optional[str] = None
    parent_page_id: Optional[str] = None

class IntegrationSalesforceSchema(BaseModel):
    enabled: bool = False
    send_transcript_to_salesforce: bool = False
    object_type: Optional[str] = None

class IntegrationsSchema(BaseModel):
    confluence: IntegrationConfluenceSchema = IntegrationConfluenceSchema()
    salesforce: IntegrationSalesforceSchema = IntegrationSalesforceSchema()
```

Pydantic сам валидирует. Никаких `_validate_confluence_settings` функций.

### P9. Settings loading: pure read

`_load_note_taker_settings_for_context()` должен ТОЛЬКО возвращать settings dict. Salesforce-side-effect вынести в отдельную функцию `maybe_send_recording_to_salesforce(settings, recording)`, вызывать из handler'а после получения settings.

Принцип: name это контракт, side-effects явные.

### P10. Per-provider keyterms contract (closes M4)

```python
# speech_to_text/transcription/transcribe/base.py
class BaseTranscriber:
    MAX_KEYTERM_WORDS: ClassVar[int | None] = None
    MAX_KEYTERMS: ClassVar[int | None] = None

    def _sanitize_keyterms(self, keyterms: list[str]) -> list[str]:
        if self.MAX_KEYTERM_WORDS:
            keyterms = [k for k in keyterms if len(k.split()) <= self.MAX_KEYTERM_WORDS]
        if self.MAX_KEYTERMS:
            keyterms = keyterms[:self.MAX_KEYTERMS]
        return keyterms
```

```python
class ElevenLabsTranscriber(BaseTranscriber):
    MAX_KEYTERM_WORDS = 5
    MAX_KEYTERMS = 100
```

Per-provider sanitization через class attribute, не дублируя код.

---

## Recommended sequencing

Каждая фаза — **самостоятельный slice**, можно мержить отдельно, измеряется отдельно. Принцип: «сначала останавливаем кровь, потом чиним позвоночник».

### Phase 1 — Stop the bleeding (1 sprint)

- [x] **JSONB codec init in engine_factory** — already merged.
- [x] **Defensive `_parse_result` validator** — already merged.
- [x] **Defensive `_coerce_jsonb_to_dict` in format_transcript_segments** — already merged.
- [ ] Добавить scheduled cleanup задачу для `note_taker_pending_confirmation` (P6, простой).
- [ ] Удалить `_MISTRAL_CACHE` / `_ELEVEN_CACHE` / `_RUNNING` (если grep показывает, что они не нужны вне модуля), либо обернуть в `cachetools.TTLCache` (P7).

**Acceptance:** ни одной из обнаруженных race / leak проблем не остаётся в проде. Audit: `grep -rn "_MISTRAL_CACHE\|_ELEVEN_CACHE\|_RUNNING\b" api/src` должен вернуть пусто или только определения с TTLCache.

### Phase 2 — Transcriptions domain (1 sprint)

- P1: создать `core/domain/transcriptions/{service,schemas}.py`, `PgDataStorage` методы переписать через сервис.
- Удалить `_update_fields`, `_JSONB_FIELDS`, `_ALLOWED_UPDATE_FIELDS`.
- Удалить зависимость `PgDataStorage` на `PgVectorClient` (заменить на `async_session_maker` + service).

**Acceptance:** ни одного raw `store.client.execute_command` или `store.client.fetchrow` в `speech_to_text/`. CI прогоняется зелёно. Никаких изменений в публичной поверхности `transcription_service.submit / get_meta / get_transcription`.

### Phase 3 — Note Taker Settings domain (1-2 sprints, slice-by-slice)

- P2 + P3: вычленить `core/domain/note_taker_settings/`, перенести Pydantic-схемы туда.
- Версионирование: `settings_revision` колонка + миграция existing data.
- Frontend: генерация TS-типов из Pydantic.

**Acceptance:** `grep -rn "from services.agents.teams.note_taker_settings import" api/src` показывает только runtime/handlers. Schema живёт в `core/domain/`.

### Phase 4 — Module reorg + status enum (1 sprint)

- P4: `JobStatus` enum, использовать везде. Удалить magic strings.
- P2 продолжение: разделить `services/agents/teams/note_taker/` на runtime / handlers / postprocess / files.
- P9: вынести Salesforce side-effect из settings-loader.
- Перенести `note_taker_confluence.py` / `note_taker_salesforce.py` в `services/integrations/`.

**Acceptance:** в `services/agents/teams/note_taker/` только bot-runtime код. Никаких импортов в `services/integrations/` из этой папки.

### Phase 5 — Long tail (по факту)

- P5: единый путь исполнения (URL и upload через taskiq).
- P8: declarative validators через Pydantic (после P3 это почти бесплатно).
- P10: per-provider keyterms contract.
- L1: удалить dead-флаги (`MAGNET_SYNC` если не используется, `personal_config_store` если не используется).

---

## Метрики прогресса

После каждой фазы добавлять короткий отчёт в этот файл (как делается в `CUBE_CSS_ARCHITECTURE_ROADMAP.md`):

```
- **Phase 2 debt reduced:** PgDataStorage now delegates to TranscriptionsService;
  raw-asyncpg call sites in speech_to_text reduced 4 → 0; jsonb-codec race
  surface area shrank to pgvector-only.
```

Audit-метрики, которые стоит добавить в `web/scripts/audit-ds-migration.mjs` (или новый `api/scripts/audit-note-taker.py`):

- `noteTakerRawAsyncpg`: count of `store.client.execute_command|fetchrow` в `speech_to_text/` и `services/agents/teams/`.
- `noteTakerStatusMagicStrings`: count of `"pending"|"running"|"completed"|"failed"|"transcribed"|"rerunning"` строковых литералов вне определения enum.
- `noteTakerCrossModuleImports`: count `from services.agents.teams.note_taker_settings import` из bot-runtime файлов.

Каждая метрика — baseline-guarded (как `legacyLayoutClasses`, `transitionAll` в CUBE roadmap'е).

---

## Out of scope

- Полная миграция фронта на ds-токены (это отдельный track CUBE).
- Refactor LiteLLM провайдеров и `ai_services` слоя.
- Performance: Mistral/ElevenLabs выбор по умолчанию, оптимизация long audio (>30 мин).
- Auth flow Teams-бота: client-id / superuser-id mapping — это Provider-уровень.
- Knowledge Graph / Magnet sync flow — feature-flag, не активно используется.

---

## Appendix A — критические call-graph'ы

### Admin Preview Upload

```
NoteTakerJobsController.run_preview_upload (controller.py:91)
  └─> jobs_service.create(NoteTakerJobCreate)        [advanced-alchemy: note_taker_jobs]
  └─> asyncio.create_task(_run_preview_job_background)
        ├─> note_taker_files._upload_stream_to_object [object storage]
        ├─> _update_preview_job_status('running')    [advanced-alchemy: note_taker_jobs]
        ├─> transcription_service.submit            [STT pipeline]
        │     └─> _run_pipeline_and_cleanup
        │           └─> TranscriptionPipeline.run
        │                 ├─> _stt._transcribe            [provider]
        │                 ├─> _dr.diarize                 [provider]
        │                 ├─> merge_words_and_speakers    [utils/merge.py]
        │                 ├─> _sync_to_magnet (optional)  [knowledge graph]
        │                 ├─> storage.update_transcription [PgDataStorage → raw asyncpg → transcriptions]
        │                 └─> storage.update_status('completed') [PgDataStorage]
        ├─> poll storage.get_status loop (5..30s, timeout 900s)
        ├─> transcription_service.get_transcription  [PgDataStorage.get_meta → raw asyncpg]
        ├─> format_transcript_segments               [note_taker_utils.py]
        ├─> execute_prompt_template(STT_TRANSCRIPT_POSTPROCESSING) [LLM]
        ├─> parse_speaker_mapping_output / parse_suggested_keyterms_from_output [transcript_postprocess.py]
        └─> _update_preview_job_status('transcribed', result={...}) [advanced-alchemy: note_taker_jobs]
```

### Teams Bot Recording Flow

```
Azure Bot Service → POST /teams/note-taker/{provider_system_name}/messages
  └─> handle_note_taker_message_by_name (routes/user/agents.py:620)
        └─> runtime.dispatch(activity)
              └─> note_taker_handlers/messages.py / events.py
                    ├─> note_taker_store.get_meeting_account_info [teams_meeting]
                    ├─> note_taker._load_note_taker_settings_for_context [note_taker_settings]
                    ├─> note_taker._send_stt_recording_to_salesforce (SIDE EFFECT)
                    └─> note_taker_transcription.run_transcription_pipeline
                          └─> [same STT pipeline as Admin Preview]
```

### Continue → Rerun postprocessing

```
NoteTakerJobsController.rerun_postprocessing (controller.py:151)
  └─> note_taker_rerun_bg_task.kiq                  [taskiq queue]
        └─> _rerun_postprocessing_background
              ├─> _update_preview_job_status('rerunning')
              ├─> annotate_transcript_speakers
              ├─> execute_prompt_template(chapters)
              ├─> execute_prompt_template(summary)
              ├─> execute_prompt_template(insights)
              └─> _update_preview_job_status('completed', result={..., postprocessing: {...}})
```

## Appendix B — таблица `transcriptions.transcription` JSONB shape

После `merge_words_and_speakers` и записи через `update_transcription`:

```json
{
  "text": "Full text concatenated by spaces",
  "segments": [
    {
      "start": 0.0,
      "end": 4.32,
      "speaker": "speaker_0",
      "text": "Sentence 1.",
      "chunk_id": null
    },
    ...
  ]
}
```

**Не имеет** ключей: `file_id`, `filename`, `participants`, `speaker_labels`. Эти поля живут в outer META dict (возвращается `get_meta`), не в `transcription` JSONB.

`format_transcript_segments(meta)` корректно различает: вход — META, через `meta.get("transcription")` достаёт inner dict с `segments`. Это работает только если codec расшифровал JSONB → dict, иначе валится в fallthrough на пустой результат (исправлено через `_coerce_jsonb_to_dict`).

## Appendix C — список файлов, потенциально под удаление после рефакторинга

| Файл | После какой фазы | Причина |
|---|---|---|
| `services/agents/teams/note_taker_settings.py` | Phase 3 | Содержимое разнесено в `core/domain/note_taker_settings/` |
| `services/agents/teams/note_taker_pending_store.py` | Phase 6 (если делать) | Заменено advanced-alchemy доменом |
| `speech_to_text/transcription/storage/postgres_storage.py::_update_fields` | Phase 2 | Inline ORM service replaces |
| `services/agents/teams/note_taker_confluence.py` | Phase 4 | Переезд в `services/integrations/confluence/` |
| `services/agents/teams/note_taker_salesforce.py` | Phase 4 | Переезд в `services/integrations/salesforce/` |
| `_MISTRAL_CACHE`, `_ELEVEN_CACHE`, `_RUNNING` (in-memory dicts) | Phase 1 | Если нет реальных consumer-ов |

---

## Резюме

**Ключевая проблема Note Taker — это не STT и не Teams-bot, это организация модулей.** 50+ файлов лежат в одной плоской папке `services/agents/teams/`, смешивая 5 разных concern'ов и пересекаясь импортами. Параллельно две таблицы (`transcriptions`, `note_taker_pending_confirmation`) ходят через сырой asyncpg в `PgVectorClient`, который для них не предназначен — отсюда 3 production-бага подряд за неделю.

**Минимальный путь к стабильности:** Phase 1 (мои фиксы + scheduled cleanup + cache bound) + Phase 2 (transcriptions domain). Это 1-2 спринта работы, и подсистема перестаёт быть «landmine field».

**Долгосрочный путь:** Phase 3-5 — реорганизация модулей по ответственностям, schema-as-source-of-truth, status enum, единый путь исполнения. Это уже не про «стабильность», а про «легко добавить фичу не сломав другую».

Готов начать делать эти slice'ы — начиная с Phase 2 (TranscriptionsService) — после согласования приоритетов.

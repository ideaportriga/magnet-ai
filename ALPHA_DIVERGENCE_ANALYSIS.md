# Анализ изменений в `alpha` после ветвления

**Ваша ветка:** `alpha-taskiq-reka-cube-css`
**База (merge-base с `origin/alpha`):** `76308175`
**Текущий tip `origin/alpha`:** `d4d9c370`
**Дата анализа:** 2026-04-29

## Контекст

Ваша ветка содержит крупную миграцию UI: удаление Quasar, переход на Reka UI / CUBE CSS, рефакторинг паттернов компонентов (`KmListPage`, темы, иконки Phosphor, и т.д.). Это означает, что любые изменения в `alpha`, затрагивающие Quasar-компоненты или старый бутстрап, скорее всего **устарели** в контексте вашей ветки.

## Полный список коммитов на `alpha` после точки расхождения

```
d4d9c370 chore(release): 0.7.0-alpha.18 [skip ci]      ← skip (авторелиз)
4aff1b8e fix: quasar import issue                      ← коммит #1
a25c9ef7 chore(release): 0.7.0-alpha.17 [skip ci]      ← skip (авторелиз)
e628acbe feat(api_keys): improve create form usability ← коммит #2
582fe719 fix(frontend): add detail view for API keys   ← коммит #3
a753fdba fix(frontend): avoid unnecessary requests…    ← коммит #4
```

Итого **4 функциональных коммита** для анализа.

---

## Сводная таблица решений

| # | Коммит | Что делает | Рекомендация | Стоимость |
|---|--------|------------|--------------|-----------|
| 1 | `4aff1b8e` quasar import issue | Чинит regex-парсинг импортов `@quasar/vite-plugin` в `boot/quasar.js` | **Не переносить** (устарело) | — |
| 2 | `e628acbe` api_keys CreateNew UX | `<form @submit>`, autofocus, guard в `create()` | **Перенести вручную** (адаптация под km-* компоненты) | ~10 мин |
| 3 | `582fe719` API keys detail view | Backend GET/PATCH + новый Details.vue + роут + типы | **Бэкенд — перенести**; **фронт — переписать с нуля** | ~30 мин backend + 1–2ч frontend |
| 4 | `a753fdba` unnecessary requests after delete | Точечный фикс инвалидации в `createEntityQueries.ts` | **Перенести как есть** | ~1 мин |

---

## Детальный анализ

### #1 — `4aff1b8e` — fix: quasar import issue

**Файл:** `web/packages/shared/src/lib/boot/quasar.js` (1 файл, +8/-16)

**Что делает:** убирает `//`-комментарии внутри `import {…}` блока Quasar. Плагин `@quasar/vite-plugin` использует regex для перезаписи импортов и ломается на `/` и `*` в скобках — в результате один импорт остаётся «голым» (`dist/quasar.client.js`), а соседние файлы перезаписываются на глубокие пути → две копии плагина → `Notify.create is not a function` в проде.

**Состояние в вашей ветке:**
```bash
$ ls web/packages/shared/src/lib/boot/
componentList.js  globalProperties.js  initDataSource.js  metadata.js
```
Файла `quasar.js` **больше нет** — вы удалили Quasar bootstrap целиком в рамках миграции.

**Рекомендация:** ❌ **НЕ ПЕРЕНОСИТЬ.** Изменение неприменимо: фикс относится к удалённому коду.

**Что сохранить из этого коммита:** только урок на будущее — если где-то ещё используется `@quasar/vite-plugin` (вряд ли, но проверьте `vite.config.*`), помните, что комментарии внутри `import {}` ломают его regex.

---

### #2 — `e628acbe` — feat(api_keys): improve create form usability

**Файл:** `web/apps/@ipr/magnet-admin/src/components/ApiKeys/CreateNew.vue` (1 файл, +14/-12)

**Что делает три полезных мелочи:**
1. Оборачивает форму в `<form @submit.prevent="create">` — Enter в инпуте сабмитит форму.
2. Добавляет `autofocus` на инпут имени.
3. Гард в начале `create()`: `if (!name.value || loading.value) return` — защита от двойных кликов и пустого имени.

**Состояние в вашей ветке (`CreateNew.vue`):** файл уже мигрирован с Pug+Quasar на HTML+`km-*` компоненты:
- `q-dialog` → `km-dialog`
- `q-spinner` → `km-loader`
- классы `q-mb-lg/q-pl-8` → `mb-lg/pl-8` (CUBE)
- Pug → обычный HTML template

Логика `create()` в вашей ветке без guard'а, формы нет, `autofocus` отсутствует.

**Рекомендация:** ✅ **ПЕРЕНЕСТИ ВРУЧНУЮ.** Прямой `git cherry-pick` не сработает (другая разметка). Нужно:

1. Обернуть содержимое блока `step === 0` в `<form @submit.prevent="create">…</form>`.
2. Добавить `autofocus` атрибут на `<km-input ref="nameRef" v-model="name" …>` — **сначала проверьте**, что `km-input` пробрасывает `autofocus` на нативный input (если нет — добавить через `nameRef.value.focus()` в `onMounted` или переключатель watcher по `showNewDialog`).
3. В `create()` добавить первой строкой:
   ```js
   if (!name.value || loading.value) return
   ```

**Риск:** низкий. Чисто UX-улучшение в одном файле.

---

### #3 — `582fe719` — fix(frontend): add detail view for API keys

Самый крупный коммит из четырёх. **6 файлов, +223/-2.** Логически делится на две части — backend и frontend.

#### 3a. Backend (3 файла) — **переносится чисто**

| Файл | Что добавляется |
|------|-----------------|
| `api/src/routes/admin/api_keys.py` | Эндпоинты `GET /{id}` (получить ключ) и `PATCH /{id}` (обновить) |
| `api/src/services/api_keys/services.py` | Функции `get_api_key(id)` и `update_api_key(id, data)` |
| `api/src/services/api_keys/types.py` | Класс `UpdateApiKeyData` + расширение `ApiKeyConfigBase` (`updated_at`, `created_by`, `updated_by`, `notes`, `scopes`) |

**Состояние в вашей ветке:**
- `api_keys.py` — **только** `list`, `create`, `delete`. Нет `get_one`, нет `update`.
- `services.py` — нет `get_api_key`/`update_api_key`.
- `types.py` — `ApiKeyConfigBase` уже содержит `expires_at` и `is_active` (видимо, добавлены ранее), но **нет** `notes`, `created_by`, `updated_by`, `updated_at`, `scopes`. Нет `UpdateApiKeyData`.
- `core/domain/api_keys/schemas.py` уже имеет класс `APIKeyUpdate` — то есть доменный слой готов, не хватает только service-слоя и роута.

**Рекомендация:** ✅ **ПЕРЕНЕСТИ.** Чистый backend-инкремент, не трогает UI. Можно `git checkout 582fe719 -- api/src/routes/admin/api_keys.py api/src/services/api_keys/services.py api/src/services/api_keys/types.py`, **но осторожно** — это перезапишет ваш `types.py`. Лучше скопировать руками:
- Добавить импорты `patch` и `UpdateApiKeyData`/`APIKeyUpdate`.
- Добавить методы `get_api_key`/`update_api_key` в роутер и сервис.
- В `types.py` смержить расширения полей (у вас уже есть `expires_at`/`is_active`, добавьте только новые).

**Риск:** низкий, чистое расширение API.

#### 3b. Frontend (3 файла) — **частично переносится, Details.vue переписать**

| Файл | Что добавляется | Решение |
|------|-----------------|---------|
| `web/apps/@ipr/magnet-admin/src/types/entities.ts` | `is_active`, `expires_at`, `notes` в интерфейс `ApiKey` | ✅ перенести (3 строки) |
| `web/apps/@ipr/magnet-admin/src/router.js` | Роут `/api-keys/:id` → `Details.vue` | ✅ перенести |
| `web/apps/@ipr/magnet-admin/src/components/ApiKeys/Details.vue` | **Новый файл, 151 строка**, Pug + Quasar | ⚠️ **переписать с нуля** |

**Почему Details.vue нельзя перенести как есть:**
- Использует Pug-синтаксис (вы перешли на обычный HTML template).
- `q-tooltip`, `q-toggle`, `q-menu`, `q-item`, `q-item-section`, `q-btn` — Quasar-компоненты, в вашей ветке заменены на `km-*` или удалены.
- `layouts-details-layout`, `km-popup-confirm`, `km-input-flat` — проверьте наличие/совместимость в вашей ветке.
- Композабл `useEntityDetail` уже есть в вашей ветке (✅ `composables/useEntityDetail.ts`), так что логика API/состояния переносима.
- Класс `q-mb-md`, `q-pl-6`, `q-pa-sm` — старые legacy-классы Quasar, в вашей ветке заменены CUBE-классами.

**Рекомендация:**
1. Перенести `entities.ts` (3 строки) — ✅ безопасно.
2. Перенести `router.js` (10 строк) — ✅ безопасно.
3. Details.vue — **написать заново**, опираясь на:
   - Логику из `Details.vue` оригинала (composables, поля, save/delete handlers).
   - UI-конвенции вашей ветки: посмотрите соседний detail-view, например `KmListPage`-страницы или другой Details.vue, где уже применён CUBE + km-компоненты.

**Стоимость:** backend ~30 мин (механическая работа), Details.vue ~1–2 часа в зависимости от того, насколько готов набор `km-*` компонентов (toggle, menu, tooltip, popup-confirm).

---

### #4 — `a753fdba` — fix(frontend): avoid unnecessary requests after entity deletion

**Файл:** `web/apps/@ipr/magnet-admin/src/queries/createEntityQueries.ts` (1 файл, +3/-2)

**Что делает:** В `useRemove.onSuccess` меняет:
```ts
// Было:
onSuccess: () => {
  qc.invalidateQueries({ queryKey: keys.all })  // это перезагрузит и detail удалённой сущности → 404
  qc.invalidateQueries({ queryKey: ['catalog'] })
}
// Стало:
onSuccess: (_, id) => {
  qc.removeQueries({ queryKey: keys.detail(id) })  // выкинуть из кэша detail
  qc.invalidateQueries({ queryKey: keys.lists() }) // обновить только списки
  qc.invalidateQueries({ queryKey: ['catalog'] })
}
```

**Состояние в вашей ветке:** содержит **СТАРЫЙ** код (`invalidateQueries({ queryKey: keys.all })`). Подтверждено чтением `createEntityQueries.ts:117–125`.

**Рекомендация:** ✅ **ПЕРЕНЕСТИ КАК ЕСТЬ.** Изменение точечное, не зависит от UI-миграции, и реально полезное (после удаления сущности с открытой detail-страницы старый код делал лишний запрос на 404).

**Способ:** `git cherry-pick a753fdba` — должен пройти чисто (или 1-минутная ручная замена по diff'у выше).

**Риск:** очень низкий. Локальное изменение в одном хуке React Query.

---

## Рекомендуемый порядок переноса

Если решите переносить, я бы шёл от самого безопасного к самому затратному:

1. **`a753fdba`** (1 мин) — `cherry-pick`, точечный фикс инвалидации.
2. **`e628acbe`** (10 мин) — UX-доработки CreateNew.vue (form/autofocus/guard).
3. **`582fe719` backend** (~30 мин) — get/update эндпоинты + сервисы + типы.
4. **`582fe719` frontend types + router** (~5 мин) — типы и роут.
5. **`582fe719` Details.vue** (~1–2 ч) — переписать в стиле вашей ветки. Можно отложить — функционал не блокирующий, у вас сейчас нет детального просмотра API keys.
6. **`4aff1b8e`** — пропустить.

## Что НЕ нужно переносить и почему

- **`4aff1b8e`** — относится к файлу `boot/quasar.js`, который вы удалили в рамках миграции. Любая попытка применить = воссоздать удалённый код.
- **Авторелизные коммиты** `d4d9c370`, `a25c9ef7` — генерируются CI при релизе alpha. Не трогать.

## Что проверить дополнительно перед переносом

- Перед переносом frontend Details.vue: убедиться, что в вашей ветке **уже существуют** `km-popup-confirm`, `km-input-flat`, `layouts-details-layout` (или их эквиваленты после миграции).
- Перед переносом backend `update_api_key`: пройтись по диффу `core/domain/api_keys/schemas.py` — убедиться, что поля `notes`, `scopes`, `created_by`, `updated_by` присутствуют в доменной модели. Если нет — нужна доп. миграция БД либо урезать набор полей в `UpdateApiKeyData` до тех, что реально есть.
- При переносе `entities.ts`: проверить, что вы не удалили эти поля сознательно.

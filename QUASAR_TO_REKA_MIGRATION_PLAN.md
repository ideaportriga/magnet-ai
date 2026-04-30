# План миграции `magnet-admin`: Quasar → Reka UI + CUBE CSS

> **Статус:** Phase 1 in progress
> **Автор анализа:** Claude (assistant)
> **Дата:** 2026-04-25
> **Уточнение:** GitHub Copilot audit, 2026-04-25, branch `alpha-taskiq-reka-cube-css`
> **Целевое приложение:** `web/apps/@ipr/magnet-admin`
> **Связанные пакеты:** `web/packages/ui-comp`, `web/packages/themes`, `web/packages/shared`, `web/packages/ds` (новый)

---

## 0.1. Phase 0 — зафиксированные решения

В рамках auto-mode реализации сделаны следующие допущения. Каждое можно
отменить, но это будет означать переделку Foundation phase.

| Вопрос | Решение | Обоснование |
|---|---|---|
| **Scope миграции** | **Полное удаление Quasar из обоих apps + всех общих пакетов** (`@ui-comp`, `@shared`, `@themes`). Решение пересмотрено перед Phase 4 (см. §0.3). | Цель — полностью избавиться от Quasar в проекте. Сделать постепенными PR-волнами с 4-x шагов. |
| **Префикс компонентов** | `km-*` — без изменений. | Нулевой риск для 388 .vue потребителей, codemod проще. |
| **Префикс CSS variables** | `--ds-*` для всего нового; `--q-*` остаются как **временные deprecated alias'ы** в `@ds/tokens/_compat-q-aliases.css`. Удаляются в Phase 5 после очистки `var(--q-*)` в admin scope. | Не ломает legacy CSS (themes/Stylus, ui-comp) во время поэтапного cutover. |
| **Локация нового пакета** | `web/packages/ds/` рядом с `@ui-comp`/`@themes`. tsconfig aliases: `@ds`, `@ds/styles`, `@ds/tokens`, `@ds/composition`, `@ds/utilities`, `@ds/reset`, `@ds/*`. | Нет дисраптива для panel; alias-уровневое переключение возможно позже. |
| **CSS resolution** | Path‑aliases указывают на `.ts`-шимы (`tokens/index.ts → import './index.css'`). | `nxViteTsPaths` стабильно резолвит TS, Vite дальше сам обрабатывает `.css`. |
| **Шаблоны новых компонентов** | Plain Vue `<template>` (не Pug). | Стандарт экосистемы Reka; меньше зависимостей; читается легче. |
| **Стили новых компонентов** | Plain CSS с CSS variables. Stylus/Sass только для legacy. | Никаких новых препроцессоров для DS; токены уже в `:root`. |
| **Иконки** | unplugin-icons + `@iconify-json/*` в Phase 2. FA v5 → v6 миграция через codemod `fas fa-times` → `fa6-solid:xmark`. | Tree-shake вместо ~80 KB FA шрифтов; current `IconPicker` мигрируется один раз. |
| **`useNotify` API** | Source of truth — `@ds/composables/useNotify`; `@shared/utils/notify` становится re-export'ом. Сигнатура остаётся API-совместимой. | 33 файла уже используют composable, сигнатура не меняется. |
| **`@ds` reset** | НЕ подключается одновременно с Quasar. Только в Phase 5 после удаления `quasar/src/css/index.sass`. | Reset перепишет body/`*` стили — конфликт с Quasar reset. |
| **Brand темы** | `default` мигрируется в Phase 1; `salesforce`/`siebel` — в Phase 6. | Изоляция риска: основная тема стабилизируется первой. |
| **Storybook / Histoire** | Опционально, после Phase 3. Не блокирует миграцию. | Можно работать через `magnet-admin` smoke + unit тесты. |

Если кто-то из команды хочет изменить эти решения — фиксируется в Open
questions §11 и Phase 1 переделывается до перехода к Phase 2.

---

## 0.3. Phase 4 redesign — полное удаление Quasar

После завершения Phase 3.5 был принят следующий пересмотр стратегии:
**убрать Quasar полностью** из проекта, включая `magnet-panel` и общие
пакеты `@ui-comp`, `@shared`, `@themes`. Phase 4 разбита на 9 шагов в 6
PR-волн для управляемости.

### Inventory (на старт Phase 4)

| Зона | Файлов | q-tokens | Quasar imports | Особенности |
|---|---|---|---|---|
| `magnet-admin/src` | 388 .vue | 308 `<q-*>` + 659 `q-pa-*` utility | 22 файла | основной |
| `magnet-panel/src` | 22 .vue | ~310 q-tokens (Pug!) | 4 файла | Pug‑шаблоны, нет Cypress |
| `@ui-comp/components/base/` | 50 .vue | (legacy) | 0 после Phase 3 | удаляем все |
| `@ui-comp/components/{Agent,auth,Retrieval,Search,user}/` | 19 .vue | 299 q-tokens | 2× `copyToClipboard`, 1× type-only `QMenu/QPopupEdit` | mixed consumers |
| `@shared/lib/boot/quasar.js` | 1 | — | exports `quasarConf` для `app.use(Quasar, ...)` | используют оба apps |
| `@shared/lib/utils/notify.ts` | 1 | — | `Quasar.Notify.create(...)` | 38+ потребителей |
| `@themes/base/factory.styl` | 1 | — | — | генерирует `q-pa-*`, `bg-*`, `text-*` (конкурент `@ds/utilities`) |
| `@themes/base/quasar_overrides.styl` | 1 | — | — | 170 строк CSS-патчей Quasar |
| `@themes/utils/loadFonts.js` | 1 | — | `@quasar/extras/material-icons/...` | загрузка Material Icons |

### Reorganization non-base `@ui-comp`

Перед переписыванием — переезд по правильным местам:

| Папка | Кто использует | Решение |
|---|---|---|
| `Agent/` (Message, Confirmation) | admin + panel | оставить в `@ui-comp` |
| `auth/*` (Login, Signup, ForgotPassword) | только admin | **переехать в `magnet-admin/src/components/Auth/`** |
| `Retrieval/Prompt`, `Retrieval/Answer` | admin + panel | оставить в `@ui-comp` |
| `Retrieval/MetadataFilter*` (5 файлов) | только admin | **переехать в `magnet-admin/src/components/KnowledgeGraph/`** |
| `Search/*` (4 файла) | admin + panel | оставить в `@ui-comp` |
| `user/UserMenu` | admin + panel | оставить в `@ui-comp` |
| `user/UserProfilePage`, `user/UserSecurityPage` | только admin | **переехать в `magnet-admin/src/components/Profile/`** |

После reorg в `@ui-comp/src/components/` остаются 9 общих компонентов
(`Agent/2`, `Retrieval/2`, `Search/4`, `user/UserMenu`).

### Bridge архитектура `@ui-comp` (после Phase 4d)

```ts
// @ui-comp/src/index.ts
export * from '@ds/components/domain'
import KmInstall from './utils/install'
export default KmInstall
```

```ts
// @ui-comp/src/utils/install.ts (переписан с явных импортов)
import * as kmComponents from '@ds/components/domain'
import AgentMessage from '../components/Agent/Message.vue'
// ...

export default {
  install(app) {
    for (const [name, component] of Object.entries(kmComponents)) {
      app.component(toKebab(name), component)  // KmBtn → km-btn
    }
    app.component('agent-message', AgentMessage)
    // ...9 явных регистраций общих компонентов
  },
}
```

`import.meta.glob` → явные импорты: надёжный tree-shake, нет неожиданных
регистраций, проще удалить компоненты в будущем.

### 9 шагов Phase 4

| Шаг | Действие | Какие файлы | PR |
|---|---|---|---|
| **4a** | Подключить `<DsToastHost>`/`<DsDialogHost>`/`<DsLoadingHost>` в `App.vue` обоих apps | `magnet-admin/src/App.vue`, `magnet-panel/src/App.vue` | PR 1 |
| **4b** | `@shared/utils/notify.ts` → re-export `@ds/composables/useNotify` | `@shared/lib/utils/notify.ts` | PR 1 |
| **4c** | Reorganize non-base `@ui-comp`: переезд + переписать на `@ds`. Pug → plain templates везде. Type-import `QMenu` заменить на native/Reka типы. | 19 файлов | PR 2 |
| **4d** | `@ui-comp/index.ts` → re-export `Km*` from `@ds`. Plugin install через явные импорты. Удаление 50 legacy `base/*.vue`. | `@ui-comp/src/index.ts`, `@ui-comp/src/utils/install.ts`, `@ui-comp/src/components/base/*` | PR 3 |
| **4e** | Codemod q-utility classes → @ds utilities на admin + panel + `@ui-comp` остатки. ~750 замен. | все .vue/.ts/.js | PR 4 |
| **4f** | **Сначала ручная конвертация Pug → plain templates в panel** (22 файла). Затем codemod прямых `<q-*>` тегов в обоих apps. `useQuasar()` → `useDialog`/`useNotify`. `v-close-popup` (32) → handlers. | admin (308 / 62), panel (310 / 22) | PR 4 |
| **4g** | `@themes` migration: удалить `factory.styl`, `quasar_overrides.styl`. `loadFonts.js` без `@quasar/extras` (Material Symbols через CSS @import). `loadTheme()` → `useTheme()` от `@ds`. Brand themes на CSS variables через `[data-brand]`. | `@themes/src/**` | PR 5 |
| **4h** | `main.js`: убрать `import { Quasar }`, `app.use(Quasar, quasarConf)`, `'quasar/src/css/index.sass'` в обоих apps. `vite.config.ts`: убрать `@quasar/vite-plugin`, manual chunk. Удалить `quasar-variables.sass`. | `main.js`, `vite.config.ts` обоих apps | PR 6 |
| **4i** | `web/package.json`: drop `quasar`, `@quasar/extras`, `@quasar/vite-plugin`, `@prettier/plugin-pug`, `pug`, `pug-plain-loader`, `sass-embedded`. Удалить `@shared/boot/quasar.js`, `quasarConf` exports. ESLint правило `no-restricted-imports` для `from 'quasar'` глобально. Удалить временные `--q-*` aliases из `@ds/tokens`. | `web/package.json`, `@shared/lib/boot/quasar.js`, `@shared/index.ts`, `@ds/tokens/_compat-q-aliases.css`, `eslint.config.mjs` | PR 6 |

### Риски Phase 4

| Риск | Митигация |
|---|---|
| Pug-codemod в panel сложный | **Сначала ручная конвертация Pug → plain templates** (22 файла, 1–2 дня), затем общий codemod на plain |
| `magnet-panel` без Cypress regression suite | Скриншот-тесты до/после, ручной smoke по основным flows (chat/retrieval/search/agent) |
| Brand themes (default/salesforce/siebel) сломаются | Покрыть все 3 темы в smoke после Phase 4g |
| Material Icons font после `@quasar/extras` удаления | CSS `@import` Material Symbols либо скачать локально |
| `:deep(.q-*)`, `var(--q-*)` в CSS scoped | Отдельный grep pass после codemod, отдельная очистка |
| `MetadataFilterEditor.vue` имеет `import type { QMenu, QPopupEdit }` | Заменить на native HTMLElement type или Reka `MenuRoot` types |
| Множество компонентов в `@ui-comp` зарегистрированы глобально через `import.meta.glob` | Замена на явные `app.component()` вызовы — безопаснее, видимее, проще debug |

### Critical path (порядок жёсткий)

`4a → 4b → 4c → 4d → 4e → 4f → 4g → 4h → 4i`

Только PR 1 (4a+4b) и PR 6 (4h+4i) могут идти параллельно с другими — но
оба нуждаются в обязательном предыдущем merge'е.

---

## 0.2. Прогресс по фазам

| Фаза | Статус | Артефакт |
|---|---|---|
| Phase 0 — Decisions & Spike | ✅ Решения зафиксированы выше; spike отложен (см. Phase 1) | этот раздел |
| Phase 1 — Foundation: токены и CUBE CSS | ✅ Готово | `web/packages/ds/` со структурой токенов, composition, utilities; alias в tsconfig; подключение в admin `main.js`; Vite build зелёный |
| Phase 2 — Primitives layer | ✅ Готово | reka-ui+@vueuse/core+@internationalized/date установлены; 16 Reka UI primitives (Dialog/AlertDialog/Tooltip/DropdownMenu/Popover/Switch/Checkbox/RadioGroup/Slider/Progress/Separator/Tabs/Accordion/Select/ScrollArea/Avatar); composables (useNotify/useDialog/useLoading/useScreen/useDarkMode/useElementSize/useScrollObserver); hosts (DsToastHost/DsDialogHost/DsLoadingHost) с promise-based programmatic API; `@ds/compat/quasar` (copyToClipboard/uid/openURL/date/colors) для codemod-friendly drop-in. Iconify отложен до Phase 3 вместе с KmIcon. |
| Phase 3 — Domain layer (Km*) | ✅ Готово (Phase 3 + 3.5) | **51 Km*-компонент** в `@ds/components/domain` с drop-in compatible API. **Wave 1 (foundation, 12):** KmIcon, KmGlyph, KmSeparator, KmTooltip, KmAvatar, KmCard, KmEmptyState, KmLoader, KmInnerLoading, KmBadge, KmChip, KmNotificationText. **Wave 2 (buttons, 5):** KmBtn (полный variant matrix + dropdown), KmIconBtn, KmBtnLoader, KmBtnExpandDown, KmNavBtn. **Wave 3 (simple forms, 4):** KmCheckbox, KmSwitch (segmented), KmToggle, KmSlider. **Wave 4 (overlays, 3):** KmPopupConfirm, KmConfirmAction, KmErrorDialog. **Wave 5 (complex forms, 8):** KmInput, KmInputFlat, KmSelect (multi+search+selectAll, Reka Combobox), KmSelectFlat, KmTabs+KmTab (slot+items dual API), KmFilePicker (drag-drop), KmChipsInput. **Wave 6 (layout/nav, 8):** KmSection, KmBackground, KmNavSection, KmDrawer, KmDrawerLayout (с persistent useDrawerResize), KmDrawerResizeHandle, KmStepper, KmFilterBar. **Wave 7 (misc, 5):** KmImage, KmScore, KmSliderCard, KmChipCopy (copy+toast), KmLocaleSwitcher. Все используют `@shared/composables/useValidation` для совместимости с legacy `:rules`. **Phase 3.5 (9 шт):** KmInputListAdd (per-row validation), KmMarkdown (markdown-it stack 1:1), KmJsonEditor (vanilla-jsoneditor), KmCodemirror (vue-codemirror + json/python langs + useValidation), KmPicker (Reka Popover + 2-col + search), KmIconPicker (DsDialog + FA grid + paginate), KmDate (Reka Calendar + Luxon↔CalendarDate adapter, легаси `@update:date(DateTime)` API), KmRange (двойной KmDate + shortcuts), KmDataTable (TanStack Table 1:1, q-* всё заменено на DsProgress/KmBtn/KmGlyph/KmLoader/KmSelect). **Iconify rewrite — отдельный workstream после первого cutover.** |
| Phase 4 — Cutover | 🟡 4a–4d готовы; 4e–4i остались | См. §0.4 ниже — детальная разбивка по подфазам со статусом. |
| Phase 5 — Удаление Quasar (deps + plugin) | ⏳ Ожидает | Зависит от Phase 4e–4h. |
| Phase 6 — Cleanup и документация | ⏳ Ожидает | brand themes на CSS variables, Storybook, README, panel scope final state. |

---

## 0.4 — Что реально осталось до полного отказа от Quasar

> Аудит выполнен на HEAD `58c29158 fix: pr3 delete quasar components`, working tree чист.

### ✅ Что уже сделано

| Раздел | Состояние | Артефакты |
|---|---|---|
| **`@ds` пакет** | ✅ 100% | 73 `.vue` (54 domain Km* + 18 primitives), 9 composables, 3 hosts, 1617 строк CSS (10 tokens / 7 composition / 6 utilities / reset) |
| **Reka UI primitives** | ✅ 15/15 | Dialog, AlertDialog, Tooltip, DropdownMenu, Popover, Tabs, Accordion, Select, Switch, Checkbox, RadioGroup, Slider, Progress, Separator, Avatar, ScrollArea |
| **CUBE CSS layers** | ✅ 100% | composition (stack/cluster/sidebar/switcher/center/flow/frame), utilities (spacing/color/typography/radius/shadow/layout). 90+ usage в шаблонах. `data-state`/`data-variant` exceptions используются в KmStepper/KmPicker/KmSwitch/KmSelect |
| **Phase 4a — hosts mounted** | ✅ | `<DsToastHost>`/`<DsDialogHost>`/`<DsLoadingHost>` в `App.vue` admin и panel |
| **Phase 4b — notify rewire** | ✅ | `@shared/utils/notify.ts` re-export'ит `@ds/composables/useNotify` |
| **Phase 4c — non-base @ui-comp** | ✅ | 14 shared (Agent×2, auth×3, Retrieval×2, Search×4, user×3) + 5 MetadataFilter* перенесены в admin |
| **Phase 4d — `@ui-comp` bridge** | ✅ | `index.ts` re-export'ит Km* from `@ds`; 50 legacy `base/*.vue` удалены; `install.ts` со static imports |
| **`reka-ui`, `@vueuse/core`, `@internationalized/date`** в deps | ✅ | в `web/package.json` |
| **`@ds/compat/quasar.ts`** утилиты | ✅ | `copyToClipboard`, `uid`, `openURL`, `date`, `colors` без Quasar runtime |

### Подфазы — статус

| # | Подфаза | Что делать | Статус |
|---|---|---|---|
| 1 | **4e** | Codemod `q-pa-*`/`q-px-*`/…/`q-gutter-*` → `@ds/utilities` (`p-md`, `px-sm`, `gap-md`, …). 698 совпадений + numeric scale через `@ds/utilities/legacy.css` | ✅ |
| 2 | **4f-pug** | Конвертация `<template lang="pug">` → plain Vue templates | ✅ |
| 3 | **4f-tags** | Замена `<q-*>` тэгов на Km*/`@ds` primitives | ✅ |
| 4 | **4f-runtime** | `$q.loading` → `useLoading()`; `v-close-popup`/`v-ripple` удалены; `import { … } from 'quasar'` → `@ds/compat/quasar` (29 импортов) | ✅ |
| 5 | **4g-shared** | `@shared/lib/boot/quasar.js` удалён; `quasarConf` экспорт убран из `@shared/index.ts` | ✅ |
| 6 | **4g-themes** | `factory.styl` + `quasar_overrides.styl` удалены; `app.styl` очищен от orphan `.q-drawer`/`[id^=q-portal--]` selectors; `quasar-variables.sass` удалён; `_colors.styl` теперь эмитит `--ds-color-*` напрямую (через переписанный `functions.styl`); brand-themes (salesforce/siebel) переведены на `--ds-color-*` overrides | ✅ |
| 7 | **4h-plugin** | `app.use(Quasar)`, `import 'quasar/src/css/index.sass'`, `@quasar/vite-plugin`, `manualChunks.quasar`, `sassVariables`, `transformAssetUrls` — всё убрано из admin + panel `main.js` + `vite.config.ts`. `@ds/reset` подключён вместо Quasar reset. | ✅ |
| 8 | **4h-fa-icons** | `KmIconPicker.vue` импортирует vendored `fa-v5-icons.json` (1611 имён, 28 кБ) вместо `@quasar/extras/fontawesome-v5/icons.json`. `loadFonts.js` грузит Material Icons через Google Fonts CDN (`fonts.googleapis.com/icon?family=Material+Icons`). | ✅ |
| 9 | **4i-deps** | `quasar`, `@quasar/vite-plugin`, `@quasar/extras`, `@prettier/plugin-pug` убраны из `web/package.json`; lockfile обновлён; `node_modules/@quasar` отсутствует | ✅ |
| 10 | **4i-eslint** | `no-restricted-imports` для `'quasar'` и `'quasar/*'` в корневом `eslint.config.mjs` | ✅ |
| 11 | **4i-tokens-cleanup** | ~700 `var(--q-*)` → `var(--ds-color-*)` (плюс special cases: `--q-negative` → `--ds-color-error`, `--q-question_answered`/`--q-no_results` underscore→hyphen). `_compat-q-aliases.css` удалён. | ✅ |
| 12 | **5/6** | README в `@ds`. Финальный smoke + Cypress. Brand themes уже на CSS variables (см. 4g-themes), но требуется визуальная проверка `[data-brand=salesforce]` / `[data-brand=siebel]`. | ⏳ |

### Phase 4 — CUBE CSS layout migration (Slices)

Отдельный workstream: замена Quasar layout primitives (`row`/`column`/`col-*`/`no-wrap`/`gap-*`) на CUBE composition (`.stack`/`.cluster`).

| Slice | Описание | Статус | Коммит |
|---|---|---|---|
| **A — App shell** | `LayoutDefault.vue`, `Toolbar.vue`, `WorkspaceTabBar.vue`, `LayoutTab.vue` | ✅ | `f9e61aab` |
| **B — Forms & Dialogs** | 12 файлов: FeedbackModal×2, ErrorDialog, Jobs/Drawer, Jobs/CreateNew, Collections/CreateNew, Collections/Drawer, Collections/DrawerChunk, Prompts/Drawer, Retrieval/Drawer, EvaluationSets/Drawer, AssistantTools/Drawer | ✅ | `f9377a70` |
| **C — Tables & Lists** | KmDataTable usage pages, list pages, pagination | ⏳ | — |
| **D — KnowledgeGraph** | Graph UI components | ⏳ | — |
| **E — Conversation & Search** | Conversation, Search, Retrieval, Agent Workflows | ⏳ | — |
| **F — Dashboard & CRUD** | Dashboard, remaining CRUD pages | ⏳ | — |

### 🎉 Quasar полностью удалён

Все три пакета `quasar`, `@quasar/extras`, `@quasar/vite-plugin` отсутствуют в `package.json` и в `node_modules`. ESLint блокирует `import … from 'quasar'`. `nx run magnet-admin:build` и `nx run magnet-panel:build` собираются зелёными без `quasar` runtime в bundle.

Остаются только Phase 5/6 (документация, smoke-тесты, валидация brand themes).

### Критический путь

```
4e (codemod utility) ─┐
4f-pug (Pug→plain) ───┼─→ 4f-tags (q-* → Km*) ─→ 4f-runtime ($q + v-close-popup) ─→ 4h (plugin) ─→ 4i (deps)
4g-themes ────────────┘                                                                            ↓
                                                                                              5/6 cleanup
```

4e и 4f-pug — независимы, можно параллельно. 4g-themes тоже независимо. Остальное последовательно.

### Стратегические заметки

- **Pug → plain — самый объёмный шаг (342 файла)**. Можно сохранить Pug если решим оставить `pug` плагин, но user стейт-смент «полноценно отказаться от Quasar и переделать на CUBE CSS + Reka UI» подразумевает чистый Vue-stack без Pug-зависимости. Делаем conversion.
- **4f-tags — нельзя через простой sed** для overlay-тэгов (`q-dialog`, `q-menu`, `q-tabs`, `q-popup-edit`) — у них API сильно отличаются от Reka. Нужна аккуратная замена пер-файл, желательно через subagent с чётким маппингом.
- **Никаких compat-stubs для Q-компонентов**. Заменять напрямую на Reka (`<DsDialog>`, `<DsDropdownMenu>`, `<KmTabs>`) и адаптировать `v-model`/слоты.
- **Закрытие popup/dialog** через явные handlers (`@click="open = false"`), а не `v-close-popup`. Reka использует controlled state.

---

---

## 0. TL;DR

`magnet-admin` уже имеет **четкий слой абстракции** над Quasar в виде пакета `@ui-comp` (50+ компонентов‑обёрток `km-btn`, `km-input`, `km-dialog`, …) и пакета `@themes` с дизайн‑токенами в Stylus. Это превращает миграцию из «переписать 388 .vue файлов» в задачу **«переписать ≈50 wrapper'ов, перевести токены на CSS custom properties и заменить прямые обращения к Q‑компонентам»**. В текущей ветке быстрый audit нашёл **минимум 493 `<q-*` в 68 файлах** только для HTML‑синтаксиса; Pug‑шаблоны, CSS‑селекторы и utility‑классы нужно считать отдельным скриптом перед стартом.

Стратегия:

1. **Параллельная установка** Reka UI и Quasar — собираем новую дизайн‑систему `@ds` в отдельном пакете, не трогая существующий `@ui-comp`.
2. **Cube CSS как методология** для глобального CSS: `composition` (макеты), `utility` (классы из токенов), `block` (Vue компоненты), `exception` (data‑атрибуты для вариаций).
3. **Перепись токенов**: Stylus `$colors / $spacing / $typography` → плоский набор CSS variables в `:root[data-theme]`.
4. **Поэтапная замена**: сначала добавляем `@ds` рядом с `@ui`, затем включаем новую реализацию только в `magnet-admin`; глобальный re-export `@ui-comp → @ds` делаем только после решения по `magnet-panel`.
5. **Compatibility API только как временный мост**: `useNotify`, clipboard, dialog/loading, theme loader, `v-close-popup`, `v-ripple`, scroll/resize observers закрываем адаптерами, но не превращаем их в финальный публичный стиль новой DS.
6. **Финальная архитектура — CUBE CSS + Reka UI, без Quasar‑паттернов**: никаких `q-*`, `--q-*`, Quasar prop vocabulary как основного API, `$q` или мышления через global plugin.
7. **Окончательное удаление Quasar** в самом конце, когда `grep -r "quasar"` чист в выбранном scope (`admin` alone или `admin+panel`) и CI проверяет запрет новых Quasar‑импортов.

**Оценка по объёму работ:** 8–12 недель для одного фронтенд‑инженера полной занятости, 5–7 недель парой. Можно резать на мелкие итерации, потому что Quasar и Reka UI мирно сосуществуют в Vue 3 (никаких глобальных конфликтов имён компонентов: Reka — это `<DialogRoot>`, Quasar — `<q-dialog>`).

**Архитектурная цель:** миграция считается успешной не тогда, когда Quasar просто спрятан за wrapper'ами, а когда приложение мыслит новой системой: Reka отвечает за accessibility/поведение, CUBE CSS — за layout/style/state, а Quasar compatibility остаётся только в удаляемом переходном слое.

---

## 1. Текущее состояние `magnet-admin`

### 1.1 Объём кода и зависимости

| Метрика | Значение |
|---|---|
| `.vue` файлов в `magnet-admin/src` | **388** |
| `.vue` файлов в `magnet-panel/src` | **22** |
| Файлов с прямым `<q-*` в `magnet-admin/src` + `ui-comp/src` | **минимум 68** (только HTML‑template grep) |
| Прямых `<q-*` в `magnet-admin/src` + `ui-comp/src` | **минимум 493** (только HTML‑template grep) |
| Импортов из `'quasar'` в `magnet-admin/src` | **22 файла** |
| Импортов из `'quasar'` в `ui-comp/src` / `shared/src` | **5 / 2 файла** |
| Импортов из `'quasar'` в `magnet-panel/src` | **4 файла** |
| Использований `useQuasar()` | **5 файлов / 10 упоминаний** в `magnet-admin/src` |
| Использований кастомного `useNotify()` | **33 файла / 97 упоминаний** в `magnet-admin/src` |
| Использований директивы `v-close-popup` | **35** в `magnet-admin/src` + `ui-comp/src`, **4** в `magnet-panel/src` |
| Использований директивы `v-ripple` | **5** в `magnet-admin/src` + `ui-comp/src` |
| `q-scroll-area` / `QScrollArea` | **17** в `admin/ui/shared`, **2** в `panel` |
| Quasar utility‑классов (`q-pa-*`, `q-gutter-*`, …) | **659** упоминаний в исходном инвентаре; нужно обновить скриптом |
| Cypress тестов с `.q-*` селекторами | 6 типов селекторов в ≈10 файлах |
| Иконки FontAwesome v5 (`fas`/`fab`/`far`) | **342** упоминания в исходном инвентаре; нужно обновить скриптом |
| Версия Quasar | `^2.17.7` |

> Audit note: текущие счетчики получены быстрым `find`/`grep` без build/cache folders. Они намеренно помечены как lower bound: Pug‑шаблоны (`template lang="pug"`) не всегда видны через `<q-*`, а CSS `:deep(.q-*)` и `var(--q-*)` нужно считать отдельно.

### 1.2 Архитектурные точки интеграции Quasar

1. **Vite plugin** — `web/apps/@ipr/magnet-admin/vite.config.ts:14,21-23`
   ```ts
   import { quasar, transformAssetUrls } from '@quasar/vite-plugin'
   quasar({ sassVariables: '@/styles/quasar-variables.sass' })
   ```
2. **Manual chunk** — `vite.config.ts:51` `manualChunks.quasar = ['quasar', '@quasar/extras']`.
3. **SASS переменные** — `web/apps/@ipr/magnet-admin/src/styles/quasar-variables.sass` (8 базовых цветов).
4. **Глобальная установка** — `src/main.js:7-9, 53` — `import 'quasar/src/css/index.sass'`, `app.use(Quasar, quasarConf)`.
5. **Boot конфиг** — `web/packages/shared/src/lib/boot/quasar.js` экспортирует 32 компонента, 3 плагина (`Notify`, `Loading`, `Dialog`), 1 директиву (`ClosePopup`), `Notify.setDefaults({ position: 'bottom-right' })`.

`magnet-panel` не является гипотетическим риском: `web/apps/@ipr/magnet-panel/src/main.js` также импортирует `Quasar`, `quasarConf`, `quasar/src/css/index.sass` и устанавливает `@ui`. Его `vite.config.ts` содержит `@quasar/vite-plugin` и `manualChunks.quasar`. Поэтому удаление Quasar из `web/package.json`, `@shared` или `@ui` возможно только после явного решения: мигрируем panel вместе с admin или изолируем legacy `@ui` для panel.

### 1.3 Существующая «дизайн‑система» проекта (важная находка)

Это **главный фактор**, упрощающий миграцию.

#### `web/packages/ui-comp` — слой компонентов‑обёрток

50 компонентов в `src/components/base/`, регистрируются глобально с префиксом `km-`:

| Категория | Компоненты |
|---|---|
| Кнопки | `Btn`, `BtnExpandDown`, `BtnLoader`, `IconBtn`, `NavBtn` |
| Формы | `Input`, `InputFlat`, `InputListAdd`, `Select`, `SelectFlat`, `Checkbox`, `Switch`, `Toggle`, `Range`, `Slider`, `SliderCard`, `Date`, `Picker`, `IconPicker`, `FilePicker`, `ChipsInput` |
| Layout | `Section`, `Drawer`, `DrawerLayout`, `Card`, `Background`, `Separator`, `NavSection` |
| Overlays | `PopupConfirm`, `ConfirmAction`, `ErrorDialog`, `Tooltip` |
| Feedback | `Loader`, `BtnLoader`, `InnerLoading`, `EmptyState`, `NotificationText`, `Score` |
| Data | `DataTable` (на TanStack Vue Table), `Markdown`, `JsonEditor`, `Codemirror`, `Image`, `Icon`, `Chip`, `ChipCopy` |
| Navigation | `Tabs`, `Stepper`, `FilterBar` |
| Locale | `LocaleSwitcher` |

> Большинство потребителей используют `<km-btn>`, `<km-input>`, `<km-dialog>` — Quasar внутри них **скрыт от приложения**. Это даёт нам возможность **переписать внутренности `@ui-comp` без изменения публичного API**.

Важно: `web/packages/ui-comp/src/utils/install.ts` регистрирует компоненты через `import.meta.glob('../components/**/*.vue', { eager: true })`, а не только через named exports из `index.ts`. Поэтому strategy “просто заменить `index.ts` на `export * from '@ds'`” недостаточна: нужно сохранить default Vue plugin install API и контролировать, какое приложение получает legacy или DS‑реализацию.

#### `web/packages/themes` — пакет токенов и тем

```
themes/src/
├── base/
│   ├── tokens/
│   │   ├── _colors.styl       ← brand, text, borders, controls, buttons, semantic, statuses
│   │   ├── _spacing.styl
│   │   ├── _typography.styl
│   │   ├── _radii.styl
│   │   ├── _elevation.styl
│   │   └── _components.styl
│   ├── factory.styl           ← генерирует utility‑классы
│   ├── functions.styl
│   ├── typography.styl
│   ├── utilities.styl
│   ├── quasar_overrides.styl  ← removed in plan
│   └── openui_overrides.styl
└── themes/
    ├── default/
    ├── salesforce/
    └── siebel/
```

Уже есть архитектура «один источник правды → CSS custom properties с префиксом `--q-*`» (см. `_colors.styl:1-7` — комментарий `All values are consumed by factory.styl via generateColorClasses() and exposed as CSS custom properties: --q-{name}`). **Префикс будет переименован** с `--q-` (Quasar) на нейтральный (`--ds-` или `--mag-`).

### 1.4 «Рискованные» места

| Зона | Чем рискованно | Митигация |
|---|---|---|
| Минимум 493 прямых `<q-*` в 68 файлах (`admin` + `ui-comp`, HTML‑syntax only) | Не все обёрнуты в `@ui-comp`; Pug и CSS требуют отдельного прохода | SFC/Pug codemod + ручной обход топ‑20 «плотных» файлов |
| 33 файла через `useNotify()` | Уже изолировано через app composable и `@shared/utils/notify` | Перенести источник правды в `@ds`/`@shared` adapter, UI реализовать через Toast host |
| 5 файлов с `useQuasar()` (Dialog API) | Императивный programmatic API | Заменяем на `useDialog()` composable (свой) поверх Reka `<DialogRoot>` |
| `v-close-popup` (35 раз в admin/ui) | Quasar‑специфичная директива | Свой `v-close-popup` на основе provide/inject или замена на handler |
| `v-ripple` (5 раз) | Quasar‑специфичная директива | Удалить или заменить CSS pressed/focus state |
| `q-table` CSS/comments остатки | Реальный `<q-table>` уже запрещён ESLint, но остались `.q-table`/`--q-table-*` | Очистить CSS selectors и token aliases перед финальной проверкой |
| `q-tree` (1 файл, `DocumentDetails.vue`) | Сложный компонент | Переписать на Reka Tree (Alpha) либо свой минимальный компонент |
| `q-date` (несколько диалогов) | Полноценный календарь | Reka Date Picker / DatePicker (Alpha) |
| 659 utility‑классов `q-pa-*`, `q-gutter-*` | Большой объём | Codemod на наши utility‑классы из токенов |
| Cypress `.q-page`, `.q-table`, `.q-notification`, `.q-dialog--modal`, `.q-field--error` | Тесты сломаются при удалении Quasar | Заменить на `data-test="*"` атрибуты на новых компонентах **до удаления Quasar** |
| FontAwesome v5 через `@quasar/extras` | Нужна замена доставки иконок | Перейти на `@iconify-json/fa6-*` или встроить FA напрямую |
| `animate.css` | Не Quasar, но всё рядом | Оставляем — независимая зависимость |

---

## 2. Целевой стек

### 2.1 Reka UI — headless‑компоненты

**Reka UI** ([reka-ui.com](https://reka-ui.com)) — это эволюция Radix Vue v2: unstyled, accessibility‑first, tree‑shakable Vue 3 компоненты. Все наши потребности покрыты:

| Нужно | Reka UI |
|---|---|
| Dialog / AlertDialog | `Dialog`, `AlertDialog` |
| Dropdown / Menu | `DropdownMenu`, `ContextMenu`, `Menubar`, `NavigationMenu` |
| Tooltip | `Tooltip` |
| Popover / Hover Card | `Popover`, `HoverCard` |
| Tabs | `Tabs` |
| Accordion / Expansion | `Accordion`, `Collapsible` |
| Select / Combobox | `Select`, `Combobox`, `Listbox`, `Autocomplete` |
| Checkbox / Radio / Switch / Toggle | `Checkbox`, `RadioGroup`, `Switch`, `Toggle`, `ToggleGroup` |
| Slider / Range | `Slider` |
| Progress | `Progress` |
| Avatar | `Avatar` |
| Tags / Chips Input | `TagsInput` |
| PIN ввод | `PinInput` |
| Date | `Calendar`, `DatePicker`, `DateRangePicker`, `DateField`, `TimeField` |
| Toast (Notify) | `Toast` |
| Tree | `Tree` (Alpha — оценить готовность) |
| Stepper | `Stepper` (Alpha) |
| Pagination | `Pagination` |
| Splitter | `Splitter` (для drawer/resizable панелей) |
| ScrollArea | `ScrollArea` (заменит `q-scroll-area`) |
| Separator / Aspect Ratio / Visually Hidden | `Separator`, `AspectRatio`, `VisuallyHidden` |

**Утилиты Reka UI**: `Primitive`, `Slot`, `useId`, `useEmitAsProps`, `useFilter`, `useForwardProps`, `useForwardPropsEmits`, `useDateFormatter`, `useDirection`, `useLocale`, `useForwardExpose`, `Presence`, `RovingFocus`, `FocusScope`, `ConfigProvider`.

**`asChild` prop‑паттерн** — позволяет передать стиль/атрибуты исходного компонента в дочерний DOM‑элемент. Заменяет «слотовые сценарии» Quasar (`<q-btn><template v-slot>...</template></q-btn>`).

### 2.2 CUBE CSS — методология

[cube.fyi](https://cube.fyi/) / [piccalil.li/blog/cube-css](https://piccalil.li/blog/cube-css/).

> **C**omposition · **U**tility · **B**lock · **E**xception

| Слой | Что туда идёт |
|---|---|
| **Composition** | Макетные утилиты вне компонента: `.stack`, `.cluster`, `.sidebar`, `.flow`, `.center`, `.switcher` (паттерны Every Layout). Управляют ритмом и расположением блоков. |
| **Utility** | Атомарные классы из дизайн‑токенов: `.bg-primary`, `.text-muted`, `.p-md`, `.gap-sm`, `.rounded-pill`, `.shadow-1`. Генерируются из `_colors.styl`/`_spacing.styl`/etc. |
| **Block** | Vue SFC = блок: `KmBtn`, `KmDialog`, `KmDataTable`. Стили в `<style>` блоке компонента, минимальные, остальное — composition + utility. |
| **Exception** | Вариации блока через `data-*` атрибуты: `<KmBtn data-state="loading">`, `<KmDialog data-size="lg">`. CSS селектор: `.km-btn[data-state='loading']`. Семантично, не плодит классов. |

**Группировка классов** в шаблонах (стандарт CUBE):

```html
<button
  class="km-btn flow gap-sm bg-primary text-on-primary"
  data-state="loading"
  data-size="md"
>
```

Преимущество: визуальная дисциплина (block → composition → utility), знакомая семантика data‑атрибутов вместо `v-bind:class` хака. Оригинальный CUBE часто показывает группировку через `class="[ block ] [ composition ] [ utility ]"`; для этого проекта лучше не добавлять literal `[`/`]` классы в Vue templates, чтобы не шуметь в snapshots, Cypress и class‑based поиске.

#### 2.2.1 Финальные правила архитектуры: CUBE + Reka, без Quasar patterns

Эта миграция не должна закончиться “Quasar‑подобной DS на Reka”. Совместимость нужна только для плавного перехода; финальный код должен выглядеть как собственная дизайн‑система.

| Область | Финальное правило |
|---|---|
| Поведение | Reka UI используется как headless/accessibility слой: focus management, roving focus, portals, aria, keyboard interaction. Не копируем Quasar lifecycle/plugin model. |
| Styling | Все стили идут через CUBE: composition classes для layout, token utilities для атомарных значений, block CSS внутри компонента, `data-*` для exceptions. |
| Public component API | Основной API — семантический: `variant`, `tone`, `size`, `density`, `state`, `orientation`, `placement`. Quasar vocabulary (`flat`, `dense`, `unelevated`, `rounded`, `round`, `no-caps`, `color`, `text-color`) допустим только как deprecated alias на время миграции. |
| DOM/classes | Финальный DOM не содержит `.q-*`, `q-*` utility classes, Quasar selector hooks, `q-` component names или `--q-*` tokens. |
| State | Состояния выражаются через `data-state`, `data-variant`, `data-tone`, `data-size`, `aria-*`, а не через Quasar class names вроде `.q-field--error`. |
| Layout | Не переносим Quasar `row`/`col`/`q-gutter-*` как ментальную модель. Используем `.cluster`, `.stack`, `.sidebar`, `.switcher`, CSS Grid/Flex и локальные block styles. |
| Services | Нет `$q`, `useQuasar()`, global Quasar plugin или `Dialog.create()`/`Notify.create()` style API как финального интерфейса. Вместо этого — typed composables + host components. |

Переходные aliases должны иметь срок жизни: либо удаляются в той же фазе, где очищен потребитель, либо явно попадают в cleanup checklist с владельцем. Если alias нужен дольше, он живёт в `@ds/compat/*`, а не в core component API.

### 2.3 Tokens → CSS custom properties

Текущая структура в Stylus отлично ложится на CSS variables. Переход:

```stylus
// before (themes/src/base/tokens/_colors.styl)
$colors = { primary: #6840c2, ... }
```

```css
/* after (themes/src/base/tokens/colors.css) */
:root {
  --ds-color-primary: #6840c2;
  --ds-color-primary-light: #E5E3F2;
  --ds-color-primary-bg: rgb(80 47 153 / 0.07);
  --q-primary: var(--ds-color-primary); /* temporary legacy alias */
  /* ... */
}
:root[data-theme='dark'] {
  --ds-color-primary: #8b66e0;
  /* ... */
}
:root[data-brand='salesforce'] { /* ... */ }
:root[data-brand='siebel']     { /* ... */ }
```

Темизация через `data-theme` / `data-brand` на `<html>` совпадает с текущим механизмом `loadTheme(name)`. Миграцию токенов лучше делать в два шага: сначала генерировать `--ds-*` **и временные alias переменные `--q-*`**, затем убрать `--q-*` только после очистки legacy CSS (`var(--q-*)`, `.q-*`, `quasar_overrides.styl`). Это снижает риск визуального регресса в `@themes`, `@ui-comp` и `magnet-panel`.

### 2.4 Иконки

Quasar использовал `material-icons` + FontAwesome v5 (через `@quasar/extras`).

**Рекомендация**: перейти на **[unplugin-icons](https://github.com/unplugin/unplugin-icons)** + Iconify коллекции (`@iconify-json/fa6-solid`, `@iconify-json/fa6-brands`, `@iconify-json/material-symbols`):

- ✅ Автоматический tree‑shaking — в бандл попадает только реально используемая иконка как inline SVG (≈ 100–500 байт каждая) вместо ~80 KB FA CSS + шрифтов.
- ✅ Тот же синтаксис в шаблонах через wrapper `<KmIcon name="fa6-solid:check">`.
- ✅ Наш существующий `IconPicker.vue` на 342 иконках — пройти codemod `fas fa-times` → `fa6-solid:xmark` (или сохранить v5: `fa-solid-v5:times`).

### 2.5 Утилитные библиотеки, которые **не** трогаем

- `@tanstack/vue-table` — уже основной datagrid, остаётся.
- `@tanstack/vue-query` — независим.
- `pinia`, `vue-router`, `paraglide` — не зависят от Quasar.
- `vue-codemirror`, `vanilla-jsoneditor`, `markdown-it`, `mermaid` — независимы.
- `vue-draggable-plus` — независим.
- `animate.css` — оставляем (можно даже убрать в пользу CSS @keyframes, отдельная задача).

---

## 3. Карта соответствий: Quasar → Reka UI + наш `km-*`

> Стрелка `←` означает «обёртка `km-*` использует Reka UI напрямую», стрелка `→` — «прямое использование Reka UI с CUBE‑классами».

### 3.1 Кнопки и формы

| Quasar | Reka UI | Wrapper в `@ui-comp` | Заметки |
|---|---|---|---|
| `q-btn` (51) | `Primitive` + наша CSS | **`<km-btn>`** | Уже существует — переписать template без `q-icon`/`q-spinner`. `loading` → `data-state="loading"`. |
| `q-btn-toggle` (5) | `ToggleGroup` | `<km-btn-toggle>` (новый) | Сегментированный контрол. |
| `q-btn-dropdown` (2) | `DropdownMenu` + Btn | `<km-btn-dropdown>` (новый) или комбинация существующих |
| `q-input` (5) + km-input | `Primitive` + `<input>` | **`<km-input>`** | Полностью своя реализация, сохранить API (`label`, `rules`, `error`, `dense`). |
| `q-select` (3) + km-select | `Select` или `Combobox` | **`<km-select>`** | Тот, что с поиском → Combobox; обычный → Select. |
| `q-checkbox` + km-checkbox | `Checkbox` | **`<km-checkbox>`** | |
| `q-radio` (1) | `RadioGroup` | `<km-radio-group>` (новый) | Используется один раз. |
| `q-toggle` (7) + km-toggle | `Toggle` или `Switch` | **`<km-toggle>`** | Boolean off/on. |
| `q-slider` (12) + km-slider | `Slider` | **`<km-slider>`** | |
| `q-file` (1) + km-file-picker | `<input type=file>` обёртка | **`<km-file-picker>`** | Не нужен Reka. |
| `q-form` (3) | нет (свой) | `<km-form>` (новый, опционально) | Минимальная композиция: контекст, валидация. Сейчас формы делают валидацию вручную через рефы. |
| `q-date` | `Calendar` / `DatePicker` | **`<km-date>`** | Используем @internationalized/date через Reka. |
| `q-chip` (5) + km-chip | свой `<span>` + utility | **`<km-chip>`** | Без Reka — чистый CSS. |

### 3.2 Layout

| Quasar | Замена |
|---|---|
| `q-layout`, `q-page-container`, `q-page` | Корневой `App.vue` + CSS Grid + Composition‑утилиты `.app-shell`, `.main-content` |
| `q-header`, `q-toolbar`, `q-toolbar-title` | `<header class="app-header cluster gap-md">` — обычные семантические теги |
| `q-drawer` (нет упоминаний в коде, но есть km-drawer) | `Dialog` (modal=false) + `Splitter` для resizable, либо своя реализация на CSS Grid |
| `q-page` | `<main class="page flow">` |
| `q-space` (11) | `class="ms-auto"` (margin‑inline‑start: auto) или CSS gap. Не нужен компонент. |
| `q-separator` (18) | `Separator` или `<hr class="km-separator">` |
| `q-card` + km-card | `<article class="km-card flow">` — без Reka |
| `q-card-section`, `q-card-actions` | `<div class="km-card__body flow">`, `<footer class="km-card__actions cluster">` |

### 3.3 Overlays

| Quasar | Reka UI | Wrapper | Замечание |
|---|---|---|---|
| `q-dialog` (9) | `Dialog`, `AlertDialog` | `<km-dialog>` (новый), `<km-confirm>` (на базе сущ. PopupConfirm) | Programmatic API через `useDialog()` |
| `q-menu` (9) | `DropdownMenu`, `Popover` | `<km-menu>` (новый) | Контекстные меню |
| `q-tooltip` (18) + km-tooltip | `Tooltip` | **`<km-tooltip>`** | |
| `q-popup-proxy` | `Popover` или `Dialog` | по контексту | |
| `q-banner` (1) | свой `<div role="status">` | `<km-banner>` | Без Reka |
| `q-fab` | `DropdownMenu` + Btn (FAB стиль) | свой | Floating action button |

### 3.4 Data display

| Quasar | Замена |
|---|---|
| `q-icon` (119) + km-icon | `<km-icon>` на unplugin-icons |
| `q-list`, `q-item`, `q-item-section`, `q-item-label` (53 в сумме) | `<ul class="km-list"><li class="km-list__item cluster">` — чистый CSS, без библиотеки |
| `q-card` (см. Layout) | свой |
| `q-badge` (15) | `<span class="km-badge">` — utility‑только |
| `q-avatar` (3) | `Avatar` (Reka) — ленивая загрузка fallback |
| `q-img` (1) | `<img loading="lazy">` |
| `q-table` | TanStack Vue Table (как в остальном проекте). В текущей ветке реальных `<q-table>` почти нет/они запрещены ESLint, но остались комментарии, `:deep(.q-table ...)` и `var(--q-table-*)`, которые тоже нужно убрать перед финальной проверкой. |
| `q-tree` (1, в `DocumentDetails.vue`) | Reka `Tree` (Alpha, проверить) или свой минимальный recursive компонент |
| `q-expansion-item` (2) | `Accordion` или `Collapsible` |
| `q-timeline` | свой CSS (если нужно — нет в инвентаре) |

### 3.5 Navigation

| Quasar | Reka UI | Wrapper |
|---|---|---|
| `q-tabs`, `q-tab`, `q-tab-panels`, `q-tab-panel` | `Tabs` | **`<km-tabs>`** — уже есть, переписать на Reka |
| `q-stepper` | `Stepper` (Alpha) или свой | **`<km-stepper>`** — уже есть |
| `q-breadcrumbs` | свой `<nav>` + Composition | если используется |
| `q-pagination` | `Pagination` | новый |

### 3.6 Feedback

| Quasar | Замена |
|---|---|
| `q-spinner`, `q-spinner-dots`, `q-spinner-hourglass` (≈5) | CSS `@keyframes` спиннер в `<km-loader>`/`<km-btn-loader>` |
| `q-linear-progress` (6) | `Progress` (Reka) |
| `q-circular-progress` | свой SVG или Reka `Progress` (на line) |
| `q-skeleton` | свой `<div class="km-skeleton">` |
| `q-inner-loading` (2) + km-inner-loading | overlay div + spinner — без Reka |
| `Notify.create()` (через `useNotify`) | Reka `Toast` + наш `useNotify()` (API не меняем) |
| `Loading.show()` / `Dialog.create()` | `useLoading()` / `useDialog()` composables (свои), на базе Reka |

### 3.7 Утилиты и директивы

| Quasar | Замена |
|---|---|
| `useQuasar()` (5) | разбиваем: `useNotify`, `useDialog`, `useScreen` (своя реактивная обёртка над `matchMedia`), `useDarkMode` |
| `v-close-popup` (35 в admin/ui, 4 в panel) | свой `v-close-popup` (provide/inject от ближайшего Dialog/Menu контекста) **или** заменяем на `@click="emit('close')"` codemod'ом |
| `v-ripple` | убрать как визуальный эффект либо заменить CSS `data-ripple`/pressed state; не тянуть отдельную ripple‑библиотеку без дизайн‑решения |
| `q-resize-observer` / `QResizeObserver` | native `ResizeObserver`, `@vueuse/core` `useResizeObserver` или локальный composable `useElementSize` |
| `q-scroll-observer` / `QScrollObserver` | passive scroll listener / `IntersectionObserver` / локальный `useScrollObserver` |
| `copyToClipboard` (13 файлов в admin/ui, panel тоже использует) | сначала `@ds/compat/quasar`, затем `navigator.clipboard.writeText()` с fallback/error handling |
| `uid` (4 файла) | `crypto.randomUUID()` |
| `date` (2 файла) | `luxon` (уже в зависимостях) или `date-fns` |
| `colors` (2 файла) | свой helper или [colord](https://github.com/omgovich/colord) (~1.7KB) |
| `openURL` (1 файл) | `window.open()` |

### 3.8 Quasar utility‑классы → наш набор

659 упоминаний spacing/gutter/typography/colour утилит. Переписываем codemod'ом:

| Quasar | Наш (CUBE‑style) | Token |
|---|---|---|
| `q-pa-xs` | `p-xs` | `--space-xs` |
| `q-pa-sm` | `p-sm` | `--space-sm` |
| `q-pa-md` | `p-md` | `--space-md` |
| `q-pa-lg` | `p-lg` | `--space-lg` |
| `q-px-md` | `px-md` | `--space-md` |
| `q-py-sm` | `py-sm` | `--space-sm` |
| `q-mb-md` | `mb-md` | `--space-md` |
| `q-ma-none` | `m-0` | `0` |
| `q-gutter-sm` | `cluster gap-sm` или `stack gap-sm` (composition) | `--space-sm` |
| `q-gap-md` | `gap-md` | `--space-md` |
| `q-gutter-x-sm` | `cluster gap-x-sm` | `--space-sm` |
| `row` | `cluster` (Every Layout) | — |
| `col` / `col-auto` | flex utility `flex-1` / `flex-none` | — |
| `text-h1`...`text-h6` | `text-h1`...`text-h6` (свои) | `--font-size-h1`... |
| `text-body1` | `text-body` | `--font-size-body` |
| `text-primary` | `text-primary` (берёт из `--ds-color-primary-text`) | `--ds-color-primary` |
| `bg-primary` | `bg-primary` | `--ds-color-primary` |

Кодмод (jscodeshift / vue-codemod / простой `node:fs` скрипт) пройдёт по `**/*.vue` и заменит. Названия специально близки — разница в одну `q-` префикс.

---

## 4. Целевая структура нового пакета `@ds` (Design System)

Не путать с существующим `@ui-comp` — в первую фазу делаем рядом, в финале переименовываем.

```
web/packages/ds/
├── package.json
├── src/
│   ├── tokens/
│   │   ├── colors.css            ← :root { --ds-color-* }
│   │   ├── spacing.css
│   │   ├── typography.css
│   │   ├── radii.css
│   │   ├── elevation.css
│   │   ├── motion.css            ← --duration-*, --ease-*
│   │   ├── z-index.css
│   │   └── index.css
│   ├── composition/              ← CUBE: C
│   │   ├── stack.css             ← .stack > * + * { margin-block-start: var(--flow-space) }
│   │   ├── cluster.css           ← .cluster { display: flex; flex-wrap: wrap; gap: ... }
│   │   ├── sidebar.css
│   │   ├── switcher.css
│   │   ├── center.css
│   │   ├── flow.css
│   │   └── index.css
│   ├── utilities/                ← CUBE: U (генерация из tokens)
│   │   ├── spacing.css           ← .p-{xs,sm,md,lg,xl}, .m-*, .gap-*
│   │   ├── color.css             ← .bg-*, .text-*, .border-*
│   │   ├── typography.css        ← .text-{h1,h2,...,body,caption}
│   │   ├── layout.css            ← .flex, .grid, .hidden, .visible
│   │   ├── radius.css
│   │   ├── shadow.css
│   │   └── index.css
│   ├── reset.css                 ← заменяет 'quasar/src/css/index.sass'
│   ├── components/               ← CUBE: B (Vue SFC)
│   │   ├── primitives/           ← обёртки над Reka
│   │   │   ├── Dialog/
│   │   │   ├── Menu/
│   │   │   ├── Tooltip/
│   │   │   ├── Popover/
│   │   │   ├── Tabs/
│   │   │   ├── Select/
│   │   │   ├── Combobox/
│   │   │   ├── Checkbox/
│   │   │   ├── Radio/
│   │   │   ├── Switch/
│   │   │   ├── Toggle/
│   │   │   ├── Slider/
│   │   │   ├── Progress/
│   │   │   ├── Avatar/
│   │   │   ├── Accordion/
│   │   │   ├── Toast/
│   │   │   └── Calendar/
│   │   └── domain/               ← наши km-компоненты (наследники @ui-comp)
│   │       ├── KmBtn.vue
│   │       ├── KmInput.vue
│   │       ├── KmCard.vue
│   │       └── ...
│   ├── composables/
│   │   ├── useNotify.ts          ← реализация через Toast
│   │   ├── useDialog.ts
│   │   ├── useLoading.ts
│   │   ├── useScreen.ts
│   │   ├── useDarkMode.ts
│   │   └── useTheme.ts
│   ├── hosts/
│   │   ├── DsToastHost.vue       ← один ToastProvider/Viewport на приложение
│   │   ├── DsDialogHost.vue      ← programmatic dialogs через store/promise
│   │   └── DsLoadingHost.vue     ← global loading overlay
│   ├── compat/
│   │   ├── quasar.ts             ← copyToClipboard, uid, openURL, date helpers
│   │   └── ui-plugin.ts          ← legacy-compatible install() для @ui bridge
│   ├── directives/
│   │   └── close-popup.ts
│   └── index.ts                  ← export * + Vue plugin install()
└── tsconfig.json
```

В `web/tsconfig.base.json` нужно добавить явный alias:

```json
{
  "compilerOptions": {
    "paths": {
      "@ds": ["packages/ds/src/index.ts"],
      "@ds/*": ["packages/ds/src/*"]
    }
  }
}
```

`@ui` пока остаётся legacy alias для `packages/ui-comp/src/index.ts`; переключать его глобально нельзя, пока `magnet-panel` использует тот же пакет.

**Установка в admin:**

```ts
// main.js
import '@ds/tokens'
import '@ds/reset.css'
import '@ds/composition'
import '@ds/utilities'
import ds from '@ds'

app.use(ds, {
  theme: 'default',
  toast: { position: 'bottom-right' },
})
```

В корневом `App.vue` или layout нужно один раз смонтировать host‑компоненты (`DsToastHost`, `DsDialogHost`, `DsLoadingHost`). Без этого `useNotify()`/`useDialog()` будут работать только как thin wrappers без места, где реально рендерятся Toast/Dialog через Portal.

---

## 5. Поэтапный план миграции

### Фаза 0 — Decisions & Spike (1 неделя)

Цель: обнулить риск.

- [ ] **Spike**: написать 1 экран на новой системе (например, `Login.vue` — простой) — проверить разработческий опыт, accessibility, размер бандла, iframe/Siebel embedding, Portal/z-index поведение overlay, SSR (если когда-нибудь появится). Бенчмарк: время первой отрисовки страницы admin до/после.
- [ ] Обновить инвентарь Quasar автоматическим скриптом, который понимает Vue SFC + Pug и исключает `paraglide`, `knowledge-magnet`, `.nx`, `node_modules`, coverage/build artifacts.
- [ ] Зафиксировать scope по `magnet-panel`: **A)** мигрируем вместе с admin, **B)** оставляем panel на legacy `@ui` и legacy `quasarConf`, **C)** делаем app-level alias override только для admin.
- [ ] Решить **формат именования компонентов**: оставить `km-*` (привычно для команды) или новый префикс. Рекомендация: оставить `km-*` — нулевой риск для потребителей.
- [ ] Зафиксировать “anti-Quasar API contract”: какие старые props/directives допускаются как deprecated aliases, где они живут (`@ds/compat`), и в какой фазе удаляются.
- [ ] Решить судьбу префикса CSS variables: `--q-*` (плохо — намекает на Quasar) → **`--ds-*`** или `--mag-*`.
- [ ] Решить, делаем ли совместимость с brand‑темами (`salesforce`, `siebel`) сразу или после удаления Quasar.
- [ ] Решить иконочную стратегию: unplugin-icons + Iconify vs FontAwesome официальный пакет.
- [ ] Зафиксировать список Reka UI компонентов в Alpha, которые нам нужны (`Tree`, `Stepper`, date pickers, `Autocomplete`) — оценить готовность.
- [ ] Утвердить план на код‑ревью.

**Артефакт фазы:** этот документ + рабочий прототип одного экрана.

### Фаза 1 — Foundation: токены и CUBE CSS (1 неделя)

Цель: подложить параллельную систему стилей, не ломая текущий вид.

- [ ] Создать `web/packages/ds` (новый Nx проект).
- [ ] Перенести `web/packages/themes/src/base/tokens/*.styl` в `ds/src/tokens/*.css` (CSS variables).
- [ ] Сгенерировать `--ds-*` и временные alias `--q-*`, чтобы legacy CSS продолжал работать во время поэтапного cutover.
- [ ] Реализовать composition‑утилиты (`stack`, `cluster`, `sidebar`, `switcher`, `flow`, `center`).
- [ ] Реализовать utility‑слой (spacing, color, typography, radius, shadow) — генерация из токенов либо вручную (выбираем по объёму).
- [ ] Добавить `@ds` / `@ds/*` в `web/tsconfig.base.json` и убедиться, что Nx/Vite paths plugin резолвит пакет без app-level hacks.
- [ ] Подключить `@ds/tokens` и `@ds/reset` параллельно с Quasar в `magnet-admin/main.js`.
- [ ] Smoke: текущее приложение должно выглядеть как раньше (новые стили не активны без классов). Cypress smoke прогон.

**Артефакт фазы:** работает Quasar + параллельные новые токены и utilities.

### Фаза 2 — Primitives layer (2 недели)

Цель: иметь **рабочие Reka UI обёртки в `@ds`** для всех overlays и базовых форм. Использования в приложении нет — только Storybook/docs.

- [ ] Установить `reka-ui`, `@internationalized/date`, `@vueuse/core`, `unplugin-icons`, `@iconify-json/fa6-solid`, `@iconify-json/fa6-brands`, `@iconify-json/material-symbols`.
- [ ] Сделать `Dialog`, `AlertDialog`, `Menu`, `Tooltip`, `Popover`, `Tabs`, `Accordion`, `Select`, `Combobox`, `Toast`, `Switch`, `Checkbox`, `RadioGroup`, `Slider`, `Progress`, `Separator`, `Avatar`, `ScrollArea` обёртки с CUBE‑стилизацией.
- [ ] `useNotify`, `useDialog`, `useLoading`, `useDarkMode`, `useResizeObserver`, `useScrollObserver` — composables.
- [ ] Добавить `DsToastHost`, `DsDialogHost`, `DsLoadingHost` и проверить programmatic API через mounted host, а не через глобальные singleton DOM inserts.
- [ ] Добавить `@ds/compat/quasar` для `copyToClipboard`, `uid`, `date`, `openURL`, чтобы codemod мог сначала заменить imports без переписывания бизнес‑логики.
- [ ] Core primitives не принимают Quasar‑style props. Если нужен compatibility mapping (`dense`, `flat`, `color`), он реализуется отдельным wrapper/adapter и помечается как deprecated.
- [ ] **Подключить vitepress / Histoire / Storybook** для каталога компонентов (опционально, сильно ускорит работу команды).

**Артефакт фазы:** в `@ds` есть `<DsDialog>`, `<DsTabs>` и т.п. Они используются только в Storybook/docs.

### Фаза 3 — Domain layer (km-* компоненты) (2 недели)

Цель: дублировать существующие `@ui-comp` компоненты в `@ds/components/domain` на новой основе. **Внешняя совместимость допускается как переходный слой, но целевой API должен быть CUBE/DS‑семантическим, не Quasar‑семантическим**.

Порядок (от простых к сложным):

1. `KmIcon` (иконки на iconify) — используется в большинстве остальных.
2. `KmSeparator`, `KmChip`, `KmBadge`, `KmAvatar`, `KmCard`, `KmEmptyState`, `KmLoader`, `KmInnerLoading`, `KmNotificationText`.
3. `KmBtn`, `KmIconBtn`, `KmBtnLoader`, `KmBtnExpandDown`, `KmNavBtn`.
4. `KmCheckbox`, `KmSwitch`, `KmToggle`, `KmSlider`, `KmRange`.
5. `KmInput`, `KmInputFlat`, `KmInputListAdd`, `KmChipsInput`.
6. `KmSelect`, `KmSelectFlat`, `KmPicker`, `KmIconPicker`, `KmFilePicker`.
7. `KmTooltip`, `KmPopupConfirm`, `KmConfirmAction`, `KmErrorDialog`.
8. `KmTabs`, `KmStepper`, `KmFilterBar`.
9. `KmDate` (Reka Calendar/DatePicker).
10. `KmDrawer`, `KmDrawerLayout`, `KmSection`, `KmBackground`, `KmNavSection`.
11. `KmDataTable` — порт текущей TanStack‑реализации (она почти не зависит от Quasar — пройти по template).
12. Доменные: `KmMarkdown`, `KmJsonEditor`, `KmCodemirror`, `KmImage`, `KmChipCopy`, `KmScore`, `KmSliderCard`, `KmLocaleSwitcher`.

Каждый компонент закрывается:
- ✅ целевые `props`/`emits` описаны в семантике DS (`variant`, `tone`, `size`, `density`, `state`), а legacy props задокументированы как deprecated aliases или вынесены в compat wrapper;
- ✅ pixel‑close к текущему виду (или согласованные правки от дизайнера);
- ✅ keyboard nav и aria через Reka;
- ✅ style/layout реализованы через CUBE layers, без Quasar class names и без копирования Quasar DOM shape;
- ✅ **`data-test="km-btn"`** атрибуты добавлены — для будущих cypress.

**Артефакт фазы:** в `@ds` есть полный набор `Km*`. `@ui-comp` ещё используется приложением.

### Фаза 4 — Cutover: переключение приложения (2–3 недели)

Цель: переключить `magnet-admin` на `@ds` и убрать прямые Q‑компоненты.

#### 4.1 Переключение wrapper-компонентов

`@ui-comp` экспортирует named components и default Vue plugin, который регистрирует компоненты через `import.meta.glob`. Поэтому глобальный re-export `@ui-comp → @ds` рискован: он сразу затронет `magnet-panel`, а также может сломать `app.use(uiComps)`.

Безопасная стратегия:

1. `@ds` реализует собственный `install(app)` и named exports для `Km*`.
2. `magnet-admin` получает `app.use(ds)` параллельно с `app.use(uiComps)` на время миграции.
3. Новые/мигрированные компоненты регистрируются под теми же `km-*` именами только в admin scope. Если Vue warning по duplicate registration мешает, делаем app-level Vite alias `@ui` → `packages/ds/src/compat/ui-plugin.ts` **только для admin**, а panel продолжает использовать legacy `@ui`.
4. После решения по panel можно либо перевести `packages/ui-comp` в thin bridge к `@ds`, либо оставить его legacy до отдельной миграции panel.

Критерий готовности: `magnet-admin` не импортирует Quasar через `@ui`, но `magnet-panel` продолжает собираться и работать в выбранном режиме.

#### 4.2 Codemod для прямых Q‑компонентов

Скрипт `scripts/codemod-quasar-to-ds.mjs`:

| Источник | Цель |
|---|---|
| `<q-icon name="...">` | `<km-icon name="...">` (с маппингом FA имён) |
| `<q-btn ... />` | `<km-btn ... />` (props почти совместимы) |
| `<q-dialog v-model="x">` | `<km-dialog v-model:open="x">` |
| `<q-tooltip>` | `<km-tooltip>` |
| `<q-list>...<q-item>...</q-list>` | `<ul class="km-list"><li class="km-list__item cluster">...` |
| `<q-card-section>` | `<div class="km-card__body flow">` |
| `<q-separator />` | `<km-separator />` |
| `<q-spinner-dots />` | `<km-loader variant="dots" />` |
| `<q-input ... />` | `<km-input ... />` |
| `<q-select>` | `<km-select>` |
| `<q-toggle>` | `<km-toggle>` |
| `<q-tabs><q-tab>` | `<km-tabs items="...">` |
| `<q-tab-panels><q-tab-panel>` | `<km-tab-panels>` |
| `<q-table>` | (1 файл, ручной перенос на TanStack) |
| `<q-tree>` | (1 файл, ручной перенос) |

Топ‑20 «плотных» файлов — **дополнительно ревью человеком** (RetrievalTabControls.vue, MetadataFieldsTable.vue, RetrievalTestDrawer.vue, …).

Codemod не должен быть чистым regex. В проекте смешаны plain templates и Pug, поэтому нужны два режима: `@vue/compiler-sfc` для SFC блоков и отдельный Pug parser/ручной список для `template lang="pug"`. Первый прогон делает dry-run report, второй — `--apply`, третий — human review hot files.

#### 4.3 Codemod для utility‑классов (659 упоминаний)

Скрипт по `**/*.{vue,ts,js}` с allowlist классов:

```js
const map = {
  'q-pa-': 'p-',
  'q-px-': 'px-',
  'q-py-': 'py-',
  'q-pt-': 'pt-',  'q-pb-': 'pb-',  'q-pl-': 'pl-',  'q-pr-': 'pr-',
  'q-ma-': 'm-',
  'q-mx-': 'mx-',  'q-my-': 'my-',  'q-mt-': 'mt-',  'q-mb-': 'mb-',
  'q-gutter-': 'cluster gap-',
  'q-gutter-x-': 'cluster gap-x-',
  'q-gap-': 'gap-',
}
```

Edge cases (`q-ma-none` → `m-0`, `q-py-auto` → `py-auto`) добавить руками. Отдельно пройти CSS selectors и CSS variables: `:deep(.q-table ...)`, `.q-field--error`, `.q-notification`, `var(--q-table-*)`, `var(--q-primary)`. Это не utility‑классы, но они тоже удерживают Quasar semantics.

#### 4.4 Удаление `useQuasar()` и `v-close-popup`

5 файлов с `useQuasar()` — точечная замена на `useDialog()`, `useScreen()`, `useNotify()` из `@ds`.

35 `v-close-popup` в admin/ui — на время миграции можно реализовать одноимённую директиву в `@ds/compat`, но финальный target — явные close handlers / Reka controlled state, без Quasar directive pattern. 5 `v-ripple` — удалить или заменить согласованным pressed/focus state. `copyToClipboard`, `uid`, `date`, `openURL` сначала перевести на `@ds/compat/quasar`, затем постепенно заменить на native/Luxon helpers.

#### 4.5 Cypress

Перед удалением Quasar — обновить селекторы:

| Старое | Новое |
|---|---|
| `.q-page` | `[data-test="page"]` или семантический `<main>` |
| `.q-layout` | `[data-test="app"]` |
| `.q-table` | `.km-data-table` (уже есть) или `[data-test="data-table"]` |
| `.q-notification` | `[data-test="toast"]` |
| `.q-dialog--modal` | `[data-test="dialog"]` |
| `.q-field--error` | `[data-state="error"]` |
| `.q-card.card-hover` | `[data-test="card"][data-hoverable]` |

Один прогон Cypress на ветке после codemod, прежде чем мерджить.

**Артефакт фазы:** приложение использует только `@ds`. `import 'quasar'` остаётся в `main.js` и `quasar.js` boot, но реальное использование 0.

### Фаза 5 — Удаление Quasar (3–5 дней)

- [ ] Удалить `import 'quasar/src/css/index.sass'` из `main.js`.
- [ ] Удалить `app.use(Quasar, quasarConf)` и сам `quasarConf` из `@shared`.
- [ ] Удалить `@quasar/vite-plugin` из `vite.config.ts`.
- [ ] Удалить `manualChunks.quasar`.
- [ ] Удалить `web/apps/@ipr/magnet-admin/src/styles/quasar-variables.sass`.
- [ ] Удалить `web/packages/themes/src/base/quasar_overrides.styl`.
- [ ] Удалить временные `--q-*` aliases из `@ds/tokens` после очистки всех `var(--q-*)` в admin scope.
- [ ] Удалить или изолировать `@ds/compat/quasar`, deprecated props (`dense`, `flat`, `no-caps`, `text-color`, etc.) и compat directives из core build.
- [ ] Добавить ESLint/no-restricted-imports/no-restricted-syntax checks: запрет `from 'quasar'`, `$q`, `useQuasar`, `<q-*`, `.q-*`, `--q-*`, Quasar‑style core props в `web/packages/ds/src/components`.
- [ ] Удалить из `web/package.json`: `quasar`, `@quasar/extras`, `@quasar/vite-plugin` **только если выбранный scope включает `magnet-panel` или panel уже изолирован от этих dependencies**.
- [ ] Не удалять `sass`, `sass-embedded`, `stylus`, `@types/stylus`, `pug`, `pug-plain-loader`, `@prettier/plugin-pug` в рамках admin-only миграции: текущие темы и panel всё ещё используют Stylus/Pug, а Quasar CSS импортирует Sass.
- [ ] Прогон `lint`, `vitest`, `cypress`, бандл‑анализ (`vite-bundle-visualizer`).
- [ ] PR с ярлыком `migration:final`. CI должен пройти зелёным.

**Артефакт фазы:** `grep -r "quasar" web/apps/@ipr/magnet-admin web/packages/ds` → пусто, а `@ds/components` не содержит Quasar vocabulary как core API. Для `web/packages/ui-comp` условие зависит от решения по panel: либо тоже пусто, либо пакет явно помечен legacy и не импортируется admin.

### Фаза 6 — Cleanup и документация (3–5 дней)

- [ ] Перенести brand‑темы (`salesforce`, `siebel`) на CSS variables.
- [ ] Описать `@ds` в README пакета (как добавить новый компонент, как добавить токен, как делать темизацию).
- [ ] Storybook/Histoire каталог в основной CI.
- [ ] Обновить CLAUDE.md / web README — указать новый стек.
- [ ] Зафиксировать итоговый статус `magnet-panel`: migrated, legacy-isolated или отдельный follow-up epic. Это должно быть отражено в README и Nx/tsconfig aliases.

---

## 6. Стратегия миграции одного компонента (cookbook)

На примере `<km-btn>`:

### 6.1 Текущая реализация (Quasar + Stylus + Pug)

```pug
<template lang="pug">
.km-button(:class='[{ "km-button-flat": flat }]', @click='click')
  q-icon(:name='icon', :size='iconSize')
  .km-button-text {{ label }}
  q-spinner(v-if='loading', size='24px')
</template>
```

### 6.2 Новая реализация (Reka + CUBE CSS + plain template)

```vue
<script setup lang="ts">
import { Primitive } from 'reka-ui'
import KmIcon from '../KmIcon/KmIcon.vue'
import KmLoader from '../KmLoader/KmLoader.vue'

interface Props {
  label?: string
  icon?: string
  iconAfter?: string
  variant?: 'primary' | 'simple' | 'flat' | 'link'
  size?: 'sm' | 'md' | 'lg'
  loading?: boolean
  disabled?: boolean
  asChild?: boolean
}
const props = withDefaults(defineProps<Props>(), {
  variant: 'primary',
  size: 'md',
})
const emit = defineEmits<{ click: [Event] }>()
</script>

<template>
  <Primitive
    :as="asChild ? undefined : 'button'"
    :as-child="asChild"
    class="km-btn"
    :class="['cluster gap-sm']"
    :data-variant="variant"
    :data-size="size"
    :data-state="loading ? 'loading' : disabled ? 'disabled' : undefined"
    :disabled="disabled || loading"
    data-test="km-btn"
    @click="emit('click', $event)"
  >
    <KmIcon v-if="icon" :name="icon" />
    <span v-if="label" class="km-btn__label">{{ label }}</span>
    <KmLoader v-if="loading" size="sm" />
    <KmIcon v-else-if="iconAfter" :name="iconAfter" />
  </Primitive>
</template>

<style>
.km-btn {
  /* B in CUBE: minimal styles. composition + utilities do the rest */
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border: 1px solid transparent;
  border-radius: var(--ds-radius-md);
  font: var(--ds-font-button);
  cursor: pointer;
  transition: background var(--ds-duration-fast) var(--ds-ease-out);
}

/* E in CUBE: variations through data attributes */
.km-btn[data-variant='primary'] {
  background: var(--ds-color-btn-primary-bg);
  color: var(--ds-color-btn-primary-text);
}
.km-btn[data-variant='primary']:hover:not([data-state='disabled']) {
  background: var(--ds-color-btn-primary-hover-bg);
}
.km-btn[data-variant='flat'] {
  background: transparent;
  color: var(--ds-color-btn-flat-text);
}
.km-btn[data-size='sm'] { padding: var(--ds-space-xs) var(--ds-space-sm); }
.km-btn[data-size='md'] { padding: var(--ds-space-sm) var(--ds-space-md); }
.km-btn[data-size='lg'] { padding: var(--ds-space-md) var(--ds-space-lg); }
.km-btn[data-state='loading'],
.km-btn[data-state='disabled'] { opacity: 0.6; pointer-events: none; }
</style>
```

**Что обратить внимание:**
- `Primitive` от Reka обеспечивает `asChild` сценарии (можно передать `as-child` и обернуть `<RouterLink>` без вложенных кнопок).
- Стилизация — через `data-*` (CUBE Exception), не через `:class="{ ... }"` каскад.
- `cluster gap-sm` — composition‑утилита для горизонтальной раскладки иконка+текст+спиннер.
- `font: var(--ds-font-button)` — composite token (font‑shorthand с size+weight+line‑height).

### 6.3 Тесты компонента

```ts
import { mount } from '@vue/test-utils'
import KmBtn from './KmBtn.vue'

it('renders with primary variant by default', () => {
  const w = mount(KmBtn, { props: { label: 'Click' } })
  expect(w.attributes('data-variant')).toBe('primary')
})

it('shows loader when loading', () => {
  const w = mount(KmBtn, { props: { label: 'Click', loading: true } })
  expect(w.attributes('data-state')).toBe('loading')
  expect(w.findComponent({ name: 'KmLoader' }).exists()).toBe(true)
})
```

---

## 7. Темизация и dark mode

### 7.1 Слой токенов

```css
/* @ds/tokens/colors.css */
:root,
:root[data-theme='light'] {
  --ds-color-primary: #6840c2;
  --ds-color-primary-text: #ffffff;
  --ds-color-bg: #fbfbfe;
  --ds-color-text: #191b23;
  --ds-color-border: #eaeaf6;
  /* ... */
}

:root[data-theme='dark'] {
  --ds-color-primary: #8b66e0;
  --ds-color-primary-text: #ffffff;
  --ds-color-bg: #0e1018;
  --ds-color-text: #f4f2f8;
  --ds-color-border: #2a2c38;
  /* ... */
}

@media (prefers-color-scheme: dark) {
  :root:not([data-theme]) { /* fallback */ }
}
```

### 7.2 Brand‑темизация

```css
:root[data-brand='salesforce'] { --ds-color-primary: #0070d2; }
:root[data-brand='siebel']     { --ds-color-primary: #c43d2c; }
```

### 7.3 Применение

```ts
// useTheme.ts
export function useTheme() {
  const set = (theme: 'light'|'dark'|'auto') => {
    document.documentElement.dataset.theme = theme === 'auto' ? '' : theme
    localStorage.setItem('theme', theme)
  }
  /* ... */
}
```

Текущий механизм `loadTheme(name)` в `main.js` остаётся API‑совместимым — внутри переключает `data-theme`.

---

## 8. Метрики успеха

| Метрика | Цель |
|---|---|
| Размер production бандла | **−30%** (Quasar + Roboto + extras = ~600 KB; Reka tree‑shake + Iconify SVG ≈ 200–300 KB) |
| Number of `import 'quasar'` | **0** |
| `q-*` классы в `**/*.vue` | **0** |
| `--q-*` tokens / `.q-*` selectors в финальном admin scope | **0** после удаления legacy aliases |
| Quasar vocabulary как core API (`dense`, `flat`, `unelevated`, `no-caps`, `text-color`, `$q`) | **0** в `@ds` core; разрешено только в `@ds/compat` до cleanup |
| Reka primitives | Используются только как headless behavior layer; стилизация остаётся в CUBE layers |
| Cypress smoke pass rate | **100%** |
| Vitest pass rate | **100%** |
| Lighthouse Accessibility | **≥ 95** |
| Lighthouse Performance (admin Login) | **≥ 90** на десктопе |
| Время первого рендера админки локально | **−15%** или лучше |
| Brand‑темы (`default`/`salesforce`/`siebel`) | работают как раньше |

---

## 9. Риски и митигация

| Риск | Вероятность | Влияние | Митигация |
|---|---|---|---|
| Reka UI Alpha компоненты (Tree, Stepper, Calendar) недостаточно зрелые | средняя | средний | Spike в Фазе 0; готовый fallback — свой минимальный компонент или Vue3‑porting Radix UI Tree |
| Cypress тесты массово красные после codemod | средняя | высокий | Заранее перейти на `data-test` атрибуты; запускать suite после каждого codemod'а |
| Brand‑темы (Salesforce, Siebel) визуально расходятся | средняя | средний | Дизайнер делает QA по топ‑20 экранам в каждой теме перед удалением Quasar |
| Изменения дизайна в процессе → блокирует миграцию | средняя | средний | Заморозка значимых дизайн‑итераций на admin до конца Фазы 5; ну или ставить им `--ds-*` |
| Время на миграцию вырастает в 2× | средняя | средний | Чёткие фазы; возможен «откат на середине» — Quasar+Reka сосуществуют |
| `magnet-panel` использует общий `@ui-comp`/`@themes`/`@shared quasarConf` | **подтверждено** | высокий | В Фазе 0 выбрать scope. Для admin-only миграции не трогать глобально `@ui`, `@shared quasarConf`, package deps и Vite panel config. |
| Programmatic Notify/Dialog/Loading некуда рендерить после Quasar | средняя | высокий | `DsToastHost`, `DsDialogHost`, `DsLoadingHost` в root layout + unit/e2e tests для promise/close semantics |
| Compatibility слой превращается в постоянный Quasar‑like API | высокая | высокий | Deprecated aliases только в `@ds/compat`, owner + cleanup phase, ESLint checks против Quasar vocabulary в `@ds/components` |
| Codemod пропустит Pug templates или CSS `:deep(.q-*)` | высокая | средний | Инвентарь через SFC/Pug parser, dry-run report, отдельный CSS pass, ESLint no-restricted-syntax/no-restricted-imports после cutover |
| `@quasar/extras` иконки не покрывают какие‑то редкие случаи | низкая | низкий | Добавить точечно SVG в `@ds/icons` |
| TS‑типизация форм стала строже / сломались `rules` API | средняя | низкий | Сохранить совместимость API в `<KmInput>` |

> 🚨 **Критично решить в Фазе 0**: `magnet-panel` уже использует `@ui`, `@shared quasarConf`, Quasar CSS/plugin и часть Quasar helpers. Миграция должна **либо** включить panel, **либо** оставить для panel legacy path, пока он не мигрирует.

---

## 10. Альтернативы, рассмотренные и отвергнутые

| Альтернатива | Причина отказа |
|---|---|
| **Tailwind CSS + shadcn-vue** | Близкое к Reka, но shadcn-vue пока менее зрелый, чем Reka (которая уже Radix Vue v2). Tailwind конфликтует с CUBE‑идеологией («много классов в HTML»). Можно скомбинировать — но мы решили цельную CUBE‑систему. |
| **PrimeVue / Vuetify / Naive UI** | Те же проблемы, что Quasar — opinionated стилизация, тяжелее уйти в свою дизайн‑систему. |
| **Stay on Quasar и улучшать кастомизацию** | Не решает запрос пользователя «полностью избавиться от Quasar и сделать свою дизайн‑систему». |
| **Headless UI (Vue)** | Меньше компонентов, чем Reka; Reka — прямой потомок Radix с большим покрытием. |
| **Радикально на чистом CSS без headless‑либы** | Accessibility (focus management, aria) — большая работа; Reka даёт это бесплатно. |

---

## 11. Open questions (требуют решения перед стартом)

1. **`magnet-panel`**: мигрируем вместе с admin или изолируем legacy `@ui`/Quasar только для panel? Это blocker для Phase 4/5.
2. **Brand‑темы**: дизайн‑токены `default`/`salesforce`/`siebel` нужно унифицировать в одной таблице, или у каждой полностью свой набор?
3. **Storybook / Histoire**: нужен в этой миграции или делается отдельно?
4. **Pug**: оставляем как опцию для шаблонов в новых компонентах или переходим на plain `<template>`? (Рекомендация: **plain** — стандарт в экосистеме, Reka примеры на нём.)
5. **Stylus**: в `web/packages/themes` Stylus используется широко — переписываем все стили на чистый CSS или оставляем для legacy частей?
6. **Иконки**: миграция 342 FA‑упоминаний (`fas fa-times`) на iconify (`fa6-solid:xmark`) включает переименование (FA5 → FA6) или сохраняем v5?
7. **`useNotify` API**: сохраняем 1‑в‑1, но где живёт источник правды — `@shared/utils/notify`, `@ds/composables/useNotify` или app-local adapter?
8. **`@ds` vs `@ui-comp`**: оставляем оба пакета, делаем app-level alias для admin или переводим `@ui-comp` в bridge только после panel?
9. **Legacy aliases**: какой максимальный срок жизни у deprecated Quasar‑style props/directives после cutover? Рекомендация: не дольше одной фазы после миграции последнего потребителя.
10. **Бюджет**: 8–12 недель — приемлемо? Если меньше — резать скоуп (например, не трогать `salesforce`/`siebel` темы).

---

## 12. Чеклист «готово к старту»

- [ ] Этот план одобрен техлидом и дизайнером
- [ ] Решены open questions §11
- [ ] Создан Linear/Asana epic с разбивкой по фазам
- [ ] Назначен ownership: один лид‑инженер на всю миграцию
- [ ] Фаза 0 spike закончена и положительная
- [ ] Заведена ветка `feat/migrate-to-reka-ui`
- [ ] Плановый ритм релизов admin не блокируется (короткие feature-flagged вмердживания)
- [ ] Бекап / тег `pre-quasar-removal` создан перед Фазой 5

---

## Приложение A. Файлы с самой высокой плотностью Quasar (топ‑20)

| # | Файл | Q‑компонентов | Строк | Плотность |
|---|---|---|---|---|
| 1 | `KnowledgeGraph/Retrieval/RetrievalTabControls.vue` | 50 | 527 | 9.5% |
| 2 | `KnowledgeGraph/MetadataFields/MetadataFieldsTable.vue` | 38 | 1391 | 2.7% |
| 3 | `KnowledgeGraph/Retrieval/RetrievalTestDrawer.vue` | 22 | 1039 | 2.1% |
| 4 | `KnowledgeGraph/Sources/SourcesTab.vue` | 22 | 642 | 3.4% |
| 5 | `KnowledgeGraph/common/KgDropdownField.vue` | 21 | 661 | 3.2% |
| 6 | `KnowledgeGraph/Details.vue` | 18 | 923 | 1.9% |
| 7 | `KnowledgeGraph/ContentProfiles/ContentConfigDialog.vue` | 18 | 904 | 2.0% |
| 8 | `KnowledgeGraph/EntityExtraction/EntityExtractionTab.vue` | 18 | 714 | 2.5% |
| 9 | `KnowledgeGraph/MetadataFields/MetadataPanel.vue` | 16 | 471 | 3.4% |
| 10 | `KnowledgeGraph/DataExplorer/DocumentDetails.vue` | 15 | 1437 | 1.0% |
| 11 | `KnowledgeGraph/DataExplorer/EntitiesTable.vue` | 14 | 278 | 5.0% |
| 12 | `KnowledgeGraph/Retrieval/GuidedExamplesTable.vue` | 14 | 129 | 10.8% |
| 13 | `KnowledgeGraph/MetadataFields/MetadataFieldDialog.vue` | 12 | 1028 | 1.2% |
| 14 | `KnowledgeGraph/ContentProfiles/ContentProfilesTab.vue` | 12 | 513 | 2.3% |
| 15 | `KnowledgeGraph/StructureGuides/StructureGuideDialog.vue` | 12 | 454 | 2.6% |
| 16 | `KnowledgeGraph/common/KgDialogBase.vue` | 11 | 187 | 5.9% |
| 17 | `KnowledgeGraph/common/KgConfirmDialog.vue` | 11 | 165 | 6.7% |
| 18 | `KnowledgeGraph/MetadataFields/MetadataTab.vue` | 9 | 1189 | 0.8% |
| 19 | `KnowledgeGraph/EntityExtraction/EntityColumnsSection.vue` | 9 | 472 | 1.9% |
| 20 | `KnowledgeGraph/DataExplorer/DocumentsTable.vue` | 8 | 188 | 4.3% |

> **Замечание**: Knowledge Graph модуль — самая «горячая» зона. План миграции должен учитывать это в распределении нагрузки и code review. Пути в таблице нужно обновить перед стартом: в текущей ветке часть файлов переехала (например, `RetrievalTestDrawer.vue` найден в `KnowledgeGraph/Playground`), а `ui-comp/src/components/Retrieval/MetadataFilterEditor.vue` тоже попадает в hot list.

## Приложение B. Полный реестр Quasar точек входа (для finder/grep)

```bash
# Найти всё что нужно убрать в Фазе 5
grep -RInE "from ['\"]quasar['\"]" web/apps/@ipr/magnet-admin/src web/packages/ui-comp/src web/packages/shared/src
grep -RInE "import ['\"]quasar/" web/apps/@ipr/magnet-admin/src web/packages/ui-comp/src
grep -RIn "useQuasar" web/apps/@ipr/magnet-admin/src web/packages/ui-comp/src
grep -RInE "v-close-popup|v-ripple" web/apps/@ipr/magnet-admin/src web/packages/ui-comp/src
grep -RInE "<q-[a-z-]+|(^|[[:space:]])q-[a-z-]+\(" web/apps/@ipr/magnet-admin/src web/packages/ui-comp/src
grep -RInE "(class|:class).*q-(pa|px|py|pt|pb|pl|pr|ma|mx|my|mt|mb|ml|mr|gutter|gap)" web/apps/@ipr/magnet-admin/src web/packages/ui-comp/src
grep -RInE "\.q-|--q-|var\(--q-" web/apps/@ipr/magnet-admin/src web/packages/ui-comp/src web/packages/themes/src
grep -RIn "@quasar/" web/apps/@ipr/magnet-admin/src web/packages package.json web/package.json
```

Если в окружении есть `rg`, предпочтительнее использовать `rg`/`rg --files`; в текущем терминале audit выполнялся через `find`/`grep`, потому что `rg` не установлен.

## Приложение C. Команды для типичных задач миграции

```bash
# Создать пакет @ds (через Nx)
yarn nx g @nx/vue:lib ds --directory=packages/ds --buildable --publishable=false

# Установить новые зависимости
cd web && yarn add reka-ui @internationalized/date @vueuse/core
cd web && yarn add -D unplugin-icons @iconify-json/fa6-solid @iconify-json/fa6-brands @iconify-json/material-symbols

# Прогнать codemod
node scripts/codemod-quasar-to-ds.mjs --apply
node scripts/codemod-q-utility-classes.mjs --apply

# Smoke
yarn nx run magnet-admin:lint
yarn nx run magnet-admin:test
yarn nx run magnet-admin:e2e --browser chrome --headless

# Если panel остаётся в workspace scope, проверять и его
yarn nx run magnet-panel:lint
yarn nx run magnet-panel:test

# Финальная проверка перед удалением Quasar
grep -RInE "<q-[a-z-]+|(^|[[:space:]])q-[a-z-]+\(|from ['\"]quasar['\"]|--q-|\.q-" web/apps/@ipr/magnet-admin/src web/packages/ds/src && echo "STILL HAS QUASAR" || echo "CLEAN"
```

---

**Конец документа.**

# План рефакторинга UI на Reka UI + CUBE CSS

> Дата: 2026-04-26  
> Scope: `web/packages/ds`, `web/packages/ui-comp`, `web/packages/themes`, `web/apps/@ipr/magnet-admin`, `web/apps/@ipr/magnet-panel`  
> Цель: сначала проверить и укрепить новые примитивы, затем переделать UI так, чтобы он опирался на надежную дизайн-систему, а не на Quasar-наследие, переходные адаптеры и CSS-хаки.

## 0. Краткое Резюме

### Статус Исполнения На 2026-04-26 (updated 14:30)

- Phase 0 выполнена как первая опорная итерация: добавлены `web/scripts/audit-ds-migration.mjs`, `web/scripts/ds-migration-baseline.json`, отчет `reports/frontend-ds-audit-2026-04-26.md`, npm/yarn scripts и README guardrails.
- Audit и ESLint scope исключают generated `src/paraglide/**`, чтобы migration metrics и lint warnings отражали живой UI-код, а не сгенерированные i18n modules.
- ESLint guardrail расширен: новые imports из `@quasar/extras` запрещены без allowlist.
- Phase 2.2 выполнена для dynamic color fallbacks: добавлен `web/packages/ds/src/utils/resolveDsColor.ts`, а `dynamicQCssVarFallbacks` в audit baseline снижен с 16 до 0.
- Phase 3.1 выполнена: Material Icons font files завендорены в `web/packages/themes/src/base/assets/fonts/material-icons/`, `loadFonts.js` переведен на local assets, `@quasar/extras` удален из `web/package.json` и lockfile, audit metric `quasarExtrasRefs` снижен с 4 до 0.
- В рамках font cleanup исправлены vendored FontAwesome CSS paths с `../webfonts/` на `../fonts/fa/`; admin/panel builds больше не показывают эти asset resolve warnings.
- Phase 3.2 выполнена: `v-close-popup` удален из admin/panel templates, dialog close actions переведены на явные state updates, no-op directive удален из `@ui-comp` install, audit metric `vClosePopup` снижен с 29 до 0.
- Phase 3.3 выполнена: последние `v-ripple="false"` usages удалены из KnowledgeGraph menus, audit metric `vRipple` снижен с 5 до 0.
- Phase 7.4 частично выполнена для Cypress: все `.q-*` selectors в `web/apps/@ipr/magnet-admin/cypress/**` заменены на DS/data-test hooks, audit metric `cypressQSelectors` снижен с 16 до 0.
- Phase 7.4 продолжена для KnowledgeGraph select control: `KgDropdownField.vue` переведен с `.q-field*`/`.q-virtual-scroll*`/`.q-item-label` selectors на стабильные `.km-select*`, `.ds-select*`, `.km-input*`, `.ds-input` hooks; `KmSelect.vue` получил недостающие compatibility hooks для `popup-content-class`, slots и popup events. Audit metrics снижены: `.q-*` CSS selectors 303 -> 277, `:deep(.q-*)` 86 -> 74, `@ds/compat` imports 26 -> 25.
- Phase 7.4 продолжена для KnowledgeGraph prompt/section controls: `KgPromptSection.vue`, `KgExpandablePrompt.vue`, `KgDialogSection.vue` переведены с `.q-field*`/`.q-expansion-item*`/`.q-item*` selectors на стабильные `.km-expansion-item*`, `.ds-textarea`, `.ds-input`, `.km-input*` hooks; color resolving переведен с `@ds/compat/legacy` на публичный `resolveDsColor` из `@ds`. Audit metrics снижены: `.q-*` CSS selectors 277 -> 234, `:deep(.q-*)` 74 -> 47, `@ds/compat` imports 25 -> 23.
- **выполнено:** Phase 7.4 продолжена для app layout.css и всех оставшихся component files: удалены мёртвый блок `sticky-virtscroll-table` из layout.css (q-table__*), `.km-textarea-relaxed` мигрирован на `.km-input__*` селекторы, батч-удалены `.km-input:not(.q-field--readonly) .q-field__control::before` из 27 component files, очищены `Details.vue`, `FileUrlUpload.vue`, `Retrieval/Prompt.vue`, `Search/Prompt.vue`. **`:deep(.q-*)` полностью устранены (5→0).** Metrics: `qCssSelectors` 184→**106**, `deepQSelectors` 5→**0** (полная элиминация). Оставшиеся 106 — только в DS package utilities и theme files. Commit: `772d40f0`.
- **выполнено:** Phase 7.5 выполнена: layout.css legacy aliases retired. `q-col-gutter-*` (38 dead selectors) заменены на `gap-*` utility helpers, `.q-page` alias мигрирован на `km-page` в 3 templates (Mcp/Page.vue, KnowledgeGraph/Page.vue, ApiServers/Page.vue). Metrics: `qCssSelectors` 0, `deepQSelectors` 0. Commit: `da87fe65`.
- **выполнено:** Phase 7.6 выполнена: удалены все оставшиеся Quasar-compat слои. 65 `--q-*` CSS variable aliases удалены из `tokens/colors.css` (нет потребителей). `copyToClipboard` вынесен в `@ds/utils/clipboard`. 23 `@ds/compat/legacy` import sites мигрированы на платформенные API (`navigator.clipboard`, `crypto.randomUUID()`, luxon, `window.open`). Baseline обновлен до **всех 13 метрик = 0**. Commit: `3be017a7`.
- **выполнено:** Phase 7 final cleanup: `@ds/compat/` директория (legacy.ts + index.ts) удалена — ноль потребителей. Убраны `@ds/compat/legacy` и `@ds/compat` из `tsconfig.base.json`. `KmChipCopy.vue` и `KmErrorDialog.vue` мигрированы с относительных `compat/legacy` импортов на `../../utils/clipboard`. Оба build (admin + panel) прошли. Commit: `f3220868`.

**Текущий статус baseline (все метрики = 0):**

| Метрика | Count |
|---|---:|
| Direct quasar imports | 0 |
| @quasar/extras refs | 0 |
| v-close-popup | 0 |
| v-ripple | 0 |
| Live `<q-*>` template tags | 0 |
| `.q-*` CSS selectors | 0 |
| `--q-*` CSS variables | 0 |
| `var(--q-*)` references | 0 |
| Dynamic `var(--q-${...})` fallbacks | 0 |
| `@ds/compat` imports | 0 |
| `:deep(.q-*)` selectors | 0 |
| Cypress `.q-*` selectors | 0 |

**Следующий этап: Phase 4 — Product UI Refactor (`.row`/`.column`/`.col-*` → CUBE composition)**. Осталось ~1452 usages `.row`/`.column` в app templates — это Phase 4 работа по вертикальным срезам.

Миграция с Quasar на уровне runtime-импортов почти завершена: в frontend workspace не найдено прямых `import ... from 'quasar'`. Новый пакет `@ds` уже большой и живой: в нем есть токены, CUBE CSS composition/utilities, Reka-backed `Ds*` примитивы, `Km*` domain-компоненты, глобальные hosts, composables и compat-слой.

Оставшаяся работа не сводится к тому, чтобы "сделать красиво". Главная задача - сделать дизайн-систему надежной:

- `Ds*` примитивы должны быть маленькими, семантическими, доступными, token-driven и независимыми от Quasar-лексики.
- `Km*` компоненты нужно либо превратить в стабильный Magnet domain-layer, либо явно считать временными legacy-адаптерами.
- App UI должен перестать обращаться к внутренностям старых компонентов через `.q-*`, `:deep(.q-*)`, старые `row`/`column` привычки, `v-close-popup`, `v-ripple` и цветовые имена, которые работают только из-за `--q-*` aliases.
- Повторяющиеся продуктовые паттерны нужно поднимать в явные DS/app patterns, а не копировать scoped CSS по экранам.

Правильный порядок - снизу вверх:

1. Зафиксировать целевую архитектуру и baseline-метрики.
2. Проверить и укрепить `Ds*` primitives.
3. Стабилизировать или разделить `Km*` domain-layer и legacy compatibility.
4. Удалить Quasar compatibility и hack CSS.
5. Переделать UI приложений вертикальными срезами на утвержденных primitives/patterns.
6. Добавить tests, docs, lint rules, visual/a11y gates, чтобы система не откатывалась назад.

## 1. Аудит Текущего Состояния

### 1.1 Структура Новой Дизайн-Системы

`web/packages/ds` сейчас имеет нужную слоистую структуру:

| Слой | Текущие файлы | Наблюдение |
|---|---|---|
| Tokens | `web/packages/ds/src/tokens/*.css` | `--ds-*` custom properties для color, spacing, typography, radii, elevation, motion, z-index, component sizes. |
| Reset | `web/packages/ds/src/reset/index.css` | Заменяет Quasar reset в app entry points. |
| Composition | `web/packages/ds/src/composition/*.css` | CUBE layout primitives: stack, cluster, center, sidebar, switcher, flow, frame. |
| Utilities | `web/packages/ds/src/utilities/*.css` | Spacing, color, typography, radius, shadow, layout, плюс legacy compatibility. |
| Primitives | `web/packages/ds/src/components/primitives/**` | Reka/shadcn-inspired `Ds*` компоненты без Tailwind. |
| Domain components | `web/packages/ds/src/components/domain/**` | Большой `Km*` слой, который во многом сохраняет старый `@ui-comp` API. |
| Composables | `web/packages/ds/src/composables/**` | `useNotify`, `useDialog`, `useLoading`, `useScreen`, `useDarkMode`, observers. |
| Hosts | `web/packages/ds/src/hosts/**` | Toast, dialog, loading hosts, которые монтируются в app root. |
| Compat | `web/packages/ds/src/compat/**`, `web/packages/ui-comp/src/utils/install.ts` | Transitional helpers и no-op `v-close-popup` directive. |

### 1.2 Что Уже Хорошо

- `web/packages/ds/src/components/primitives/index.ts` экспортирует широкий набор primitives: buttons, inputs, fields, dialogs, menus, popovers, select/combobox, table, pagination, sheet/drawer, command, stepper, tags input, number field и другие.
- Проверенные core primitives действительно используют Reka там, где нужно поведение:
  - `DsButton` использует Reka `Primitive` и семантический `variant`/`size` API.
  - `DsDialog` использует Reka `DialogRoot`, `DialogContent`, `DialogOverlay`, `DialogPortal`, `DialogTitle`, `DialogDescription`, controlled `v-model:open`.
  - `DsSelect` использует Reka `SelectRoot` и связанные части.
  - `DsCombobox` forward'ит Reka `ComboboxRoot` props/emits.
- Стили в основном token-driven через `--ds-*` и `data-state`/`data-variant`/`data-size` exceptions.
- Приложение уже заметно использует `@ds`: raw grep нашел 117 `@ds` import matches, плюс много экранов получают `<km-*>` через global registration из `@ui-comp`.
- ESLint уже блокирует прямые `quasar` и `quasar/*` imports в `web/eslint.config.mjs`.
- Прямых Quasar runtime imports в проверенном frontend scope нет.

### 1.3 Основные Риски

| Риск | Наблюдение | Почему важно |
|---|---|---|
| `Km*` все еще во многом legacy compatibility layer | `KmBtn` поддерживает `flat`, `simple`, `dense`, `round`, `disable`, `color`, `bg`; `KmInput` описан как drop-in для старого input API; `@ui-comp` глобально регистрирует `Km*`. | UI может остаться Quasar-shaped даже без Quasar runtime. |
| `--q-*` aliases все еще находятся в tokens | `web/packages/ds/src/tokens/colors.css` определяет `--q-primary`, `--q-grey-*` и т.д. | Новые компоненты могут случайно начать зависеть от Quasar palette names. |
| Dynamic `var(--q-${...})` fallbacks были в domain-компонентах | Удалены из `web/packages/ds/src/components/domain` через `resolveDsColor`; audit metric сейчас 0. | Держать metric на 0, чтобы compatibility снова не протекала в контракт компонентов. |
| `@quasar/extras` удален | Material Icons font files теперь лежат в `web/packages/themes/src/base/assets/fonts/material-icons/`; `loadFonts.js` импортирует local assets. | Держать dependency graph без Quasar packages. |
| Нет DS tests/stories | Не найдено `web/packages/ds/**/*.{spec,test}.*` и `web/packages/ds/**/*.stories.*`. | Корректность primitives не защищена. |
| Остались Quasar-specific CSS selectors | Raw grep нашел 319 `.q-*` selector/mention matches. | Старые CSS-хаки могут быть мертвыми или вынуждать новые компоненты имитировать Quasar internals. |
| Legacy directives удалены | `v-close-popup` и `v-ripple` audit metrics сейчас 0; no-op `close-popup` directive registration удален. | Держать metrics на 0, чтобы state handling оставался явным. |
| Broad legacy layout utilities находятся в core utilities | `layout.css` держит `.row`, `.column`, `.col-*`, `.q-col-gutter-*`, `.q-page`. | CUBE CSS adoption размывается Quasar utility compatibility. |
| App-level CSS все еще патчит старые internals | `web/apps/@ipr/magnet-admin/src/assets/layout.css` таргетит `.q-table__middle`, `.q-table__bottom`, `.q-field__control`, `.q-textarea`. | Это ровно те хаки, от которых нужно уйти. |
| Некоторые детали primitives требуют проверки | Например, `DsField` использует `@container`, но сам не задает `container-type`; часть контролов рисует manual SVG icons. | Маленькая ошибка в primitive становится ошибкой во всем UI. |

### 1.4 Baseline-Метрики

Baseline снят из `web` через `yarn audit:ds-migration` 2026-04-26 после Phase 0, Phase 2.2, Phase 3.1, Phase 3.2, Phase 3.3, Cypress-среза Phase 7.4, KnowledgeGraph `KgDropdownField` cleanup и KnowledgeGraph prompt/section cleanup. Generated `src/paraglide/**` не входит в scan scope.

| Метрика | Count | Интерпретация |
|---|---:|---|
| Direct `quasar` imports | 0 | Хорошо. Нужно сохранить guardrail. |
| `@quasar/extras` refs | 0 | Quasar font package удален; Material Icons теперь local theme assets. |
| `v-close-popup` | 0 | Должно оставаться zero. |
| `v-ripple` | 0 | Должно оставаться zero. |
| Live `<q-*>` template tags | 0 | Аудит исключает comments/docs. |
| `.q-*` CSS selectors | 106 | Остались только в DS package utilities (layout.css 41) и theme files (fields.styl 24, siebel 23, salesforce 18). Все admin/panel component files — 0. |
| `--q-*` CSS variables | 65 | В основном aliases в `colors.css`. |
| `var(--q-*)` references | 2 | Статические ссылки на legacy CSS custom properties. |
| Dynamic `var(--q-${...})` fallbacks | 0 | Должно оставаться zero. |
| `@ds/compat` imports | 23 | Transitional compatibility imports. |
| `:deep(.q-*)` selectors | 0 | **Полностью устранены.** Все scoped :deep selectors targeting Quasar internals удалены. |
| Cypress `.q-*` selectors | 0 | Tests переведены на DS/data-test hooks; должно оставаться zero. |
| `@ds` import matches | 116 | Adoption уже значительный. |

Важно: raw grep counts включают comments/docs. Каждая cleanup-фаза должна сначала отделить live usage от исторических комментариев.

## 2. Целевая Архитектура

### 2.1 Layer Contract

Финальный frontend stack должен выглядеть так:

```text
App feature code
  -> Product patterns: list page, detail page, form dialog, toolbar, drawer, filter bar
    -> Domain components: стабильные Magnet-flavored Km* components
      -> Ds* primitives: semantic Reka/shadcn-inspired primitives
        -> CUBE CSS: composition + utilities + blocks + data-* exceptions
          -> Tokens: только --ds-*
```

### 2.2 Ownership Rules

| Слой | Должен владеть | Не должен владеть |
|---|---|---|
| Tokens | Raw design values, semantic aliases, component dimensions | One-screen hacks, Quasar aliases после cleanup |
| Composition | Layout algorithms: stack, cluster, sidebar, switcher, center, flow, frame | Product-specific spacing exceptions |
| Utilities | Маленькие atomic helpers на tokens | Постоянная Quasar compatibility API |
| `Ds*` primitives | Accessibility, keyboard behavior, primitive state, tokenized visual shell | Business logic, Quasar prop names, app-specific labels |
| `Km*` domain | Magnet defaults и повторяющаяся продуктовая семантика | Quasar compatibility как primary API |
| Product patterns | Повторяющиеся page/form/table/dialog workflows | Low-level Reka implementation details |
| Feature screens | Data fetching, feature composition, domain-specific copy | Styling internals primitives, `.q-*`, deep selector hacks |

### 2.3 Public API Rule

Новый product code должен предпочитать:

- `Ds*`, когда нужна generic primitive-level вещь: button, input, field, dialog, menu, popover, select, table structure.
- Stable `Km*`, когда нужна Magnet-specific domain вещь: application button defaults, data table wrapper, markdown, icon picker, score, drawer layout.
- Product pattern components, когда несколько экранов повторяют одну композицию: list page header, searchable table page, settings section, edit dialog.

Новый product code не должен добавлять:

- `flat`, `dense`, `round`, `no-caps`, `unelevated`, `disable`, `text-color` как новую primary API vocabulary.
- `q-*` classes, `.q-*` selectors, `--q-*` variables, `$q`, `v-close-popup`, `v-ripple`.
- Scoped `:deep()` selectors, которые таргетят DS internals, если DS не экспортирует документированный part/class/variable для этой задачи.

## 3. Правила Для Агента

Любой агент, выполняющий этот план, должен соблюдать правила:

1. Идти снизу вверх. Если экрану нужна возможность, которой нет в primitive layer, сначала исправить или расширить primitive.
2. Не гнаться за pixel parity со старым Quasar UI. Нужно сохранить usability и плотность информации, но консистентная новая система важнее копирования старых хаков.
3. Делать compatibility changes измеримыми. Каждая фаза начинается и заканчивается audit counts.
4. Работать маленькими vertical slices. Один primitive family или один product workflow на PR проще проверить.
5. Не давать app CSS лезть во внутренности компонентов. Если многим экранам нужен один override, это DS variant, slot, CSS variable или product pattern.
6. Держать `Ds*` API семантическим. Legacy Quasar-shaped props допустимы только во временных adapters.
7. Добавлять tests до broad adoption. Primitive, который используется по всему приложению, должен иметь render, state, keyboard/a11y и theme coverage.
8. После каждой фазы запускать релевантные команды из `web`:

```bash
yarn nx run magnet-admin:build
yarn nx run magnet-panel:build
yarn nx run magnet-admin:lint
yarn nx run magnet-panel:lint
```

Если target не существует, выполнить `yarn nx show project <project>` и записать замену в этот документ.

## 4. Phase 0 - Baseline, Guardrails, Inventory

Цель: сделать прогресс измеримым до изменения UI.

### Tasks

1. Создать repeatable audit script, например `web/scripts/audit-ds-migration.mjs`, который печатает counts для:
   - direct `quasar` imports
   - `@quasar/extras`
   - `v-close-popup`
   - `v-ripple`
   - live `<q-*>` tags excluding comments/docs
   - `.q-*` selectors
   - `--q-*` definitions и `var(--q-*)`
   - dynamic `var(--q-${...})` fallbacks
   - `@ds/compat` imports
   - app-level `:deep(.q-*)`
   - Cypress selectors containing `.q-*`
2. Сохранить первый output скрипта в `reports/frontend-ds-audit-YYYY-MM-DD.md`.
3. Обновить `web/packages/ds/README.md`, чтобы он соответствовал реальности:
   - README говорит, что `--q-*` aliases живут в `_compat-q-aliases.css`, но сейчас они находятся в `tokens/colors.css`.
   - явно описать stable и transitional parts.
4. Добавить или ужесточить lint rules для нового кода:
   - no direct `quasar` или `quasar/*` imports, уже есть.
   - no new `@quasar/extras` imports.
   - no new `v-close-popup` или `v-ripple`.
   - no new `--q-*` variables outside explicit compatibility allowlist.
   - no new `:deep(.q-*)` selectors.
5. Принять и записать naming policy:
   - `Ds*` - primitive/stable.
   - `Km*` - stable domain или legacy adapter.
   - Если оба значения смешаны, разделить на stable `Km*` и legacy adapters до broad refactor.

### Exit Criteria

- Одна команда печатает текущие migration metrics.
- README и этот план согласованы по compatibility locations.
- CI/lint блокирует новые Quasar-specific patterns.
- Есть письменное решение по `Ds*` vs `Km*`.

## 5. Phase 1 - Аудит И Укрепление Primitives

Цель: проверить, что primitives правильные, до перестройки UI поверх них.

### 5.1 Token Audit

Проверить файлы:

- `web/packages/ds/src/tokens/colors.css`
- `web/packages/ds/src/tokens/spacing.css`
- `web/packages/ds/src/tokens/typography.css`
- `web/packages/ds/src/tokens/radii.css`
- `web/packages/ds/src/tokens/elevation.css`
- `web/packages/ds/src/tokens/motion.css`
- `web/packages/ds/src/tokens/z-index.css`
- `web/packages/ds/src/tokens/components.css`

Tasks:

1. Разделить tokens на категории:
   - raw palette tokens
   - semantic tokens: text, border, surface, control, action, status
   - component tokens: field height, dialog width, radius, z-index
2. Убрать случайную привязку к старой palette. Если token назван как legacy color, но используется семантически, переименовать или alias'ить к semantic name.
3. Добавить недостающие semantic tokens до app refactors:
   - `--ds-color-surface-*`
   - `--ds-color-muted-*`
   - `--ds-color-danger-*`
   - `--ds-color-focus-ring`
   - `--ds-color-selection-*`
   - `--ds-color-sidebar-*`
   - `--ds-color-table-*`
4. Проверить, что light, dark, salesforce и siebel themes override'ят один и тот же набор semantic names.
5. Создать removal plan для `--q-*` aliases:
   - держать только в dedicated compatibility stylesheet, пока app usage существует.
   - никогда не использовать `--q-*` внутри stable `Ds*` primitives.
   - удалить из `colors.css`, когда domain fallbacks исчезнут.

Exit criteria:

- `Ds*` primitives используют только `--ds-*`.
- Token names описывают intent, а не Quasar history.
- Brand/dark theme overrides покрывают все tokens, используемые primitives.

### 5.2 CUBE CSS Layer Audit

Проверить файлы:

- `web/packages/ds/src/composition/*.css`
- `web/packages/ds/src/utilities/*.css`
- `web/packages/ds/src/reset/index.css`

Tasks:

1. Разделить stable utilities и legacy compatibility:
   - stable: spacing, typography, color, radius, shadow, display, DS-owned flex helpers.
   - temporary: `.row`, `.column`, `.col-*`, `.q-col-gutter-*`, `.q-page`.
2. Перенести temporary Quasar compatibility в явный import path вроде `@ds/compat/styles` или `@ds/utilities/legacy`, если изоляции недостаточно.
3. Описать CUBE usage guidance:
   - composition classes для layout structure.
   - utility classes для one-off token spacing/color/type.
   - component block CSS для reusable components.
   - `data-*` exceptions для finite state и variants.
4. Проверить responsive behavior:
   - у container queries должен быть container source.
   - для `DsField` либо добавить `container-type: inline-size`, где это задумано, либо убрать `@container`, пока parent container не гарантирован.
5. Удалять app-level layout hacks только после появления эквивалентных CUBE patterns.

Exit criteria:

- Stable CUBE layer можно документировать без упоминания Quasar.
- Legacy utilities изолированы и имеют deletion milestone.
- App pages можно мигрировать с `row`/`column` на CUBE composition без потери layout behavior.

### 5.3 Primitive Family Audit

Для каждого `Ds*` primitive пройти checklist:

| Check | Required standard |
|---|---|
| API | Semantic props, no Quasar vocabulary. |
| Accessibility | Correct role/aria, label strategy, keyboard behavior, focus visible, disabled state. |
| State | Native state, Reka `data-state` или explicit `data-*` exceptions. |
| Styling | `--ds-*` tokens; no hard-coded app colors unless promoted to tokens. |
| Slots | Slots documented and stable. |
| Model | Controlled/uncontrolled behavior clear; emits follow Vue conventions. |
| Test hooks | Stable `data-test` where app will test it. |
| Theming | Works in light/dark/brand themes. |
| Composition | Does not embed product layout decisions. |

Приоритет проверки:

1. Actions: `DsButton`, `DsButtonGroup`, `DsToggle`, `DsToggleGroup`.
2. Forms: `DsInput`, `DsTextarea`, `DsLabel`, `DsField*`, `DsCheckbox`, `DsSwitch`, `DsRadioGroup`, `DsNativeSelect`, `DsNumberField`, `DsTagsInput`, `DsPinInput`.
3. Overlays: `DsDialog`, `DsAlertDialog`, `DsPopover`, `DsDropdownMenu`, `DsTooltip`, `DsSheet`, `DsDrawer`, `DsHoverCard`.
4. Selection/navigation: `DsSelect`, `DsCombobox`, `DsCommand`, `DsTabs`, `DsAccordion`, `DsCollapsible`, `DsNavigationMenu`, `DsMenubar`, `DsContextMenu`.
5. Data display: `DsTable`, `DsPagination`, `DsBadge`, `DsAvatar`, `DsCard`, `DsItem`, `DsEmpty`, `DsSkeleton`, `DsProgress`, `DsSpinner`, `DsSeparator`.
6. Specialized primitives: `Calendar`, `RangeCalendar`, `Carousel`, `Resizable`, `Sidebar`, `InputOTP`.

Конкретные вопросы из аудита:

- `DsDialog` close icon рисуется manual SVG. Решить, приемлемо ли это, или нужно использовать project icon primitive.
- `DsSelect` должен дать достаточно slots/parts, чтобы app screens не таргетили internals.
- `DsField` responsive mode требует проверенной container-query стратегии.
- Primitive CSS глобальный, но prefix-based. Проверить class collisions и необходимость scoped styles.
- У каждого Reka overlay проверить z-index tokens и portal behavior.

### 5.4 Primitive Tests

Добавить tests до массового использования. Минимальный полезный coverage:

| Primitive group | Tests |
|---|---|
| Button | renders as button/link/as-child, disabled blocks interaction, variants/sizes set data attributes. |
| Input/Textarea/Field | model updates, invalid state, label/error/description wiring, disabled/readonly. |
| Checkbox/Switch/Radio | keyboard toggles, checked/unchecked states, disabled. |
| Dialog/Popover/Menu/Tooltip | open/close, Esc/outside click behavior, focus handling, portal rendering. |
| Select/Combobox | keyboard navigation, disabled options, empty state, model update, search path. |
| Table/Pagination | semantic table markup, empty state, pagination controls. |
| Toast/Dialog/Loading hosts | programmatic APIs resolve promises and render expected UI. |

Использовать Vitest + Vue Test Utils, если проект не стандартизировал другой runner. Browser-level Cypress/Playwright coverage добавить позже для сложных overlay interactions.

Exit criteria:

- High-use primitive families имеют tests.
- Tests падают при потере keyboard/model/focus behavior.
- App refactors могут опираться на primitives без ручного smoke каждого состояния.

## 6. Phase 2 - Стабилизация Domain Layer (`Km*`)

Цель: перестать держать `Km*` как безразмерный Quasar compatibility layer.

### 6.1 Классифицировать Каждый `Km*` Component

Создать таблицу в `web/packages/ds/README.md` или `web/packages/ds/COMPONENT_STATUS.md`:

| Status | Meaning | Examples from audit |
|---|---|---|
| Stable domain | Magnet-specific и acceptable for new code | `KmDataTable`, `KmMarkdown`, `KmIconPicker`, если API очищен. |
| Legacy adapter | Нужен, чтобы не трогать сотни call sites сразу | `KmBtn`, `KmInput`, `KmSelect`, пока сохраняют Quasar-shaped props. |
| Candidate primitive | Должен стать или делегировать в `Ds*` | Simple chips/badges, separators, scroll area, toggles. |
| Candidate product pattern | Слишком product-specific для `@ds` primitives | Complex filter bars, drawer layouts, KnowledgeGraph-specific widgets. |

Tasks:

1. Добавить status comment или metadata list для каждого export в `components/domain/index.ts`.
2. Для legacy adapters описать preferred replacement API.
3. Для stable domain components убрать Quasar vocabulary из docs/examples.
4. Для product-specific components решить: остаются в `@ds`, переезжают в app shared components или становятся patterns.

### 6.2 Удалить Dynamic `--q-*` Fallbacks

Затронутые примеры из аудита:

- `KmBtn`
- `KmChip`
- `KmAvatar`
- `KmBadge`
- `KmSwitch`
- `KmCheckbox`
- `KmLoader`
- `KmInnerLoading`
- `KmSeparator`
- `KmLinearProgress`
- `KmToggle`

Tasks:

1. Ввести central color resolver, например `resolveDsColor(name)`, который мапит accepted legacy color names в `--ds-color-*` names.
2. Оставить поддержку literal CSS colors: hex, rgb, hsl, `currentColor`, CSS variables.
3. Заменить `var(--ds-color-${name}, var(--q-${name}, ${name}))` на central resolver.
4. Добавить tests для распространенных legacy color names до удаления fallbacks.
5. Удалить `--q-*` aliases только после удаления всех dynamic fallbacks.

Exit criteria:

- Нет `var(--q-` в `web/packages/ds/src/components`.
- Domain components больше не требуют `--q-*` tokens.
- Известные legacy color names работают через explicit DS mapping.

### 6.3 Разделить Legacy API И Stable API

Текущие `KmBtn`, `KmInput`, `KmSelect` полезны как мост, но не должны определять будущий API.

Рекомендуемый путь:

1. Сохранить текущие компоненты рабочими для существующих экранов.
2. Добавить stable APIs параллельно:
   - `DsButton` для primitive use.
   - `MagnetButton` или cleaned `KmButton`, если нужен domain button.
   - `DsField` + `DsInput`/`DsTextarea` для новых forms.
   - `DsSelect`/`DsCombobox` для новой selection UX.
3. Пометить legacy-only props deprecated в TypeScript/JSDoc:
   - `flat`, `dense`, `round`, `simple`, `disable`, `no-caps`, `textColor`, `bg`, `hoverBg`, Quasar color names.
4. При каждом screen refactor уводить call sites от deprecated props.
5. После app migration удалить old props или перенести adapters в `legacy` namespace.

Exit criteria:

- У нового кода есть documented stable API без Quasar vocabulary.
- Legacy adapter props имеют deprecation comments и migration examples.
- App refactor tasks целятся в stable API, а не закрепляют старые props.

## 7. Phase 3 - Удаление Quasar Compatibility Surface

Цель: удалить оставшуюся Quasar-shaped поверхность из dependencies, CSS, directives и tests.

### 7.1 Удалить `@quasar/extras`

Status: выполнено 2026-04-26. Material Icons font files перенесены в локальные theme assets, `loadFonts.js` больше не импортирует Quasar package, dependency удалена через Yarn, audit baseline обновлен до `quasarExtrasRefs: 0`. FontAwesome CSS paths также переведены на vendored `../fonts/fa/` assets, чтобы убрать build-time `../webfonts` warnings.

Текущее состояние:

- `web/package.json` не содержит `@quasar/extras`.
- `web/packages/themes/src/utils/loadFonts.js` импортирует Material Icons font files из `web/packages/themes/src/base/assets/fonts/material-icons/`.
- `KmIconPicker` historical comment больше не ссылается на Quasar package.

Tasks:

1. Завендорить Material Icons font files в `web/packages/themes/src/base/assets/fonts/material-icons/` или перейти на не-Quasar source/package, уже приемлемый для проекта.
2. Обновить `loadFonts.js`, чтобы он импортировал local assets или новый package.
3. Удалить `@quasar/extras` из `web/package.json` и lockfile.
4. Проверить, что `KmGlyph` все еще рендерит:
   - plain material icon names
   - `o_*` outlined icon names
   - Font Awesome class strings, которые еще используются legacy data
5. Добавить lint rule, блокирующий будущие `@quasar/extras` imports.

Exit criteria:

- `rg "@quasar/extras" web` возвращает только guardrail/audit strings или stale generated cache, не live source imports.
- `web/package.json` не содержит Quasar packages.
- Icons render в admin и panel smoke checks.

### 7.2 Удалить `v-close-popup`

Status: выполнено 2026-04-26. Menu usages удалены там, где `KmMenu` уже закрывается через `autoClose`; dialog close buttons заменены на explicit `@click` updates; no-op `close-popup` directive удален из `web/packages/ui-comp/src/utils/install.ts`. Audit baseline обновлен до `vClosePopup: 0`.

Текущее состояние:

- Audit baseline: 0 live matches.
- `@ui-comp` больше не регистрирует no-op `close-popup` directive.

Tasks:

1. Заменить menu item usage на Reka menu semantics:
   - предпочитать `DropdownMenuItem @select="..."`, где возможно.
   - если используется custom menu component, expose `close()` или `v-model:open` явно.
2. Заменить dialog close buttons на explicit model updates:
   - `@click="dialogOpen = false"`
   - или `DialogClose as-child` внутри `DsDialog`/`KmDialog`.
3. Сначала обработать audit hotspots:
   - `web/apps/@ipr/magnet-admin/src/components/LayoutDefault.vue`
   - `web/apps/@ipr/magnet-admin/src/components/Layouts/WorkspaceTabBar.vue`
   - `web/apps/@ipr/magnet-admin/src/components/Dashboard/Board/ExportButton.vue`
   - `web/apps/@ipr/magnet-admin/src/components/KnowledgeGraph/Retrieval/RetrievalTabControls.vue`
   - `web/apps/@ipr/magnet-admin/src/components/Agents/FeedbackModal.vue`
   - `web/apps/@ipr/magnet-admin/src/components/Toolbar.vue`
   - `web/apps/@ipr/magnet-panel/src/components/base/ErrorDialog.vue`
   - `web/apps/@ipr/magnet-panel/src/components/Agent/FeedbackModal.vue`
4. Удалить no-op directive из `web/packages/ui-comp/src/utils/install.ts`, когда usages станут zero.

Exit criteria:

- `rg "v-close-popup" web/apps web/packages` возвращает zero live usages.
- Global directive registration для popup closing больше не нужен.
- Menus/dialogs закрываются через controlled state или Reka close primitives.

### 7.3 Удалить `v-ripple`

Status: выполнено 2026-04-26. Последние usages были `v-ripple="false"` в KnowledgeGraph row menus; они удалены без изменения обработчиков, disabled state или menu markup. Audit baseline обновлен до `vRipple: 0`.

Текущее состояние:

- Audit baseline: 0 live matches.

Tasks:

1. Заменить ripple affordance на DS hover/pressed/focus states.
2. Если нужно, добавить generic pressed state в `DsItem` или menu item primitives.
3. Удалить directive registration, если он есть.

Exit criteria:

- `rg "v-ripple" web/apps web/packages` возвращает zero live usages.
- Clickable rows/items имеют ясные hover, active, focus-visible и disabled states.

### 7.4 Удалить `.q-*` CSS Selectors И Hack CSS

Status: частично выполнено 2026-04-26 для Cypress selectors и KnowledgeGraph control slices. `web/apps/@ipr/magnet-admin/cypress/**` больше не содержит `.q-*` selectors; smoke/list/table/create/preview helpers используют `.km-layout`, `.km-data-table`, `data-test="table-row"`, `data-test="ds-toast"`, `[role="alert"]` и `[aria-invalid="true"]`. `KgDropdownField.vue` больше не содержит `.q-field*`, `.q-virtual-scroll*`, `.q-item-label` selectors или type-only `@ds/compat/legacy` import; `KmSelect.vue` теперь exposes стабильные hooks для popup content class, `append`/`before-options`/`no-option` slots и `popup-show`/`popup-hide` events. `KgPromptSection.vue`, `KgExpandablePrompt.vue`, `KgDialogSection.vue` больше не содержат `.q-field*`, `.q-expansion-item*`, `.q-item*` selectors; стили переведены на `.km-expansion-item*`, `.ds-textarea`, `.ds-input`, `.km-input*`, а color resolving снят с `@ds/compat/legacy` и использует публичный `resolveDsColor` из `@ds`. Audit baseline обновлен до `cypressQSelectors: 0`, `.q-*` CSS selectors: 234, `:deep(.q-*)`: 47, `@ds/compat`: 23.

Текущее состояние:

- Audit baseline: 234 `.q-*` CSS selector matches.
- Многие из них - app-level patches старых field/table internals.
- Cypress `.q-*` selectors: 0.

Priority buckets:

1. Global app CSS:
   - `web/apps/@ipr/magnet-admin/src/assets/layout.css`
   - заменить `.q-table__middle`, `.q-table__bottom`, `.q-field__control`, `.q-textarea` и т.д.
2. Repeated form hacks:
   - patterns вроде `.km-input:not(.q-field--readonly) .q-field__control::before` во множестве create/page компонентов.
   - перенести нужное поведение в `KmInput`/`DsInput` variants или удалить dead code.
3. KnowledgeGraph custom controls:
   - `MetadataFieldsTable.vue`
   - `MetadataFieldDialog.vue`
   - `SmartExtractionFieldDialog.vue`
   - выполнено: `KgDropdownField.vue`
   - выполнено: `KgPromptSection.vue`
   - выполнено: `KgExpandablePrompt.vue`
   - выполнено: `KgDialogSection.vue`
4. Panel icon patches:
   - `Retrieval/Prompt.vue`
   - `Search/Prompt.vue`
5. Cypress selectors:
   - выполнено: `.q-page`, `.q-layout`, `.q-table`, `.q-card`, `.q-dialog--modal`, `.q-field--error`, `.q-notification` заменены на `data-test`, DS classes или accessibility hooks.

Tasks:

1. Для каждого `.q-*` selector решить:
   - dead code: удалить.
   - поведение все еще нужно: реализовать через DS prop/variant/token/part.
   - test selector: заменить на `data-test`.
2. Не воссоздавать Quasar internal class names в новых компонентах.
3. Если app нужно стилизовать DS subpart, expose стабильный DS class или CSS variable.

Exit criteria:

- Нет live `.q-*` selectors в app/components CSS.
- Ни один app screen не зависит от hidden internal markup старых Quasar components.
- Cypress использует stable `data-test` hooks.

### 7.5 Retire Legacy Layout Utility Aliases

Текущее состояние:

- `layout.css` держит `.row`, `.column`, `.col-*`, `.q-col-gutter-*`, `.q-page`.

Tasks:

1. Инвентаризировать usage legacy layout classes в admin и panel.
2. Map common conversions:
   - `row items-center` -> `cluster` с `data-align="center"` или `.flex items-center`, если это действительно simple.
   - `column` -> `stack` или `.flex flex-col` по смыслу.
   - `col` -> composition layout или explicit `.flex-1 min-w-0`.
   - `q-col-gutter-*` -> `gap-*` или composition `data-gap`.
   - `q-page` -> `km-page` или page pattern.
3. Мигрировать feature-by-feature, не только global codemod, потому что layout behavior может измениться.
4. Перенести оставшиеся aliases в отдельно импортируемый legacy stylesheet, затем удалить import, когда counts станут zero.

Exit criteria:

- Новый UI не использует Quasar layout vocabulary.
- Compatibility aliases удалены или изолированы за explicit legacy import без app dependency.

## 8. Phase 4 - Product UI Refactor По Vertical Slices

Цель: перестроить UI на проверенных primitives и patterns.

Каждый slice выполняется так:

1. Inventory slice:
   - components/pages
   - `Km*` usage
   - direct `Ds*` usage
   - local CSS и `:deep()` selectors
   - layout classes
   - test selectors
2. Найти missing DS capability.
3. Сначала исправить/расширить primitive или pattern.
4. Refactor slice.
5. Запустить build/lint/tests и обновить audit counts.
6. Записать новый pattern в DS docs.

### 8.1 Slice A - App Shell, Navigation, Menus ✅ DONE (commit `f9e61aab`)

Приоритетные файлы:

- `web/apps/@ipr/magnet-admin/src/components/LayoutDefault.vue` ✅
- `web/apps/@ipr/magnet-admin/src/components/Toolbar.vue` ✅
- `web/apps/@ipr/magnet-admin/src/components/Layouts/WorkspaceTabBar.vue` ✅
- `web/apps/@ipr/magnet-panel/src/components/LayoutTab.vue` ✅

Changes applied:
- `.row`/`.column no-wrap` → `.cluster`/`.stack` CUBE primitives with `data-gap`, `data-wrap`, `data-justify`
- Removed Quasar vocab: `clickable`, `dense`, `active-class`, `view="hHh lpR fFf"` from all four files
- Fixed `:active`/`active-class` → `:class` conditional binding
- Replaced `<li class="km-item" clickable dense>` close button → `<button>` element
- Added `data-test` hooks: `panel-layout`, `panel-header`, `panel-close`, `sidebar-toolbar`, `workspace-tab-bar`, `tab-context-menu`, `user-menu`, etc.
- Loading/error/empty states: `column no-wrap items-center justify-center` → `flex items-center justify-center`

Both builds pass (magnet-admin ✓, magnet-panel ✓).

### 8.2 Slice B - Forms And Dialogs

Приоритетные файлы:

- create/edit dialogs under `AssistantTools`, `ApiServers`, `Collections`, `EvaluationSets`, `Jobs`, `Prompts`, `Retrieval`.
- `web/apps/@ipr/magnet-admin/src/components/Agents/FeedbackModal.vue`
- `web/apps/@ipr/magnet-panel/src/components/base/ErrorDialog.vue`
- `web/apps/@ipr/magnet-panel/src/components/Agent/FeedbackModal.vue`

Goals:

- Стандартизировать forms на `DsField` + `DsInput`/`DsTextarea`/`DsSelect` или cleaned `KmFormField` pattern.
- Заменить local `.q-field__control` hacks на field variants/tokens.
- Стандартизировать dialog footer/actions на `DsDialog`/`KmDialog` с explicit controlled close behavior.
- Привести validation messages, required labels, disabled/read-only states и loading states к одному контракту.

Exit criteria:

- Form CSS не таргетит `.q-field*` или `.q-textarea`.
- Common form layout представлен DS/pattern components.
- Dialogs имеют accessible title/description и keyboard close behavior.

### 8.3 Slice C - Tables, Lists, Pagination

Приоритетные файлы:

- list pages using `KmDataTable`.
- `web/apps/@ipr/magnet-admin/src/assets/layout.css` table sections.
- `web/apps/@ipr/magnet-admin/src/components/KnowledgeGraph/Metadata/MetadataFieldsTable.vue`.

Goals:

- Сделать `KmDataTable` source of truth для sticky header, horizontal scroll, empty/loading/fetching states, row click, pagination, density.
- Удалить global `.sticky-virtscroll-table .q-table*` rules.
- Заменить Cypress `.q-table` selectors на `data-test="km-data-table"`, `data-test="table-row"` или feature-specific hooks.
- Expose documented slots/props для column alignment, wrapping, truncation, actions, row states.

Exit criteria:

- Table behavior живет в `KmDataTable`/`DsTable`, не в global CSS.
- Нет `.q-table*` selectors.
- List pages используют единый page/table pattern.

### 8.4 Slice D - KnowledgeGraph Complex UI

Приоритетные файлы:

- `web/apps/@ipr/magnet-admin/src/components/KnowledgeGraph/common/KgDropdownField.vue`
- `web/apps/@ipr/magnet-admin/src/components/KnowledgeGraph/common/KgPromptSection.vue`
- `web/apps/@ipr/magnet-admin/src/components/KnowledgeGraph/Metadata/MetadataFieldDialog.vue`
- `web/apps/@ipr/magnet-admin/src/components/KnowledgeGraph/Metadata/SmartExtractionFieldDialog.vue`
- `web/apps/@ipr/magnet-admin/src/components/KnowledgeGraph/Retrieval/RetrievalTabControls.vue`
- `web/apps/@ipr/magnet-admin/src/components/KnowledgeGraph/Sources/SourcesTab.vue`
- `web/apps/@ipr/magnet-admin/src/components/KnowledgeGraph/EntityExtraction/EntityExtractionTab.vue`

Goals:

- Заменить custom dropdown/input/menu hacks на stable DS primitives.
- Если KnowledgeGraph нужен specialized field/dropdown pattern, создать app-level `Kg*` pattern, который composes DS primitives вместо patching internals.
- Удалить `v-ripple` и list item Quasar vocabulary.
- Consolidate action menus, confirm dialogs, inline editors.

Exit criteria:

- KnowledgeGraph controls не зависят от `.q-field*`, `.q-item*`, `.q-virtual-scroll*`, `.q-tooltip`, `.q-focus-helper`.
- Complex controls документированы как app patterns или generic DS enhancements.

### 8.5 Slice E - Conversation, Search, Retrieval, Agent Workflows

Приоритетные файлы:

- `web/apps/@ipr/magnet-admin/src/components/Conversation/**`
- `web/apps/@ipr/magnet-admin/src/components/Retrieval/**`
- `web/apps/@ipr/magnet-panel/src/components/Search/**`
- `web/apps/@ipr/magnet-panel/src/components/Retrieval/**`
- `web/apps/@ipr/magnet-panel/src/components/Agent/**`
- shared components in `web/packages/ui-comp/src/components/**`

Goals:

- Стандартизировать message cards, toolbars, feedback actions, copy buttons, markdown, drawers, tabs, scroll areas.
- Решить, какие components должны жить в `@ui-comp` shared package, а какие в app-local patterns.
- Заменить `.q-icon` CSS на `KmGlyph`/`KmIcon` styling или documented icon props.
- Убедиться, что panel и admin используют одинаковое DS behavior там, где workflows общие.

Exit criteria:

- Shared chat/retrieval/search UI использует DS patterns вместо app-specific patches.
- Panel не содержит `.q-icon`, `v-close-popup` или Quasar-shaped dialog close behavior.

### 8.6 Slice F - Dashboard And Remaining CRUD Pages

Goals:

- Перевести оставшиеся create/edit/list/detail pages на те же page patterns.
- Удалить duplicated `.km-input:not(.q-field...)` hacks из create/page components.
- Нормализовать toolbar/search/new-button/table layout.
- Уменьшить one-off scoped CSS, когда есть DS utility или pattern.

Exit criteria:

- Remaining CRUD screens используют consistent page, form, table patterns.
- Audit counts по Quasar selectors и legacy layout classes идут к zero.

## 9. Phase 5 - Product Patterns And Documentation ✅ DONE

Цель: не собирать одну и ту же композицию вручную после стабилизации primitives.

### Candidate Patterns

Создавать только когда минимум три экрана требуют одинаковую структуру:

| Pattern | Possible home | Purpose |
|---|---|---|
| `DsPage` / `KmPage` | `@ds` или app shared | Page padding, width, scroll contract. |
| `KmListPage` | app shared или `@ds/components/patterns` | Header, search, actions, table body. |
| `KmDetailLayout` | app shared | Title/details/actions/tabs layout. |
| `KmFormDialog` | `@ds` domain | Dialog with form body, footer, loading, validation. |
| `KmActionMenu` | `@ds` domain | Standard Reka menu для row/page actions. |
| `KmFilterPanel` | app shared | Filter groups, reset/apply actions. |
| `KmEmptyState` | already exists | Ensure it covers list/table/section empty states. |
| `KmInlineEdit` | `@ds` domain if generic | Replace popup-edit style flows. |

### Documentation Tasks

1. Добавить `web/packages/ds/COMPONENT_STATUS.md`:
   - primitive stable/experimental/deprecated status
   - domain stable/legacy/product-specific status
   - replacement guidance
2. Добавить examples для high-use primitives и patterns.
3. Добавить migration guide:
   - Quasar prop vocabulary -> DS prop vocabulary
   - `row`/`column` -> CUBE composition
   - `.q-field` hacks -> field variants/tokens
   - `v-close-popup` -> controlled open state
   - `.q-table` -> `KmDataTable`
4. Рассмотреть lightweight DS playground на существующем VitePress/docs tooling до добавления Storybook/Histoire.

Exit criteria:

- Новый агент может из docs понять, какой component использовать.
- Deprecated legacy APIs имеют documented replacement.
- Product patterns предотвращают появление нового one-off CSS.

## 10. Phase 6 - Testing, Visual QA, Accessibility Gates

Цель: сделать дизайн-систему безопасной для дальнейшего развития.

### 10.1 Automated Tests

Tasks:

1. Добавить unit/component tests для primitive families из Phase 1.
2. Добавить tests для global hosts:
   - toast appears and closes
   - confirm dialog resolves true/false
   - loading overlay increments/decrements correctly
3. Добавить tests для наиболее используемых domain components:
   - `KmBtn`
   - `KmInput`
   - `KmSelect`
   - `KmDialog`
   - `KmDataTable`
   - `KmMenu`
   - `KmTabs`
4. Добавить route-level smoke tests для main workflows:
   - login/auth shell
   - один CRUD list/detail/create flow
   - KnowledgeGraph metadata flow
   - Retrieval/Search/Agent panel flow
   - table sorting/pagination
   - dialogs/menus/selects

### 10.2 Visual QA

Tasks:

1. Определить viewport matrix:
   - mobile narrow
   - tablet
   - desktop
   - wide desktop
2. Определить theme matrix:
   - default light
   - dark, если supported
   - salesforce
   - siebel
3. Захватывать screenshots для каждого migrated slice перед удалением compatibility CSS.
4. Проверять:
   - text overflow
   - overlapping controls
   - table scroll behavior
   - popover/dialog positioning
   - visible focus rings
   - disabled/loading/error states

### 10.3 Accessibility

Tasks:

1. Добавить keyboard walkthroughs для:
   - dialogs
   - menus
   - select/combobox
   - tabs
   - table sorting/pagination
2. Запускать axe или аналог, если доступен, для migrated screens.
3. Проверить labels/errors для forms.
4. Проверить screen reader names для icon buttons и close buttons.
5. Проверить focus return after dialogs/popovers close.

Exit criteria:

- Primitive и domain tests есть для high-risk components.
- Migrated slices имеют visual smoke coverage.
- Accessibility checks покрывают все Reka overlay/selection components.

## 11. Phase 7 - Final De-Compat And Cleanup

Цель: удалить старый мост после перестройки UI на новую систему.

Final deletion checklist:

1. `rg "from ['\"]quasar|import .*['\"]quasar" web` -> zero.
2. `rg "@quasar/extras" web` -> zero, кроме historical docs, если они намеренно оставлены.
3. `rg "v-close-popup|v-ripple" web/apps web/packages` -> zero.
4. `rg "\.q-[A-Za-z0-9_-]+" web/apps web/packages` -> zero live selectors.
5. `rg "--q-|var\(--q-" web/apps web/packages` -> zero outside historical docs.
6. No dynamic `var(--q-${...})` strings in `web/packages/ds`.
7. No `.row`/`.column`/`.col-*` usage that depends on Quasar semantics; remaining generic utilities documented as DS-owned or deleted.
8. No Cypress selectors depend on Quasar classes.
9. Remove no-op `close-popup` directive registration.
10. Remove legacy compatibility stylesheet imports.
11. Remove or move `@ds/compat` helpers if all call sites migrated.
12. Update `QUASAR_TO_REKA_MIGRATION_PLAN.md` to point at this plan as active post-migration design-system refactor.
13. Update package lockfile after dependency removal.
14. Run final build/lint/test/smoke for admin and panel.

Exit criteria:

- Frontend можно объяснить без упоминания Quasar, кроме historical docs.
- Новый UI начинается с documented primitives и patterns.
- Compatibility code удален или изолирован с explicit owners и deletion dates.

## 12. Рекомендуемый Порядок Исполнения

1. Phase 0: audit script, docs correction, guardrails.
2. Phase 1.1 и 1.2: tokens и CUBE layers.
3. Phase 1.3 и 1.4: primitive review и tests для high-use primitives.
4. Phase 2.1: classify `Km*` components.
5. Phase 2.2: central color resolver и remove dynamic `--q-*` fallbacks.
6. Phase 3.1: remove `@quasar/extras`.
7. Phase 3.2 и 3.3: remove `v-close-popup` and `v-ripple`.
8. Phase 4 Slice A: shell/navigation/menus.
9. Phase 4 Slice B: forms/dialogs.
10. Phase 4 Slice C: tables/lists/pagination.
11. Phase 4 Slice D: KnowledgeGraph complex UI.
12. Phase 4 Slice E: conversation/search/retrieval/agent workflows.
13. Phase 4 Slice F: dashboard and remaining CRUD pages.
14. ✅ Phase 5: promote repeated compositions into patterns and docs. — `KmListPage` extracted, 13 pages migrated, `COMPONENT_STATUS.md` created.
15. Phase 6 (in progress): expand tests, visual QA, accessibility gates.
    - ✅ 6.1 first slice: vitest config + jsdom shim for `@ds` (`packages/ds/vitest.config.ts`, `vitest.setup.ts`), `nx run ds:test` target. **120 tests across 20 files** covering: action/form primitives (`DsButton`, `DsInput`, `DsTextarea`, `DsLabel`, `DsCheckbox`, `DsSwitch`, `DsRadioGroup`, `DsNumberField`), overlay/selection primitives (`DsDialog`, `DsPopover`, `DsTooltip`, `DsDropdownMenu`, `DsSelect`), domain wrappers (`KmBtn`, `KmInput`, `KmDialog`, `KmTabs`), and hosts (`toastStore`, `dialogStore`, `loadingStore`). Test pattern documented in `web/packages/ds/COMPONENT_STATUS.md` (Testing section).
    - 🐛 Real bugs surfaced and fixed by tests: `DsCheckbox` and `DsSwitch` were passing `:checked`/`@update:checked` instead of Reka's actual `:model-value`/`@update:model-value` — they were silently uncontrolled in production. `DsTooltip` had a slot condition `v-if="$slots.default && !$slots.trigger"` that was the inverse of the documented usage; rich-content tooltips never rendered when both `trigger` and `default` slots were supplied. `DsInput` and `DsTextarea` did not expose `focus()` / `blur()` / `select()` so `<KmInput ref>.focus()` silently did nothing.
    - ⏳ Remaining: data-display primitives (`DsTable`, `DsPagination`, `DsAccordion`, `DsTabs` direct), more domain wrappers (`KmDataTable`, `KmSelect`, `KmMenu`, `KmCard`), route-level smoke tests for main workflows, visual QA matrix (light/dark/salesforce/siebel × mobile/tablet/desktop/wide), and axe a11y runs on migrated screens.
16. Phase 7: final de-compat cleanup. ✅ All 12 migration metrics at 0 per latest `yarn audit:ds-migration` run; no further code work needed.

## 13. Definition Of Done

Проект считается завершенным, когда:

- `Ds*` primitives имеют semantic APIs, Reka-backed behavior там, где нужно, tokenized styling, keyboard/focus coverage и tests.
- `Km*` components либо stable Magnet domain components, либо явно deprecated legacy adapters.
- App UI не зависит от Quasar class names, variables, directives, package assets или prop vocabulary.
- Local scoped CSS не патчит internals DS components. Нужная кастомизация exposed через DS props, slots, CSS variables, documented classes или product patterns.
- Основные admin и panel workflows build, lint, smoke test и проходят visual/a11y checks по согласованной viewport/theme matrix.
- Documentation объясняет, как строить новый UI из tokens, CUBE composition, `Ds*` primitives и product patterns.

## 14. Notes For Future Agents

- Начинай каждую задачу с audit script из Phase 0, когда он появится.
- Если screen refactor показывает missing primitive state, сначала исправь primitive.
- Не добавляй новые compatibility aliases ради одного экрана. Добавь DS token, variant, slot или pattern.
- Предпочитай удаление dead Quasar-era CSS слепому переводу.
- Считай `@ui-comp` compatibility bridge, а не destination architecture.
- Держи `magnet-panel` в scope. Там все еще есть `v-close-popup` и `.q-icon` remnants, а workflows общие с admin.
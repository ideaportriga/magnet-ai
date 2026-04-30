# CUBE CSS Architecture Roadmap

Дата: 2026-04-28

Scope: текущая frontend-архитектура Magnet после Quasar -> Reka/CUBE migration: `@ds`, `@themes`, `@ui-comp`, `magnet-admin`.

Основано на исследовании в `CUBE_CSS_RESEARCH.md`, Every Layout от Andy Bell и Heydon Pickering, текущих repo notes, `REKA_CUBE_UI_REFACTOR_PLAN.md`, `REKA_CUBE_COMPONENT_VARIANTS_AUDIT.md`, `web/packages/ds`, `web/packages/themes` и `web/apps/@ipr/magnet-admin`.

## Executive Summary

Архитектура уже близка к целевой: есть `@ds/styles`, tokens, reset, CUBE composition/utilities, Reka-backed `Ds*` primitives, domain-layer `Km*`, theme mode через `data-theme`, dev UI gallery и первые DS tests.

Оставшаяся работа не про замену фреймворка. Она про закрепление дизайн-системы как публичного контракта:

- убрать stale migration-документацию и формально описать CUBE/DS правила;
- закрепить Every Layout как источник composition-паттернов и intrinsic layout правил;
- перевести layout debt с `.row/.column/.col-*` на composition primitives;
- закрыть arbitrary visual props в `Km*` через semantic display/tone APIs;
- централизовать motion, overlay, portal и theme contracts;
- дать visual/a11y gates, чтобы новый стиль не расползался.

## Progress

Обновлено 2026-04-28:

- **Phase 0 started:** `web/packages/ds/README.md` приведен к текущей архитектуре `@ds`: удалены claims про `compat/`, `v-close-popup` и transitional `--q-*`; добавлены CUBE class-order, `data-*` exceptions, Reka portal/overlay notes и ссылки на CUBE docs.
- **Phase 0 contract hardening:** Every Layout зафиксирован как первичный источник для composition слоя: `stack`, `cluster`, `sidebar`, `switcher`, `center`, `flow` и `frame` должны использовать intrinsic/browser-driven layout вместо локальных spacing and breakpoint fixes.
- **Phase 0 debt reduced:** неиспользуемый `.q-space` alias удален из `web/packages/ds/src/utilities/layout.css`; `qCssSelectors` baseline снижен до 0.
- **Phase 4 started:** добавлены motion presets в `web/packages/ds/src/tokens/motion.css`; `LayoutDefault.vue` переведен с локальных `0.15s/0.2s ease` transitions на DS motion tokens.
- **Phase 8 guardrails started:** `web/scripts/audit-ds-migration.mjs` расширен метриками `transitionAll` и `templateVisualProps`, чтобы новый motion/visual-prop долг не рос поверх baseline.
- **Phase 4 debt reduced:** `transition: all` удален из DS primitives `DsInputOTPSlot` и `DsSidebarRail`; `transitionAll` baseline снижен 26 -> 24.
- **Phase 4 debt reduced:** dropdown controls в `KnowledgeGraph/Retrieval/RetrievalTabControls.vue` переведены с `transition: all` на `--ds-transition-colors`; `transitionAll` baseline снижен 24 -> 20.
- **Phase 4 debt reduced:** KG retrieval/source interaction surfaces в `KnowledgeGraph/Playground/RetrievalTestDrawer.vue` и `KnowledgeGraph/common/KgDropdownField.vue` переведены с `transition: all` на явные DS motion properties; `transitionAll` baseline снижен 20 -> 13.
- **Phase 4 debt reduced:** metadata/retrieval dialog interaction surfaces в `KnowledgeGraph/Metadata/SmartExtractionFieldDialog.vue`, `KnowledgeGraph/Metadata/MetadataFieldDialog.vue` и `KnowledgeGraph/Retrieval/StructureGuideDialog.vue` переведены с `transition: all` на явные DS motion properties; `transitionAll` baseline снижен 13 -> 9.
- **Phase 4 debt reduced:** оставшиеся tracked `transition: all` hits в `KnowledgeGraph/common/KgTileSelect.vue`, `KnowledgeGraph/Retrieval/ToolSection.vue`, `KnowledgeGraph/Sources/SourceTypeAvatar.vue`, `KnowledgeGraph/Metadata/MetadataFieldsTable.vue`, `KnowledgeGraph/DataExplorer/DocumentDetails.vue`, `Agents/DrawerPreview.vue`, `Collections/FileUrlUpload.vue`, `DeepResearch/Runs/Details.vue` и `packages/ui-comp/src/components/Agent/Message.vue` заменены на явные motion properties; `transitionAll` baseline снижен 9 -> 0.
- **Phase 2 started:** первый admin shell micro-slice заменил header spacer `.col` на `.km-space` в `LayoutDefault.vue`.
- **Phase 2 debt reduced:** оставшиеся header `col-auto` в `LayoutDefault.vue` заменены на CUBE utility `flex-none`; добавлен audit metric `legacyLayoutClasses` для контроля нового layout debt. Initial baseline: 885 class attributes.
- **Phase 2 debt reduced:** detail shell components `Layouts/DetailsLayout.vue`, `Layouts/Details/Header.vue` и `Layouts/Details/SubHeader.vue` переведены с `col` / `col-auto` flex-sizing helpers на `flex-1` / `flex-none`; `legacyLayoutClasses` baseline снижен 885 -> 877.
- **Phase 2 debt reduced:** `Agents/TimelineStep.vue` и `Agents/DrawerPreview.vue` переведены с legacy `col` / `col-auto` / `col-1` sizing helpers на `flex-1`, `flex-none`, `km-space` и локальные fixed-basis block classes; `legacyLayoutClasses` baseline снижен 877 -> 841.
- **Phase 2 debt reduced:** `Dashboard/Drawer/Llm.vue` и `Dashboard/Drawer/Rag.vue` заменили `col-6` form/group layouts на локальные two-column grid compositions, а оставшиеся `col-auto` spacers на `km-space` / `flex-none`; `legacyLayoutClasses` baseline снижен 841 -> 805.
- **Phase 2 debt reduced:** `DeepResearch/Configs/Details.vue` и `DeepResearch/Runs/Details.vue` переведены на composition-first layouts через `flex-1`, `flex-none`, full-width sections и локальные stats/meta patterns; `legacyLayoutClasses` baseline снижен 805 -> 770.
- **Phase 2 debt reduced:** `RAG/retrieve.vue`, `ModelProviders/Settings.vue` и `Collections/scheduler.vue` очищены от remaining `col` / `col-auto` / `col-*` helpers через flex utilities, label/value patterns и локальные grids; `legacyLayoutClasses` baseline снижен 770 -> 731.
- **Phase 2 debt reduced:** `Retrieval/retrieve.vue` и `Dashboard/Tab/Agent.vue` очищены от remaining `col` / `col-auto` / `col-12` helpers через `flex-1`, `flex-none`, `km-space` и `full-width`; `legacyLayoutClasses` baseline снижен 731 -> 707.
- **Phase 2 debt reduced:** `Jobs/Drawer.vue`, `Observability/Traces/details.vue` и `Collections/DrawerChunk.vue` переведены на composition-first layouts через `flex-1`, `flex-none` и локальный drawer meta-grid; `legacyLayoutClasses` baseline снижен 707 -> 674.
- **Phase 2 debt reduced:** `Retrieval/postprocess.vue`, `Agents/CreateNewTopic.vue`, `PromptQueue/Details.vue` и `ApiKeys/CreateNew.vue` очищены от remaining `col` / `col-auto` / `col-6` helpers через `flex-1`, `flex-none`, `km-space`, `full-width` и локальный prompt grid; `legacyLayoutClasses` baseline снижен 674 -> 639.
- **Phase 2 corrective pass:** `Jobs/Drawer.vue` corrected from a risky `col-6 -> flex-1` replacement to an explicit two-column settings grid so the former layout proportions remain stable.
- **Phase 2 debt reduced:** `KnowledgeGraph/ContentProfiles/ContentConfigDialog.vue` and NoteTaker tabs (`Bot.vue`, `Integrations.vue`, `PostProcessing.vue`, `Prompts.vue`, `MSTeams.vue`) очищены от remaining layout helpers через `flex-1`, `flex-none` и локальные grid patterns; `legacyLayoutClasses` baseline снижен 639 -> 592.
- **Phase 2 debt reduced:** EvaluationJobs family (`detailsCompare.vue`, `settingsRag.vue`, `recordsCompare.vue`, `detailsJob.vue`, `detailsTool.vue`, `block.vue`, `settings.vue`, `Page.vue`, `Drawer.vue`, `records.vue`) and `config/evaluation_jobs/component/VariantName.vue` очищены от remaining `col` / `col-auto` helpers через `flex-1`, `flex-none` and local two-column grids where equal field proportions mattered; `legacyLayoutClasses` baseline снижен 592 -> 536.
- **Phase 2 completed:** финальный broad cleanup заменил remaining audited `row` / `column` / `col` / `col-auto` / numeric `col-*` helpers across Vue class attributes на `cluster`, `stack`, `flex-1`, `flex-none` and new `basis-*` / `basis-md-*` utilities; `legacyLayoutClasses` baseline снижен 536 -> 0.
- **Phase 2 current baseline:** audit snapshot после полного cleanup: `legacyLayoutClasses: 0`, `transitionAll: 0`, `qCssSelectors: 0`.
- **Phase 3 started:** `basis-*` utilities documented in `@ds` as the sanctioned fixed-basis replacement for numeric `col-*`; first NoteTaker drawer visual-prop slice moved chips/loaders/default primary buttons from raw `color` / `text-color` props to semantic `tone` or component defaults; `templateVisualProps` baseline снижен 865 -> 855.
- **Phase 3 batched cleanup:** добавлен component-aware analyzer/rewriter for template visual props; первый safe defaults batch removed default `km-loader` / `km-toggle` color props, ignored `km-tabs` visual props, common brand chip recipes, and default solid primary button color; `templateVisualProps` baseline снижен 855 -> 621.
- **Phase 3 glyph tone contract:** `KmGlyph` получил semantic `tone` API (`brand`, `subtle`, `muted`, `weak`, `success`, `warning`, `danger`, etc.) with legacy `color` fallback; второй batched rewrite перевёл static glyph color recipes на `tone` или component default; `templateVisualProps` baseline снижен 621 -> 472.
- **Phase 3 button tone contract:** `KmBtn` получил semantic `tone`, `interactionTone` и `iconTone` APIs with legacy `color` / `icon-color` / hover fallback; третий batched rewrite перевёл common static button recipes на semantic contract; `templateVisualProps` baseline снижен 472 -> 316.
- **Phase 3 chip tone batch:** добавлен conservative `phase3-chip-tones` rewrite для static `KmChip` recipes (`light`, `in-progress`, brand/success/danger neutrals) с сохранением dynamic status expressions; `templateVisualProps` baseline снижен 316 -> 268.
- **Phase 3 parser-backed tone pass:** `template-visual-props` теперь корректно проходит nested Vue slot templates; safe defaults/glyph/button/chip rules rerun on newly visible tags, and `KgDialogSection` получил semantic `tone` API for icon/focus affordance with legacy `icon-color` fallback; `templateVisualProps` baseline снижен 268 -> 254.
- **Phase 3 badge tone batch:** добавлен conservative `phase3-badge-tones` rewrite для static `KmBadge` recipes and exact dynamic status maps (`coming soon`, boolean `Yes`, router, expiring soon); `templateVisualProps` baseline снижен 254 -> 231.
- **Phase 3 chip/button continuation:** `phase3-chip-tones` теперь покрывает exact dynamic chip status maps (runtime loaded, settings/profile states, model source/type, webhook/action states) and safe static chip recipes (`primary/white`, `in-progress/text-gray`); `phase3-button-tones` covers non-solid `grey-7 -> weak` plus ignored `svg-icon` `icon-color` cleanup; `templateVisualProps` baseline снижен 231 -> 196.
- **Phase 3 computed chip status cleanup:** evaluation/job/dashboard status components now expose `KmChip tone` directly instead of computed legacy `color` / `textColor` pairs; inert `div :color` / `:text-color` leftovers in evaluation metric cells removed; `templateVisualProps` baseline снижен 196 -> 156.
- **Phase 3 avatar tone API:** `KmAvatar` получил semantic `tone` API for repeated brand identity markers, and `phase3-avatar-tones` converts safe static avatar recipes (`primary-bg/white`, `primary-light/primary`) while leaving dynamic KnowledgeGraph/source imagery recipes untouched; `templateVisualProps` baseline снижен 156 -> 144.
- **Phase 3 score/accent continuation:** `DsBadge`/`KmChip` now expose a semantic `score` tone for repeated score chips, `KmGlyph` now exposes an `accent` tone for KnowledgeGraph teal glyphs, and safe DeepResearch/Observability status chips moved to semantic tones; `templateVisualProps` baseline снижен 144 -> 135.
- **Phase 3 control-default cleanup:** `phase3-control-defaults` removed ignored/default visual props from control wrappers (`KmBtnToggle`, `KmLinearProgress`, `KmInnerLoading`, `KmSlider`, `KmOptionGroup`, `KmRadio`, `KmSelect`, `KmSelectFlat`, `KmInput`) plus inert `KmBtn text-color` / `KmIcon color` leftovers; warning glyphs moved from `yellow-8` to `tone="warning"`; `templateVisualProps` baseline снижен 135 -> 89.
- **Phase 3 dynamic glyph/default continuation:** exact dynamic `KmGlyph :color` status/brand recipes moved to `:tone`, default `KmLoader`/`KmTimeline` primary colour props were removed, and the remaining static `KgDialogSection icon-color="teal"` moved to `tone="accent"`; `templateVisualProps` baseline снижен 89 -> 82.
- **Phase 3 semantic controls continuation:** `KmIconBtn`, `KmTimelineEntry`, `KmBtnDropdown`, `KmToggle`, and `KmSeparator` now expose semantic `tone` / `selected` surfaces for repeated selected, timeline, dropdown, toggle, and separator recipes; KnowledgeGraph source-kind and DeepResearch step glyphs moved to semantic tones; inert `KmChip` hover props removed; `templateVisualProps` baseline снижен 82 -> 60.
- **Phase 3 product-pattern tone cleanup:** navigation selected state, KG action buttons, ToolSection variants, file/chunk badges, prompt mode toggles, panel hint buttons, and destructive confirm actions now use `selected`, `variant`, or `tone` APIs (`accent`, `neutral-strong`, `danger-soft` included) instead of raw visual props; `templateVisualProps` baseline снижен 60 -> 29.
- **Phase 3 feature visual-prop closure:** remaining app-level visual props were migrated to semantic tones/themes (`SourceTypeAvatar`, hidden pin buttons, prompt/file/dashboard/KG states, warning/error banners, panel error dialog, dashboard chips). Feature template debt now reports `templateVisualProps: 0`.
- **Phase 3 guardrail hardening:** the sanctioned DS fallback allowlist now lives in one shared script module and currently has no entries; audit reports `sanctionedTemplateVisualFallbacks: 0`, so baseline check blocks growth in both feature visual props and DS compatibility fallbacks.
- **Phase 4 keyframe contract:** `tokens/motion.css` now owns shared keyframes for spin, dot pulse/wobble, attention wobble, fade, scale, slide, and collapse effects; repeated DS spinners/loaders, ui-comp retrieval dots, admin three-body loader, KG status spin, and 19 duplicated admin `.wobble` blocks now reference the shared DS keyframes.
- **Phase 4 overlay primitive consolidation:** dialog/menu keyframes now live in `tokens/motion.css` instead of sibling primitives, so `DsAlertDialog`, `DsPopover`, and `DsSelect` no longer depend on another component's style block; Sheet/Drawer/Sidebar overlays, Sheet/Sidebar slides, Accordion/Collapsible collapse, Tooltip/Combobox/HoverCard scale, ContextMenu menu motion, and NavigationMenu fade/slide/zoom now reuse shared DS keyframes.
- **Phase 4 checkpoint:** Phase 4 is intentionally parked as partially complete. Completed scope: motion presets, `transitionAll: 0`, shared keyframes, repeated loader/dot/wobble cleanup, and DS primitive overlay/menu/collapse keyframe consolidation. Remaining scope: high-traffic hardcoded motion recipes, reduced-motion/overlay smoke, and a decision for component-specific toast/progress/skeleton/caret keyframes.
- **Phase 5 started:** `@ds` README now documents the stable Reka primitive part contract for triggers, overlays, content, items, arrows, viewports, labels, and separators so portaled/headless styling has a central DS-owned target.
- **Phase 5 guardrails and cleanup:** audit now tracks scoped DS/internal deep selectors and the legacy app z-index scale. The `--km-z-*` scale has been removed from `magnet-admin`, and all 46 scoped DS/internal deep selectors were replaced with wrapper-owned styles or removed as stale. Both `deepDsSelectors` and `kmZIndexTokens` are baseline-guarded at `0`.

Первый layout migration family для Phase 2: **admin shell + repeated action/filter toolbars**. Начинать стоит с header/sidebar/workspace toolbar and list-page action bars, потому что там больше всего repeated `.row/.column/.col-auto` и Quasar-shaped button props, но поверхность достаточно стабильная для маленьких срезов.

Before:

```html
<div class="row items-center q-gutter-sm">
  <km-btn flat dense color="primary" />
  <div class="col" />
</div>
```

After:

```html
<div class="cluster" data-align="center" data-gap="sm">
  <KmBtn variant="tertiary" size="sm" />
  <div class="km-space" />
</div>
```

## Текущее Состояние

### Что Уже Хорошо

- `web/packages/ds/src/styles.ts` подключает tokens, composition и utilities как отдельные CUBE слои.
- `web/packages/ds/src/reset/index.css` заменяет Quasar reset и содержит `prefers-reduced-motion` guard.
- `web/packages/ds/src/composition` уже содержит Every Layout-inspired primitives: `stack`, `cluster`, `sidebar`, `switcher`, `center`, `flow`, `frame`.
- `web/packages/ds/src/tokens` содержит color, spacing, typography, radii, elevation, motion, z-index, component tokens.
- Reka UI активно используется в primitives: Dialog, Select, Combobox, Menu, Popover, Slider, Tabs, Accordion, Switch, Checkbox и другие.
- Компоненты уже часто используют CUBE-friendly exceptions: `data-state`, `data-variant`, `data-size`, `data-tone`, `data-display`, `data-shape`.
- Brand theme и light/dark mode уже разделены: brand грузится через `@themes`, color mode применяется через `<html data-theme>`.
- `web/scripts/ds-migration-baseline.json` показывает чистую миграционную поверхность для Quasar imports, extras, directives, `--q-*`, compat imports, deep selectors и `qCssSelectors`.
- В `web/packages/ds/src/**/*.spec.*` уже есть 20 spec-файлов для hosts, primitives и domain компонентов.

### Снятые Метрики

Короткий `rg` snapshot от 2026-04-27:

| Метрика | Count | Что означает |
|---|---:|---|
| Legacy layout class hits: `row`, `column`, `col*` | 3028 | Layout migration еще основной фронт работ. Count грубый, но хорошо показывает масштаб. |
| Hardcoded motion hits | 159 | Есть локальные `0.15s ease`, `transition: all`, локальные `@keyframes`. |
| `km-btn` / `KmBtn` usages | 663 | Domain wrapper доминирует над `DsButton`. |
| `km-input` / `KmInput` usages | 507 | Формы все еще в основном через compatibility/domain layer. |
| `km-select` / `KmSelect` usages | 161 | Select migration уже направлена в DS, но product code еще legacy-shaped. |

## Главные Проблемы

### 1. Документация И Контракты Нужно Держать Синхронными

Исходный риск Phase 0 был в том, что `web/packages/ds/README.md` все еще описывал `compat/`, `v-close-popup` и transitional `--q-*` aliases, хотя baseline уже показывал `dsCompatImports: 0`, `qCssVariables: 0`, `vClosePopup: 0`. Первый срез обновил README; дальше важно держать roadmap, audit baseline и public DS vocabulary синхронными.

Риск: новые изменения снова начнут ориентироваться на старую картину и случайно вернут Quasar vocabulary.

### 2. Layout Debt Все Еще Quasar-Shaped

`web/packages/ds/src/utilities/layout.css` сохраняет `.row`, `.column`, `.col-*`, `.col-auto`, `.km-space` как compatibility utilities. В templates все еще много usage.

Риск: CUBE composition будет формально существовать, но реальные экраны продолжат мыслить grid/flex через Quasar-классы.

### 3. Theme Tokens Смешивают Несколько Уровней

`colors.css` содержит brand, semantic, component, product/status/chat/table tokens в одном файле. Часть имен все еще legacy-semantic: `--ds-color-white` в dark mode является surface, `--ds-color-black` означает primary text, `--ds-color-seemless` содержит typo/legacy vocabulary.

Риск: новые темы будут сложны в поддержке, потому что непонятно, какие токены являются raw palette, какие semantic, а какие product-specific.

### 4. `@themes` Пересекается С `@ds`

`web/packages/themes/src/base/app.css` содержит typography classes, global utility aliases (`.overflow-hidden`, `.border-radius-*`, `.width-*`, `.height-*`, `.round`), control styles и CDN imports для Geist fonts.

Риск: два глобальных источника utility/typography могут расходиться. Темы становятся не только override-слоем, но и вторым design-system layer.

### 5. Motion Не Централизован

Есть `web/packages/ds/src/tokens/motion.css`, но app/components продолжают использовать hardcoded transitions и локальные keyframes. В одном только quick snapshot 159 hardcoded motion hits.

Риск: разные экраны ощущаются по-разному, а темы не могут управлять motion signature.

### 6. Варианты Компонентов Все Еще Слишком Свободные

`REKA_CUBE_COMPONENT_VARIANTS_AUDIT.md` уже описывает нужное направление, но в app code еще много arbitrary props: `flat`, `dense`, `color`, `text-color`, `hover-bg`, `rounded`, `borderless`, `active-color`.

Риск: пользовательский интерфейс будет визуально дрейфовать, даже если все компоненты технически идут через `Km*`.

### 7. App-Level CSS Несет Системные Решения

`web/apps/@ipr/magnet-admin/src/assets/layout.css` содержит page containers, z-index scale `--km-z-*`, border utilities, list/detail wrappers, card-grid styles. Часть этого уже выглядит как DS/product-pattern слой, а не app-only CSS.

Риск: другие apps (`magnet-panel`, будущие surfaces) не получат тот же контракт или начнут копировать CSS.

### 8. Нет Cascade Layer Contract

В `web/packages/ds/src` нет `@layer`. Сейчас порядок держится import order. Это нормально для текущей стадии, но с ростом DS/app/theme CSS будет сложнее объяснять precedence.

Риск: чтобы выиграть specificity, разработчики начнут добавлять более длинные selectors или `!important`.

### 9. Headless Portal/Overlay Contract Нужно Закрепить

Reka UI требует, чтобы проект сам задавал functional styles для overlay/content. В primitives это уже частично есть, но roadmap должен сделать это явным: stable part classes, z-index, portal styling, `data-state` animation, `asChild` triggers.

Риск: новые Dialog/Popover/Menu variations начнут стилизоваться из parent scoped CSS и снова появятся fragile overrides.

## Target Architecture

```text
App feature screens
  -> Product pattern components: list page, detail shell, filter bar, form dialog, action toolbar
    -> Stable Magnet domain components: KmDataTable, KmFilterBar, KmDialog, KmChip, KmBtn, KmSelect
      -> Reka-backed Ds primitives: DsButton, DsInput, DsSelect, DsDialog, DsMenu, DsPopover
        -> CUBE CSS: composition, utilities, blocks, data-* exceptions
          -> Tokens: semantic --ds-* + brand/mode overrides
```

Ownership rules:

| Слой | Владеет | Не владеет |
|---|---|---|
| Tokens | Значения, semantic aliases, theme overrides | One-screen fixes |
| Composition | Layout algorithms and rhythm | Цвет, shadow, typography |
| Utilities | Одноцелевые helpers | Component identity |
| Ds primitives | Accessibility, Reka behavior, functional styles, base visual shell | Business logic, Quasar vocabulary |
| Km domain | Magnet defaults, product semantics, compatibility translation | Unlimited visual freedom |
| Product patterns | Повторяемые workflows | Low-level Reka details |
| Feature screens | Data, copy, feature composition | DS internals and arbitrary visual recipes |

### Every Layout Composition Contract

Every Layout — основной источник практических layout-паттернов для composition слоя Magnet. CUBE определяет ownership CSS-слоя; Every Layout определяет self-governing алгоритмы для boxes.

Правила:

- Layout should be context-driven. Prefer browser algorithms (`gap`, `flex-wrap`, `flex-basis`, `min/max-inline-size`, `aspect-ratio`, logical properties) over manual viewport breakpoints and fixed pixel dimensions.
- Spacing is a relationship between siblings. Use `stack` / `flow` / `cluster` and tokenized `data-gap` or spacing utilities on relationship boundaries. Do not encode rhythm as child `margin-bottom` or empty spacer elements.
- `stack` owns vertical rhythm for semantically distinct blocks. Nest smaller stacks for local sub-rhythm instead of creating one-off scoped spacing classes.
- `flow` owns typographic rhythm inside rich text, markdown, prose, and generated content.
- `cluster` owns horizontal grouping and wrapping. Add `data-wrap="no"` only for true single-row controls such as toolbars and segmented actions.
- `sidebar` owns two-part layouts where one side has an intrinsic or target width and the other side consumes remaining space.
- `switcher` owns equal sibling groups that should switch directly between horizontal and vertical arrangements based on available container width.
- `center` owns constrained centered content using `max-inline-size`, not fixed width.
- `frame` owns media/aspect-ratio boxes instead of padding-bottom hacks or per-call-site height guesses.
- Feature scoped CSS may define product blocks, but should not define classes whose only job is `gap`, `margin`, `padding`, `flex`, `min-h-0`, or wrapper rhythm already covered by composition/utilities.

Review smell: if a template combines `stack data-gap`, default component margins, extra `mt-*`, and local `padding-block` around the same boundary, calculate the total rhythm or simplify to one owner.

## Roadmap

### Phase 0. Зафиксировать Контракт И Документацию

Priority: High

Deliverables:

- [x] Обновить `web/packages/ds/README.md`: убрать deleted `compat/`, `v-close-popup`, transitional `--q-*` claims; описать текущие слои `tokens`, `composition`, `utilities`, `reset`, `primitives`, `domain`, `hosts`.
- [x] Добавить ссылку на `CUBE_CSS_RESEARCH.md` и этот roadmap из `REKA_CUBE_UI_REFACTOR_PLAN.md` или `web/packages/ds/README.md`.
- [x] Описать class ordering policy: block -> composition -> token utilities -> narrow helpers; exceptions через `data-*`.
- [x] Зафиксировать public API vocabulary: `variant`, `display`, `tone`, `shape`, `size`, `state`.
- [x] Обновить migration baseline notes: `qCssSelectors: 1` нужно либо объяснить как allowed historical hit, либо довести до 0.

Definition of done:

- New docs match actual files.
- No doc claims about removed compat surfaces.
- Audit command documented and current baseline checked in.

### Phase 1. Token Taxonomy И Theme Contract

Priority: High

Deliverables:

- Разделить color token documentation на группы: base palette, semantic, component, product/domain.
- Ввести или документировать missing semantic tokens: `surface`, `surface-muted`, `text-muted`, `focus-ring`, `selection-bg`, `danger` aliases alongside current `error` if both terms remain.
- Решить legacy names: `--ds-color-white`, `--ds-color-black`, `--ds-color-seemless`. Не обязательно сразу удалить, но новые компоненты должны использовать semantic aliases.
- Описать brand vs mode: brand theme overrides and color mode overrides не должны конфликтовать. Рассмотреть `data-brand` как явный DOM contract, если theme loader будет усложняться.
- Сверить `@themes` font loading: `base/app.css` сейчас импортирует Geist через CDN; если локальные font assets должны быть source of truth, убрать CDN path из target architecture.

Definition of done:

- Новые DS components используют semantic color tokens, не legacy color names.
- Dark mode smoke-test покрывает controls, menus, dialogs, table, chips.
- Brand theme can override tokens without editing component CSS.

### Phase 2. Composition-First Layout Migration

Priority: High

Deliverables:

- Разбить 3028 legacy layout class hits на категории: true layout, harmless utility, generated/docs, domain component internals.
- Для app screens мигрировать вертикальными срезами:
  - toolbars: `.row items-center q-gutter-*` -> `.cluster` + `data-gap`;
  - forms: `.column` -> `.stack`;
  - detail pages: nested row/col -> `sidebar`, `switcher`, product shell;
  - cards/lists: fixed `.col-*` -> CSS grid/product pattern.
- Для новых и touched layouts применять Every Layout decision tree: `stack` for vertical rhythm, `flow` for prose, `cluster` for inline groups, `sidebar` for two-part layouts, `switcher` for equal responsive siblings, `center` for constrained content, `frame` for media ratio.
- Убирать one-off spacing classes and empty spacer elements when composition or token utilities can own the relationship.
- Не удалять `.row/.column/.col-*` сразу. Сначала пометить как legacy compatibility в docs, потом добавить lint/audit guard для новых usages.
- Перенести repeated app layout primitives из `magnet-admin/src/assets/layout.css` в DS/product pattern layer, если они нужны нескольким apps.

Definition of done:

- New code examples use CUBE composition.
- New code examples follow Every Layout-style intrinsic patterns before viewport breakpoints.
- Legacy layout count decreases per slice.
- `.row/.column/.col-*` remain only in compatibility zones or old screens.

### Phase 3. Component Variant Freeze

Priority: High

Deliverables:

- Использовать матрицу из `REKA_CUBE_COMPONENT_VARIANTS_AUDIT.md` как официальный target display contract.
- Для chips/badges/status первым делом перевести arbitrary `color/text-color` recipes в `display/tone/shape`.
- Для buttons перевести common recipes в target variants: `primary`, `secondary`, `tertiary`, `outline`, `danger`, `link`, `icon`, `menu-trigger`.
- Для inputs/selects описать display modes: `text-field`, `search-field`, `textarea-field`, `inline-edit-field`, `simple-select`, `filter-select`, `multi-tag-select`.
- Добавить dev warnings или lint rule для новых arbitrary visual props после того, как mapping готов.

Definition of done:

- UiGallery показывает canonical and legacy lanes.
- New feature code can be reviewed by semantic display/tone language.
- Arbitrary visual props are compatibility-only.

### Phase 4. Motion System

Priority: Medium-High

Status: **Partially complete / parked**. The guardrail-critical and repeated
primitive motion work is done; keep the remaining app-level/hardcoded motion
audit as a later Phase 4 follow-up while Phase 5 starts.

Deliverables:

- [x] Расширить `web/packages/ds/src/tokens/motion.css` presets:
  - `--ds-transition-colors`
  - `--ds-transition-opacity`
  - `--ds-transition-transform`
  - `--ds-transition-shadow`
  - `--ds-transition-overlay-enter`
  - `--ds-transition-overlay-exit`
- [x] Создать DS motion module для shared keyframes: fade, scale, slide, collapse, spinner/dots where appropriate.
- [x] Перевести DS overlays/menus/popovers/dialogs/collapse primitives на `data-state` animations backed by shared DS keyframes.
- [x] Довести `transition: all` до нуля и baseline-guard it through `transitionAll`.
- [ ] Аудит remaining hardcoded motion recipes (`0.15s`, local one-off keyframes) in high-traffic app/product components.
- [ ] Решить, какие component-specific keyframes (`toast`, `progress`, `skeleton`, `caret`) остаются локальными, а какие нужно поднять в `motion.css`.
- [ ] Убедиться, что `prefers-reduced-motion` остается global guard and smoke-check overlay/menu/dialog exit animations.

Definition of done:

- No new `transition: all` in app/DS code.
- Repeated local `wobble`, `bounce`, `fade`, `scale` keyframes either centralized or justified.
- Reka exit animations work for Dialog/Popover/Menu without JS hacks.

### Phase 5. Headless/Overlay Contract

Priority: Medium-High

Status: **In progress**. Stable Reka primitive parts are documented in
`web/packages/ds/README.md`; audit guardrails now keep parent deep selectors
and legacy `--km-z-*` tokens at zero while implementation follow-ups verify each
primitive against that contract.

Deliverables:

- [x] Для Reka-backed primitives описать stable parts/classes: trigger, content, item, overlay, arrow, viewport, label, separator.
- [x] Добавить audit metrics для `:deep()` into DS/domain/headless internals and legacy `--km-z-*` token usage.
- [x] Запретить styling portaled content из parent scoped CSS как default pattern через zero-baseline audit guardrail.
- [x] Проверить z-index: `--km-z-*` in app layout duplicates `--ds-z-*`; выбрать один public scale.
- [ ] Для triggers использовать `asChild` + `DsButton/KmBtn`, чтобы не было nested interactive elements.
- [ ] Проверить functional styles for Dialog/Popover/Menu/Select/Tooltip: max sizes, scroll behavior, overlay, collision states, focus ring.

Definition of done:

- Overlay/menu/popover styling can be changed centrally.
- New Reka usage has no private `:deep()` dependency.
- Z-index scale documented and not duplicated.

### Phase 6. Product Pattern Layer

Priority: Medium

Deliverables:

- Выделить повторяющиеся patterns из app CSS/screens:
  - list page shell;
  - detail page shell;
  - filter toolbar;
  - action toolbar;
  - form dialog;
  - empty/loading/error state;
  - card grid.
- Решить, где живут patterns: `web/packages/ds/src/components/domain` или app-specific package.
- Перевести `.collection-container`, `.km-page-card`, `.agents-grid`, `.agent-card` в named product patterns или documented app-only blocks.

Definition of done:

- Новые CRUD/list/detail pages собираются из patterns, а не копируют local CSS.
- App CSS становится тоньше и содержит только shell-specific decisions.

### Phase 7. Cascade Layers Spike

Priority: Medium

Deliverables:

- Провести spike с `@layer ds.reset, ds.tokens, ds.composition, ds.utilities, ds.components, ds.patterns, app`.
- Проверить Vite import order, Vue scoped style output, theme CSS order, portal components.
- Не мигрировать все сразу. Начать с global DS CSS entrypoints.
- Если spike не дает пользы, зафиксировать отказ и оставить import-order contract.

Definition of done:

- Принято решение: внедряем поэтапно или явно не внедряем.
- Есть visual smoke results for admin shell, dialog/menu/select, dark mode.

### Phase 8. Tests, Gallery, Guardrails

Priority: Medium

Deliverables:

- Продолжить DS specs для primitives with state: keyboard, focus, `data-state`, controlled/uncontrolled behavior.
- Добавить visual smoke для `/dev/ui-gallery`: light/dark, core components, overlay states.
- Добавить audit/lint checks:
  - [x] no new `.row/.column/.col-*` growth through `legacyLayoutClasses` audit baseline;
  - no new arbitrary `color/text-color/bg/hover-bg` where semantic API exists;
  - [x] no `transition: all` growth through `transitionAll` audit baseline;
  - [x] no arbitrary visual-prop growth through `templateVisualProps` audit baseline;
  - [x] no `:deep()` into DS internals growth through `deepDsSelectors` audit baseline;
  - [x] no legacy `--km-z-*` scale growth through `kmZIndexTokens` audit baseline;
  - no CDN font imports if local assets are the target.
- Сохранять audit counts in reports after major slices.

Definition of done:

- PR can fail on design-system regression before manual QA.
- Gallery is a review surface, not only a demo page.

## Suggested Order

1. Phase 0: update docs and baseline explanation.
2. Phase 4 small win: add motion presets, stop new `transition: all`.
3. Phase 2 first vertical slice: admin shell/header/list page layout classes -> CUBE composition.
4. Phase 3 chips/buttons: migrate high-visibility arbitrary color recipes.
5. Phase 5 overlay/menu/select contract.
6. Phase 1 token taxonomy cleanup, because it will be easier after variant pressure is visible.
7. Phase 6 product patterns.
8. Phase 7 cascade layer decision.
9. Phase 8 visual/lint gates hardened throughout.

## Immediate Next Tasks

- [x] Correct the risky `col-6 -> flex-1` replacement in `Jobs/Drawer.vue` with an explicit grid pattern.
- [x] Finish the NoteTaker tabs layout family.
- [x] Continue Phase 2 with the next measured hotspots, especially `EvaluationJobs/*` and remaining list/action surfaces.
- [x] Close the remaining audited `legacyLayoutClasses` backlog to zero with a final measured broad pass.
- [x] Review whether the new `basis-*` utilities should be promoted in DS docs as the sanctioned fixed-basis replacement for numeric `col-*` compatibility helpers.
- [x] Start Phase 3 with a small semantic visual-prop slice now that Phase 2 has reached zero.
- [x] Add a repeatable visual-prop analyzer/rewriter and run the first high-confidence batch.
- [x] Add a DS-level `KmGlyph` tone contract and batch-migrate static glyph colors.
- [x] Continue Phase 3 with a DS-level button tone/intent contract for the remaining `color`, `icon-color`, and hover-color recipes.
- [x] Continue Phase 3 with the safe static chip/status visual recipes (`km-chip color/text-color`).
- [x] Make the visual-prop rewriter nested-template aware and rerun high-confidence defaults/glyph/button/chip rules.
- [x] Add a KnowledgeGraph dialog-section `tone` contract for static icon/focus colour recipes.
- [x] Continue Phase 3 with badge tone recipes and exact dynamic badge status maps.
- [x] Continue Phase 3 with exact dynamic chip status tone maps plus safe button follow-ups.
- [x] Continue Phase 3 with computed chip status components (`:color="color"`) and dashboard/conversation status chips.
- [x] Continue Phase 3 with avatar tone API follow-ups for repeated static identity recipes.
- [x] Continue Phase 3 with score chip recipes and KG accent glyph follow-ups.
- [x] Continue Phase 3 with control-specific ignored/default visual props.
- [x] Continue Phase 3 with exact dynamic glyph tone and default wrapper follow-ups.
- [x] Continue Phase 3 with selected/icon-button/timeline/dropdown/toggle/separator tone follow-ups.
- [x] Continue Phase 3 with product-pattern button/chip/avatar/status recipes that now have semantic homes.
- [x] Triage the remaining `templateVisualProps` backlog: close feature-level visual props and explicitly allowlist only sanctioned DS wrapper compatibility fallbacks.
- [x] Continue Phase 3 guardrail hardening: centralize the sanctioned DS fallback allowlist and track it as a baseline-guarded audit metric.
- [x] Remove the remaining sanctioned DS fallback bindings after verifying there are no external call-sites.
- [ ] Plan the broader legacy visual-prop prop deprecation path for DS wrappers (`color`, `bg`, `textColor`, `iconColor`) that are now style-level compatibility only.
- [x] Start Phase 4 keyframe centralization: add shared DS keyframes and migrate repeated loaders/spinners/dots/wobble blocks.
- [x] Continue Phase 4 with overlay primitive keyframe consolidation for dialog/menu/sheet/drawer/sidebar/navigation/collapse primitives.
- [x] Park Phase 4 as partially complete with explicit remaining motion follow-ups.
- [x] Start Phase 5 by documenting the stable Reka primitive part/class contract in `@ds` README.
- [x] Continue Phase 5 by adding baseline-guarded audit metrics for `:deep()` into DS internals and `--km-z-*` duplication.
- [x] Remove the remaining `--km-z-*` scale from `magnet-admin/src/assets/layout.css` and `App.vue`; keep `kmZIndexTokens` at `0`.
- [x] Reduce `deepDsSelectors` from `46` to `0`, including KnowledgeGraph wrapper hotspots (`KgDropdownField`, `KgExpandablePrompt`, `KgPromptSection`, `KgDialogSection`) and remaining one-off selectors.
- [ ] Continue Phase 5 by checking `asChild` trigger forwarding and functional styles for Dialog/Popover/Menu/Select/Tooltip.
- [ ] Later Phase 4 follow-up: remaining high-traffic hardcoded motion recipes and component-specific toast/progress/skeleton/caret keyframe decision.

## Non-Goals

- Не переписывать все `Km*` usages на `Ds*` immediately. `Km*` can be a valid Magnet domain layer.
- Не удалять legacy layout utilities до завершения screen migration.
- Не внедрять `@layer` без visual smoke.
- Не делать тему через локальные overrides в feature components.
- Не копировать старый Quasar visual API as the new public API.

## Success Criteria

- New UI can be themed by overriding tokens, not rewriting components.
- Common screens share product patterns instead of repeated local CSS.
- Layout is intrinsic and context-driven: composition primitives own rhythm/wrapping before feature CSS adds local fixes.
- Reka primitives are styled through public DS classes and `data-*` states.
- Components expose semantic variants, not arbitrary color recipes.
- Motion feels consistent and uses tokens.
- Dark/light and future brand themes remain first-class, not afterthoughts.

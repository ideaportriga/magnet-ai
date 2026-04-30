# Component Status

This document tracks the status of all components in the design system and related product patterns.

## Primitives (`src/components/primitives/`)

Reka-UI-based headless primitives. All are **stable** unless noted.

| Primitive | Status | Notes |
|---|---|---|
| Accordion | stable | |
| Alert | stable | |
| AspectRatio | stable | |
| Avatar | stable | Use `KmAvatar` domain wrapper for standard sizes |
| Badge | stable | Use `KmBadge` domain wrapper |
| Breadcrumb | stable | |
| Button | stable | Use `KmBtn` domain wrapper for branded variants |
| ButtonGroup | stable | |
| Calendar | stable | Use `KmDate` domain wrapper |
| Card | stable | Use `KmCard` domain wrapper |
| Carousel | stable | |
| Checkbox | stable | Use `KmCheckbox` domain wrapper |
| Collapsible | stable | |
| Combobox | stable | |
| Command | stable | |
| ContextMenu | stable | |
| Dialog | stable | Use `KmDialog` domain wrapper |
| Drawer | stable | Use `KmDrawer` / `KmDrawerLayout` domain wrappers |
| Empty | stable | Use `KmEmptyState` domain wrapper |
| Field | stable | |
| Form | stable | |
| HoverCard | stable | |
| Input | stable | Use `KmInput` domain wrapper |
| InputGroup | stable | |
| InputOTP | stable | |
| Item | stable | |
| Kbd | stable | |
| Label | stable | |
| Menu | stable | Use `KmMenu` domain wrapper for legacy Quasar-style anchor menus. New code should reach for `DsDropdownMenuRoot` + sub-components (`Trigger`, `Content`, `Item`, `Separator`, `Sub`, `SubTrigger`, `SubContent`, `Label`, `Group`, `CheckboxItem`, `RadioGroup`, `RadioItem`, `Shortcut`) for proper a11y, keyboard nav, and submenu support. The convenience `DsDropdownMenu` wrapper (flat `items` array) remains for simple cases. |
| Menubar | stable | |
| NativeSelect | stable | |
| NavigationMenu | stable | |
| NumberField | stable | |
| Pagination | stable | |
| PinInput | stable | |
| Popover | stable | Use `KmPopover` domain wrapper |
| Progress | stable | Use `KmLinearProgress` domain wrapper |
| Radio | stable | Use `KmRadio` domain wrapper |
| RangeCalendar | stable | |
| Resizable | stable | |
| ScrollArea | stable | Use `KmScrollArea` domain wrapper |
| Select | stable | Use `KmSelect` domain wrapper |
| Separator | stable | Use `KmSeparator` domain wrapper |
| Sheet | stable | |
| Sidebar | stable | |
| Skeleton | stable | |
| Slider | stable | Use `KmSlider` domain wrapper |
| Sonner | stable | Used by toast host |
| Spinner | stable | Use `KmLoader` domain wrapper |
| Stepper | stable | Use `KmStepper` / `KmStep` domain wrappers |
| Switch | stable | Use `KmSwitch` domain wrapper |
| Table | stable | Use `KmDataTable` domain wrapper for full feature set |
| Tabs | stable | Use `KmTabs` / `KmTab` domain wrappers |
| TagsInput | stable | Use `KmChipsInput` domain wrapper |
| Textarea | stable | |
| Toggle | stable | Use `KmToggle` domain wrapper |
| Tooltip | stable | Use `KmTooltip` domain wrapper |

---

## Domain Components (`src/components/domain/`)

Opinionated wrappers and compound components that map design tokens to primitives.

| Component | Status | Replaces / Notes |
|---|---|---|
| KmAvatar | stable | |
| KmBackground | stable | |
| KmBadge | stable | |
| KmBanner | stable | |
| KmBtn | stable | |
| KmBtnDropdown | stable | |
| KmBtnExpandDown | stable | |
| KmBtnLoader | stable | |
| KmBtnToggle | stable | |
| KmCard | stable | |
| KmCheckbox | stable | |
| KmChip | stable | |
| KmChipCopy | stable | |
| KmChipsInput | stable | |
| KmCodemirror | stable | |
| KmConfirmAction | stable | |
| KmDataTable | stable | Replaces Quasar `q-table` |
| KmDate | stable | |
| KmDialog | stable | Replaces Quasar `q-dialog` |
| KmDrawer | stable | Replaces Quasar `q-drawer` |
| KmDrawerLayout | stable | |
| KmDrawerResizeHandle | stable | |
| KmEmptyState | stable | |
| KmErrorDialog | stable | |
| KmExpansionItem | stable | Replaces Quasar `q-expansion-item` |
| KmFilePicker | stable | |
| KmFilterBar | stable | |
| KmGlyph | stable | |
| KmIcon | stable | |
| KmIconBtn | stable | |
| KmIconPicker | stable | |
| KmImage | stable | |
| KmInnerLoading | stable | Replaces Quasar `q-inner-loading` |
| KmInput | stable | Replaces Quasar `q-input` |
| KmInputFlat | stable | |
| KmInputListAdd | stable | |
| KmJsonEditor | stable | |
| KmLinearProgress | stable | Replaces Quasar `q-linear-progress` |
| KmLoader | stable | Replaces Quasar `q-spinner` |
| KmLocaleSwitcher | stable | |
| KmMarkdown | stable | |
| KmMenu | stable | Replaces Quasar `q-menu` |
| KmNavBtn | stable | |
| KmNavSection | stable | |
| KmNotificationText | stable | |
| KmOptionGroup | stable | |
| KmPicker | stable | |
| KmPopover | stable | |
| KmPopupConfirm | stable | Replaces Quasar `q-dialog` confirm pattern |
| KmPopupEdit | stable | |
| KmRadio | stable | Replaces Quasar `q-radio` |
| KmRange | stable | |
| KmScore | stable | |
| KmScrollArea | stable | Replaces Quasar `q-scroll-area` |
| KmSection | stable | |
| KmSelect | stable | Replaces Quasar `q-select` |
| KmSelectFlat | stable | |
| KmSeparator | stable | Replaces Quasar `q-separator` |
| KmSlideTransition | stable | |
| KmSlider | stable | Replaces Quasar `q-slider` |
| KmSliderCard | stable | |
| KmStep | stable | |
| KmStepper | stable | |
| KmSwitch | stable | Replaces Quasar `q-toggle` |
| KmTab | stable | Replaces Quasar `q-tab` |
| KmTabPanel | stable | Replaces Quasar `q-tab-panel` |
| KmTabPanels | stable | Replaces Quasar `q-tab-panels` |
| KmTable | stable | Low-level table; prefer `KmDataTable` for list pages |
| KmTabs | stable | Replaces Quasar `q-tabs` |
| KmTimeline | stable | |
| KmTimelineEntry | stable | |
| KmToggle | stable | |
| KmTooltip | stable | Replaces Quasar `q-tooltip` |
| KmTree | stable | |

---

## Product Pattern Components (`apps/@ipr/magnet-admin/src/components/shared/`)

App-level compositions that codify repeating page structures. Use these instead of assembling the outer shell by hand.

| Component | Status | Slots | Notes |
|---|---|---|---|
| `KmListPage` | stable | `#tabs`, `#toolbar`, `#default`, `#overlays` | Standard admin list page shell: full-height stack, collection-container, card with optional toolbar, main content area, and teleported overlays. Used by 13+ admin pages. |

### `KmListPage` Usage

```vue
<km-list-page>
  <!-- optional: tabs row above the card -->
  <template #tabs>
    <km-tabs v-model="tab" ...>...</km-tabs>
  </template>

  <!-- optional: toolbar inside a cluster (search, actions) -->
  <template #toolbar>
    <div class="col-auto center-flex-y">
      <km-input ... />
    </div>
    <div class="km-space" />
    <div class="col-auto center-flex-y">
      <km-btn ... />
    </div>
  </template>

  <!-- main content: table, card grid, etc. -->
  <km-data-table ... />

  <!-- optional: dialogs and overlays (teleported to body via KmDialog) -->
  <template #overlays>
    <my-create-dialog ... />
    <km-popup-confirm ... />
  </template>
</km-list-page>
```

### Pages Using `KmListPage`

| Page | Tabs | Overlays |
|---|---|---|
| EvaluationSets/Page.vue | — | create-new dialog |
| EvaluationJobs/Page.vue | — | create-new, delete confirm, rerun confirm |
| Prompts/Page.vue | — | create-new dialog |
| DeepResearch/Configs/Page.vue | — | create-new dialog |
| DeepResearch/Runs/Page.vue | — | create-run dialog |
| Retrieval/Page.vue | — | create-new dialog |
| PromptQueue/Page.vue | — | create-new dialog |
| Observability/Traces/Page.vue | — | — |
| ApiKeys/Page.vue | — | create-new, delete confirm |
| Collections/Page.vue | — | create-new dialog |
| ModelConfig/Page.vue | ✓ | create-new dialog |
| AssistantTools/Page.vue | ✓ | API + RAG create dialogs |
| ModelProviders/Page.vue | ✓ | — |

### Pages NOT Using `KmListPage` (by design)

| Page | Reason |
|---|---|
| Agents/Page.vue | Card grid + footer record count row inside card |
| AIApps/Page.vue | Card grid + footer record count row inside card |
| NoteTaker/Page.vue | Conditional card per tab (one tab has no card) |
| KnowledgeProviders/Page.vue | Conditional loading vs card (no toolbar) |
| Settings/Page.vue | Completely different layout (scroll area + multi-table) |
| CollectionItems/Page.vue | Sidebar drawer layout |
| Files/Page.vue | Stats section + scroll area |
| Mcp/Page.vue | Conditional empty state vs. table layout |
| Configuration/Page.vue | Custom layout |

---

## CUBE CSS Compositions (`src/utilities/`)

Layout classes defined in the design system, available globally.

| Class | Type | Description |
|---|---|---|
| `.stack` | CUBE composition | Vertical flex column (`flex-direction: column`) |
| `.cluster` | CUBE composition | Horizontal flex row (`flex-direction: row`) |
| `.collection-container` | utility | Max-width centered page container |
| `.km-space` | utility | Flex spacer (`flex: 1`) |
| `.col` | DS-owned utility | Flex-grow fill (from `layout.css`) |
| `.col-auto` | DS-owned utility | Flex no-grow, size to content (from `layout.css`) |
| `.col-xs-*`, `.col-sm-*`, etc. | DS-owned utility | Responsive width fractions (from `layout.css`) |
| `data-gap` | CUBE attribute | Gap between flex children: `0`, `xs`, `sm`, `md`, `lg`, `xl` |
| `data-justify` | CUBE attribute | `justify-content`: `start`, `end`, `center`, `between`, `around` |
| `data-align` | CUBE attribute | `align-items`: `start`, `end`, `center`, `baseline`, `stretch` |
| `data-wrap` | CUBE attribute | `flex-wrap`: `no` disables wrapping |

---

## CSS Token Reference

Tokens are defined in `src/tokens/` and used via CSS custom properties.

- **Colors**: `--km-color-primary`, `--km-color-surface`, `--km-color-border`, etc.
- **Typography**: `.km-heading-1` through `.km-heading-7`, `.km-body`, `.km-label`, `.km-description`, `.km-field`
- **Spacing**: `p-xs`, `p-sm`, `p-md`, `p-lg`, `p-xl`, `mb-xs` … `mb-xl`, `mx-auto`, etc.
- **Borders**: `.ba-border` (all sides), `.bb-border` (bottom only), `.br-border` (right only)
- **Radius**: `.border-radius-12`
- **Background**: `.bg-white`, `.bg-primary-bg`, `.bg-background`

---

## Migration Reference

### Quasar → DS Component Map

| Quasar | DS Replacement |
|---|---|
| `q-btn` | `km-btn` |
| `q-input` | `km-input` |
| `q-select` | `km-select` |
| `q-dialog` | `km-dialog` |
| `q-card` | `km-card` |
| `q-table` | `km-data-table` |
| `q-tabs` / `q-tab` | `km-tabs` / `km-tab` |
| `q-tab-panels` / `q-tab-panel` | `km-tab-panels` / `km-tab-panel` |
| `q-separator` | `km-separator` |
| `q-toggle` | `km-switch` |
| `q-checkbox` | `km-checkbox` |
| `q-radio` | `km-radio` |
| `q-menu` | `km-menu` |
| `q-tooltip` | `km-tooltip` |
| `q-chip` | `km-chip` |
| `q-inner-loading` | `km-inner-loading` |
| `q-spinner` | `km-loader` |
| `q-scroll-area` | `km-scroll-area` |
| `q-drawer` | `km-drawer` |
| `q-expansion-item` | `km-expansion-item` |
| `q-linear-progress` | `km-linear-progress` |
| `q-slider` | `km-slider` |
| `q-stepper` / `q-step` | `km-stepper` / `km-step` |

### Layout Migration

| Old Pattern | New Pattern |
|---|---|
| `row` class | `cluster` CUBE composition |
| `column` class | `stack` CUBE composition |
| `q-pa-md` | `p-md` |
| `q-mb-md` | `mb-md` |
| `q-mx-auto` | `mx-auto` |
| `full-width full-height` container | `stack full-height` with `data-gap="0"` |

---

## Testing

The `@ds` package has its own Vitest config at `packages/ds/vitest.config.ts` (jsdom + Vue Test Utils). Run the full suite:

```bash
yarn nx run ds:test
# or, directly:
npx vitest run --config packages/ds/vitest.config.ts
```

### Coverage today

| Area | Files | Tests |
|---|---|---:|
| Action / Form primitives | `DsButton`, `DsInput`, `DsTextarea`, `DsLabel`, `DsCheckbox`, `DsSwitch`, `DsRadioGroup`, `DsNumberField` | 51 |
| Overlay / Selection primitives | `DsDialog`, `DsPopover`, `DsTooltip`, `DsDropdownMenu`, `DsSelect` | 23 |
| Domain wrappers | `KmBtn`, `KmInput`, `KmDialog`, `KmTabs` | 33 |
| Hosts | `toastStore`, `dialogStore`, `loadingStore` | 20 |
| **Total** | **20 files** | **120** |

### Adding a test

Spec files live next to the implementation as `*.spec.ts`:

```
src/components/primitives/<Family>/Ds<Component>.vue
src/components/primitives/<Family>/Ds<Component>.spec.ts
```

Cover at minimum:

1. **Renders** — semantic root tag + `data-test` hook present.
2. **Props** — variant / size / state map to `data-*` attributes the CSS relies on.
3. **Model** — `v-model` / `update:*` event round-trip.
4. **A11y / keyboard** — `aria-*` wiring, `Esc` / outside-click for overlays, `disabled` blocks interaction.
5. **Slots** — required slots render; optional slots are conditional.

For overlays (Dialog, Popover, Menu, Sheet) attach to `document.body` so Reka's portal lands in jsdom, and pass at least a `description` slot to silence Reka's a11y warnings:

```ts
mount(DsDialog, {
  props: { open: true },
  slots: { title: () => 't', description: () => 'd', default: () => 'b' },
  attachTo: document.body,
})
```

The setup file (`vitest.setup.ts`) shims `PointerEvent`, `ResizeObserver`, `IntersectionObserver`, and the pointer-capture API that Reka relies on but jsdom doesn't ship.

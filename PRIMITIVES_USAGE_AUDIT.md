# Primitives Usage Audit & Wiring Plan

> Date: 2026-04-26  
> Scope: `web/apps/@ipr/magnet-admin`, `web/apps/@ipr/magnet-panel`, `web/packages/ui-comp`  
> Goal: identify UI surfaces that hand-roll markup or rely on legacy `km-menu`-style markup when a Reka-backed `Ds*` primitive already exists, and wire those surfaces to the proper primitive.

## 0. Summary

The DS package already ships these primitives (see `web/packages/ds/COMPONENT_STATUS.md`):

| Primitive family | Members | Notes |
|---|---|---|
| ContextMenu | `DsContextMenu`, `Trigger`, `Portal`, `Content`, `Item`, `Group`, `Label`, `CheckboxItem`, `RadioGroup`, `RadioItem`, `Separator`, `Shortcut`, `Sub`, `SubTrigger`, `SubContent` | Right-click affordance with submenus, keyboard nav, portal, full a11y. |
| DropdownMenu | `DsDropdownMenu` (only the convenience wrapper today) | The wrapper accepts a flat `items: { label, separator?, onSelect, tone, disabled }[]` array. **Missing sub-component exports** — sub-menus, item groups, dynamic content require Reka primitives directly. We add `DsDropdownMenu*` sub-components mirroring the `DsContextMenu*` family below. |
| Tabs | `DsTabs` (and `KmTabs` / `KmTab` / `KmTabPanels` / `KmTabPanel` wrappers) | Already widely used via the `Km*` wrappers; underline / pill / segmented variants. |
| Separator | `DsSeparator`, `KmSeparator` | Horizontal / vertical, decorative or semantic. |
| Popover / Menu | `DsPopover`, `KmMenu` | `KmMenu` is a popover-anchored menu that **does not handle right-click semantics, sub-menus, keyboard navigation between items, or focus return** — it was a Quasar bridge. New code should reach for `DsContextMenu` / `DsDropdownMenu` instead. |

The audit below catalogs every surface where the wrong abstraction is in play.

---

## 1. Surfaces That Should Use `DsContextMenu`

The current UI fakes a context menu by listening to `@contextmenu.prevent`, opening a `KmMenu` anchored to `event.target`, and rendering a hand-rolled `<ul class="km-list"><li class="km-item">` list. This loses keyboard navigation, ARIA, focus return, and overflow handling.

| File | Current pattern | Correct primitive |
|---|---|---|
| `web/apps/@ipr/magnet-admin/src/components/Layouts/WorkspaceTabBar.vue` | `@contextmenu` → `KmMenu context-menu` over `<li class="km-item">` rows with three `KmSeparator` blocks | `DsContextMenu` + `DsContextMenuTrigger` (per tab) + `DsContextMenuContent` + `DsContextMenuItem` + `DsContextMenuSeparator`. Pin/unpin can stay as a single item; tab actions resolve through the existing handlers. |

> Other places use `@contextmenu` only for native browser menu suppression (no app menu) — no migration needed.

**Fix priority: HIGH** — explicitly named by the user. Implemented in this pass.

---

## 2. Surfaces That Should Use `DsDropdownMenu`

`KmMenu` plus `<ul class="km-list"><li class="km-item">` is the legacy shape. Each one is a dropdown menu attached to a button; almost every site has the same structure (header label, action items, separators, optional submenu).

| File | Current pattern | Correct primitive | Sub-menu? |
|---|---|---|---|
| `web/apps/@ipr/magnet-admin/src/components/LayoutDefault.vue` (user menu, lines 36–72) | `KmMenu` + `<ul class="km-list">` + `<li class="km-item">` for Profile / Locale / Logout, with a nested `KmMenu` for the locale picker | `DsDropdownMenu` + `DsDropdownMenuTrigger` + `DsDropdownMenuContent` + `DsDropdownMenuItem` + `DsDropdownMenuSeparator` + `DsDropdownMenuSub` / `SubTrigger` / `SubContent` for locales | **Yes** |
| `web/apps/@ipr/magnet-admin/src/components/Toolbar.vue` (system menu, lines 47–57) | `KmMenu` + `<ul class="km-list">` + `<li class="km-item">` over `system[]` array | `DsDropdownMenu` (or stay on the convenience wrapper with `items={…}` array) | No |
| `web/apps/@ipr/magnet-admin/src/components/Mcp/Tools.vue`, `web/apps/@ipr/magnet-admin/src/components/Mcp/Details.vue`, `web/apps/@ipr/magnet-admin/src/components/Mcp/ToolDrawer.vue` | Inline `KmMenu` on row hover for "Run / Edit / Delete" | `DsDropdownMenu` |
| `web/apps/@ipr/magnet-admin/src/components/Conversation/MessageDrawer.vue`, `Conversation/Drawer.vue` | Action `KmMenu` next to messages | `DsDropdownMenu` |
| `web/apps/@ipr/magnet-admin/src/components/Dashboard/Drawer/{Llm,Rag}.vue`, `Dashboard/Tab/{Llm,Rag,Agent}.vue` | Header action `KmMenu` for export / config | `DsDropdownMenu` |
| `web/apps/@ipr/magnet-admin/src/components/Agents/{DrawerAction,actionDetails,Channels,ToolSelection}.vue` | Per-row action `KmMenu` | `DsDropdownMenu` |
| `web/apps/@ipr/magnet-admin/src/components/EvaluationJobs/{detailsTool,detailsJob,block,Drawer}.vue` | Action `KmMenu` | `DsDropdownMenu` |
| `web/apps/@ipr/magnet-admin/src/components/{ApiTools,ApiServers,Collections,Configuration,KnowledgeProviders,KnowledgeGraph/Details,ModelConfig,ModelProviders,ModelProviders/{Drawer,ModelDrawer,Page},NoteTaker,Observability/Traces/Drawer,Profile/ProfilePage,Prompts,PromptQueue,Retrieval,Settings,AssistantTools/Page,EvaluationSets,AIApps}/<file>.vue` | Many action `KmMenu` instances | `DsDropdownMenu` |
| `web/apps/@ipr/magnet-panel/src/components/Multi/Tab.vue` | Action `KmMenu` | `DsDropdownMenu` |

**Fix priority:** the user-menu in `LayoutDefault.vue` is HIGH (explicitly named). The rest are MEDIUM — should be batched in a follow-up "menus" slice.

> Note: `DsDropdownMenu` currently exposes only the convenience wrapper. Before migrating sites that need sub-menus (locale picker, nested actions), we ship the missing sub-component primitives mirroring `DsContextMenu*`.

---

## 3. Surfaces That Should Use `DsTabs` / `KmTabs`

Most pages already use `KmTabs` (which wraps `DsTabs`). Two surfaces hand-roll tabs:

| File | Current pattern | Correct primitive |
|---|---|---|
| `web/apps/@ipr/magnet-admin/src/components/Layouts/WorkspaceTabBar.vue` | A horizontal row of `<div class="workspace-tab">` with manual active/dirty/pinned classes, click + middle-click + drag handling | **Stay custom.** This is a workbench-style draggable tab bar (closeable, pinnable, reorderable, with overflow-scroll). `DsTabs` does not model these affordances; promoting it would lose drag, pin, dirty-dot, scroll-buttons, middle-click close. The fix here is not to use `DsTabs` — only the context menu (item 1 above). |
| `web/apps/@ipr/magnet-admin/src/components/AIApps/Page.vue`, `Agents/Page.vue` | Manual filter tab strip with `<button>` per filter | `KmTabs` with `:items` (`variant="pill"` or `"segmented"`) |
| `web/apps/@ipr/magnet-admin/src/components/Observability/Traces/ToolsList.vue`, `ToolCallDisplay.vue`, `KnowledgeGraph/Playground/RetrievalResponseContent.vue`, `RetrievalTestDrawer.vue`, `KnowledgeGraph/DataExplorer/{DocumentDetails,MetadataPanel}.vue`, `KnowledgeGraph/EntityExtraction/EntityColumnsSection.vue`, `KnowledgeGraph/common/KgExpandablePrompt.vue` | Manual `<div>` segmented selectors | `KmTabs` with `variant="segmented"` |

**Fix priority: MEDIUM** — separate slice; not in this pass.

---

## 4. Surfaces That Should Use `DsSeparator` / `KmSeparator`

`KmSeparator` is already used in 81 files. The remaining gaps are:

| Pattern | Where | Correct primitive |
|---|---|---|
| `<div style="border-bottom: 1px solid …" />` or `border-top: 1px solid …` purely as a divider | several `details.vue` and drawer files | `KmSeparator` (already domain-wrapped) |
| `<hr>` | not present (grep returned 0) | n/a |
| Inline border classes (`bb-border` / `bt-border`) on a content row that is *visually* a separator and not a structural border on the row itself | a few details pages | `KmSeparator` for a clearer semantic |

**Fix priority: LOW** — cosmetic; not in this pass.

---

## 5. Other Primitives Worth A Sweep (Lower Priority, Not In This Pass)

| Primitive | Surfaces likely missing it |
|---|---|
| `DsTooltip` / `KmTooltip` | Already widely used; double-check icon-only buttons in `Toolbar.vue` and detail headers expose `tooltip="…"` for a11y. |
| `DsSelect` / `KmSelect` | Already widely used. |
| `DsCombobox` | Used in global search; consider for `KgDropdownField` and any "type-ahead → pick" combos still done with `KmSelect` + filter. |
| `DsAlertDialog` | The destructive confirmations in admin currently go through `KmPopupConfirm`; that wrapper is fine, but new destructive flows should consider `DsAlertDialog` directly. |
| `DsItem` | Could replace the bespoke `<li class="km-item">` markup throughout legacy menus once `DsDropdownMenu*` sub-components land (item 2 above does this). |
| `DsBreadcrumb*` | The header crumb in `LayoutDefault.vue` is a single span + chevron — only one level, so `DsBreadcrumb` is overkill until pages need multi-level paths. |

---

## 6. Plan — What Got Fixed (DONE)

The user explicitly named workspace-tab context menu, separator, tabs, and the user dropdown.

1. ✅ **Added the missing `DsDropdownMenu*` sub-component primitives** (`Root`, `Trigger`, `Portal`, `Content`, `Group`, `Item`, `CheckboxItem`, `RadioGroup`, `RadioItem`, `Label`, `Separator`, `Shortcut`, `Sub`, `SubTrigger`, `SubContent`) so that menu sites with sub-menus, keyboard nav, ARIA, and dynamic content can be migrated. Visuals share `.ds-menu-content` / `.ds-menu-item` with `DsContextMenu*`.
2. ✅ **Globally registered `Ds*` menu primitives** (both `Ds*` and `Ds*Menu*` families) in `web/packages/ui-comp/src/utils/install.ts:46` so admin/panel templates can use them as `<ds-dropdown-menu-…>` without per-file imports — same ergonomics as `<km-*>`.
3. ✅ **Migrated `WorkspaceTabBar.vue` context menu** from `KmMenu` + hand-rolled `<li>` rows to `DsContextMenu*`.
4. ✅ **Migrated `LayoutDefault.vue` user menu** (Profile / Locale submenu / Logout) from `KmMenu` + hand-rolled `<li>` rows to `DsDropdownMenu*`, with nested `DsDropdownMenuSub` for the locale picker.
5. ✅ **Fixed sidebar nav regression** — `KmNavBtn` (`web/packages/ds/src/components/domain/KmNavBtn.vue:14`) was missing the `navigate` emit and `path`/`parentRoute`/`alternativePaths` props after the Quasar removal, so expanded-mode sidebar buttons silently did nothing. Restored the contract with active-state logic.
6. ✅ **Migrated all 16 detail-page show-more menus** — `AIApps/details.vue`, `Agents/details.vue`, `ApiServers/Details.vue`, `ApiTools/details.vue`, `AssistantTools/details.vue`, `Collections/details.vue`, `Configuration/details.vue`, `DeepResearch/Configs/Details.vue`, `EvaluationSets/details.vue`, `KnowledgeProviders/Details.vue`, `Mcp/Details.vue`, `ModelConfig/details.vue`, `ModelProviders/Details.vue`, `NoteTaker/details.vue`, `Prompts/details.vue`, `Retrieval/details.vue` — all from `KmMenu` + `<li class="km-item">` rows to `DsDropdownMenu*`. Destructive items use `variant="destructive"`.
7. ✅ **Migrated `Toolbar.vue` system menu** to `DsDropdownMenu*` with a `DsDropdownMenuLabel` heading (replaces the hand-rolled `header` span).
8. ✅ **Migrated KnowledgeGraph row-action / preset menus** — `EntitiesTable.vue` (×2), `DocumentsTable.vue`, `GuidedExamplesTable.vue`, `ContentProfilesTab.vue`, `EntityExtractionTab.vue`, `Sources/SourcesTab.vue`, `Metadata/MetadataTab.vue` — all to `DsDropdownMenu*`.
9. ✅ Verified both `magnet-admin:build` and `magnet-panel:build`, plus `ds:test` (120 tests).

After this pass, only **two** `<km-menu>` references remain across admin/panel: a doc comment in `Retrieval/MetadataFilterEditor.vue` (already migrated to `DsDropdownMenu`), and `KnowledgeGraph/ContentProfiles/SourceTreeDropdown.vue` (deferred — see §7 below).

---

## 7. Follow-Up Slice (DONE 2026-04-27)

10. ✅ **Migrated `SourceTreeDropdown.vue` to `DsPopover`** — the last admin/panel `<km-menu>` consumer. Drops the custom `.source-dropdown-menu` chrome overrides; outer padding now comes from the DS popover token. Trigger uses `<template #trigger>` with the existing `kg-inline-field`. Only `km-menu` mention left in the repo is a doc comment.
11. ✅ **Extended `KmBtnToggle`** to render its option icon via `KmGlyph` instead of a raw `<i :class="icon">`. Backwards-compatible (FA class strings still work because `KmGlyph` detects whitespace), but now it also accepts Material Symbols (`description`, `hub`, …) and `o_*` outlined names — exactly what was needed to migrate `DataExplorerTab`.
12. ✅ **Migrated `DataExplorerTab.vue`'s view-mode toggle** from a 75-line hand-rolled `view-mode-toggle__*` block (sliding indicator + grid-laid `<button>`s) to a 4-line `<km-btn-toggle :options="viewModeOptions">`. All decorative CSS deleted; behaviour and visual identity preserved. Verified `magnet-admin` and `magnet-panel` builds plus the 120-test DS suite.
13. ✅ **Inventory:** the segmented-strip candidates flagged in the original audit (`Observability/Traces/ToolCallDisplay.vue`, `KnowledgeGraph/Playground/RetrievalResponseContent.vue`, `RetrievalTestDrawer.vue`, `DataExplorer/DocumentDetails.vue`, `DataExplorer/MetadataPanel.vue`, `EntityExtraction/EntityColumnsSection.vue`, `common/KgExpandablePrompt.vue`) all turned out to be **false positives** — no actual segmented selectors. The single real candidate was `DataExplorerTab` (now done). The original audit was speculative.

14. ✅ **Separator sweep (template-level cases)** — `AIApps/Page.vue` and `Agents/Page.vue` had a hard-coded inline `style="border-top: 1px solid rgba(0,0,0,0.12)"` on the records-count footer. Replaced with a preceding `<km-separator />`. The other ~20 hits are CSS rules inside scoped style blocks of complex components (`DocumentDetails`, `MetadataPanel`, `MetadataFieldsTable`, `RetrievalTestDrawer`, …) — those are structural component CSS, not loose template dividers, and migrating them would be a per-file structural refactor with marginal benefit. Flagged below.

15. ✅ **Icon color cascade in menu items** — destructive `<ds-dropdown-menu-item variant="destructive">` recolors the item text red, but `KmGlyph`'s default inline `style="color: var(--ds-color-icon)"` was beating that cascade, leaving icons stuck at icon-grey while the label was red. Routed `KmGlyph`'s color through a `--km-glyph-color` CSS custom property (`web/packages/ds/src/components/domain/KmGlyph.vue:46`) and wired the shared menu styles (`DsContextMenuContent.vue:90`) to set `--km-glyph-color: currentColor` on `[data-variant='destructive']` and `[data-highlighted]` items. Default-state items keep whatever color the caller passed (typically `--ds-color-icon`). Backwards-compatible — no call site changes needed.

16. ✅ **`KgInlineField` focus-visible** — when used as a `DsPopover` trigger via `as-child`, Reka injects `tabindex` so the styled `<span>` is keyboard-focusable. Added a focus-visible outline matching DS conventions (`web/apps/@ipr/magnet-admin/src/components/KnowledgeGraph/common/KgInlineField.vue:48`).

## 8. Out Of Scope (Tracked)

- Scoped `border-bottom: 1px` rules inside complex DataExplorer / Metadata / Playground components. Each one styles a specific subpart's edge (table row, panel section, header cell) — they're load-bearing layout, not visual decoration. Migrate when those components themselves get a structural rewrite, not as part of a divider sweep.
- Removing `KmMenu` itself once the doc-comment reference is rewritten — leave as legacy adapter.
- `KgInlineField` accessibility audit when used as a popover trigger — Reka injects `tabindex`/`aria-*` via `as-child`, but the styled `<span>` may need a focus-visible style.

# Reka/CUBE Component Variants Audit

Date: 2026-04-27

Scope: `Chip`, `Button`, `Input`, `Select`, `Menu`, and `Tab` variants after the Quasar to Reka/CUBE migration. The dev preview page lives at `/dev/ui-gallery` in `magnet-admin` and is registered only when `import.meta.env.DEV` is true.

## Usage Snapshot

The counts below come from `rg` over `web/apps` and `web/packages` and include both PascalCase and kebab-case templates.

| Family | Main usage counts | Notes |
| --- | ---: | --- |
| Chip | `km-chip` 146, `km-badge` 20, `KmChip` 8, `DsBadge` 7 | Most product code still uses domain chips. There are also class-only chip lookalikes such as local status chips. |
| Button | `km-btn` 596, native `button` 54, `KmBtn` 52, `DsButton` 20, `km-icon-btn` 8, `km-nav-btn` 7 | `KmBtn` dominates. Native buttons are now the main inconsistency source in admin screens. |
| Input | `km-input` 479, `KmInput` 22, native `input` 17, `DsInput` 14, `DsTextarea` 9, native `textarea` 5, `DsField` 2 | New primitive path exists but is not yet the default for new forms. Native file inputs are legitimate exceptions. |
| Select | `km-select` 155, `DsSelect` 9, `KmSelect` 2, `KmSelectFlat` 1, `DsNativeSelect` 1 | `KmSelect` already delegates simple cases to `DsSelect`, which is the right direction. |
| Menu | `ds-dropdown-menu` 136, `ds-context-menu` 12, `DsDropdownMenu` 5, `km-menu` 2 | Menu primitives are used heavily through global kebab-case registration; `KmMenu` should remain legacy-only. |
| Tab | `km-tab` 74, `km-tabs` 52, `DsTabs` 3 | Most tabs use legacy child registration. The `items` API is cleaner and easier to audit. |

No live `<q-btn>`, `<q-input>`, `<q-select>`, `<q-menu>`, `<q-tabs>`, `<q-tab>`, or `<q-chip>` call sites remain in app templates. The remaining `q-*` matches are comments and migration notes inside DS wrappers.

## Target Display Contract

The migration should stop exposing visual freedom as a public component API. Product code should not decide component identity by passing arbitrary `color`, `text-color`, `bg`, `hover-bg`, `rounded`, `square`, `borderless`, or local CSS chip/button classes. Those values can still exist inside DS implementation, but call sites should choose from a closed display set.

Three dimensions are allowed:

- **Display**: what role the component plays in the interface, such as `primary-action`, `status-badge`, `search-field`, or `filter-select`.
- **Tone**: semantic meaning, limited to `neutral`, `brand`, `info`, `success`, `warning`, and `danger` when tone is relevant.
- **Shape**: closed shape choice, currently `pill` or `square`. The former `KmChip square` look is preserved as `shape="square"` in the new API.

Everything else should be treated as an implementation detail or a temporary legacy escape hatch. New DS/domain APIs should prefer `display`, `variant`, `tone`, `shape`, `size`, and state (`disabled`, `invalid`, `loading`, `selected`) over token names.

## Visual Surface Inventory

| Family | Visual surfaces found | Main problem |
| --- | --- | --- |
| Chip | `KmChip` accepts arbitrary `color`, `textColor`, `round`, `square`, `dense`, `size`, `labelClass`, `clickable`, `removable`; `KmBadge` accepts arbitrary `color`, `textColor`, `solid/soft/outline`, `dot`, `floating`, `transparent`; `DsBadge` has `primary/secondary/destructive/outline`; local `span/div` chips exist. | Status, tag, score, boolean, source, and filter chips are all encoded as colors/classes instead of named displays. |
| Button | `DsButton` has `primary/destructive/outline/secondary/ghost/link`; `KmBtn` maps `flat/simple/secondary/link` and still allows `color`, `bg`, `hoverColor`, `hoverBg`, `round`, `dense`; native buttons and dropdown button variants remain. | Button purpose is split between variant props, color overrides, icon-only shape, and local/native markup. |
| Input | `DsInput` exposes size only; `KmInput` adds clearable, prefix/suffix, icon, textarea, dense, rounded, borderless, validation, height-like legacy props; `KmInputFlat` covers inline editing. | Search, textarea, inline edit, and plain field are named by prop combinations rather than a target display. |
| Select | `DsSelect` covers simple single select; `KmSelect` adds multi, chips, search, select-all, custom slots, icon prefix, validation; `KmSelectFlat` is a chip-like filter trigger; `DsNativeSelect` is rare. | Simple, advanced, and filter selects are mostly clear, but flat/filter and advanced combinations still drift through prop combinations. |
| Menu | `DsDropdownMenu` object API, Reka primitive menu parts, `KmMenu`, `KmBtn dropdown`, and `KmBtnDropdown` all render similar menus; visual classes are split between `.ds-menu` and `.ds-menu-content/.ds-menu-item`. | The same action menu can be reached through too many component surfaces. |
| Tab | `DsTabs` supports `underline`, `pill`, `segmented`; `KmTabs` accepts the same plus legacy ignored Quasar color/layout props; child `KmTab` registration remains common. | Visual variants are mostly closed, but the legacy API hides tab lists and suggests unsupported visual customization. |

## Migration Matrix

| Family | Freeze / retire | Target display set | Migration target |
| --- | --- | --- | --- |
| Chip | Freeze raw `color`/`textColor` at call sites after semantic mapping lands. Retire local chip-like spans and arbitrary `km-small-chip` composition. | `StatusBadge`, `TagChip`, `FilterChip`, `InputToken`, `CounterBadge`, `DotBadge`. Tones: `neutral`, `brand`, `info`, `success`, `warning`, `danger`. Shapes: `pill`, `square`. | `DsBadge`, `KmChip`, and `KmBadge` now accept `display`, `tone`, and `shape`; map existing color recipes (`primary-light + primary`, `green-2 + green-8`, `error-bg + error-text`, score colors) to semantic tone/display pairs. |
| Button | Freeze `color`, `bg`, `hoverColor`, `hoverBg`, `contentClass` as visual escape hatches. Retire new native action buttons. | `primary-action`, `secondary-action`, `tertiary-action`/ghost, `outline-action`, `danger-action`, `link-action`, `icon-action`, `menu-trigger`, `segmented-toggle`, `nav-action`. | Keep `DsButton` as primitive; `KmBtn variant` now accepts target variants (`primary`, `secondary`, `tertiary`, `outline`, `danger`, `link`) while legacy `flat/simple/color` remains compatibility-only. |
| Input | Freeze `rounded`, `borderless`, ad hoc height/border-radius props for new code. Keep prefix/suffix/clearable as behavior, not visual identity. | `text-field`, `search-field`, `textarea-field`, `inline-edit-field`, `readonly-field`, `secret-field`, `validation-field`. Sizes: `sm`, `md`, `lg`. | Promote search and inline edit to named displays. Keep `DsField + DsInput/DsTextarea` for new code and `KmInput` as a compatibility wrapper until validation-heavy forms move. |
| Select | Freeze hand-rolled popover selects and arbitrary trigger styling. Keep native select only as an explicit platform exception. | `simple-select`, `searchable-select`, `multi-tag-select`, `filter-select`, `native-select`. | Keep `DsSelect` for simple mode, keep Reka Combobox for advanced mode, and make `KmSelectFlat` the named `filter-select` display instead of a separate styling system. |
| Menu | Retire `KmMenu` and `KmBtnDropdown` for new work. Do not add new menu classes outside the DS menu style module. | `action-menu`, `context-menu`, `selection-menu`, `nested-menu`, `danger-item`, `menu-separator`, `menu-label`. | Use `DsDropdownMenu` for flat action lists and Reka primitive wrappers for rich menus. Align `.ds-menu` and `.ds-menu-content/.ds-menu-item` before adding more menu variants. |
| Tab | Retire legacy color props (`active-color`, `indicator-color`, `active-bg-color`) from new code. Migrate away from child registration when touching a screen. | `page-tabs` (`underline`), `local-switch` (`segmented`), `compact-tabs` (`pill`, legacy/narrow contexts only). | Keep `DsTabs` as the canonical implementation. Use `KmTabs :items` for domain code until the remaining `KmTab` child registrations are converted. |

## Migration Plan

1. **Name the target displays in DS.** Add explicit type aliases or docs for each family so component APIs describe role and tone, not color tokens. Started for chips/badges through `DsBadge`, `KmChip`, and `KmBadge` `display/tone/shape` props.
2. **Add compatibility translation in `Km*`.** Keep existing props working, but translate common visual recipes to target displays internally. Started for `KmBtn variant` target aliases and chip/badge semantic props; next step is dev warnings for arbitrary visual props that have a target equivalent.
3. **Migrate high-drift surfaces first.** Start with chips and buttons because they have the widest arbitrary color/class usage. Replace local chip spans and native buttons with named DS/domain components.
4. **Move form controls by behavior.** Migrate simple inputs/selects to `DsField + DsInput/DsSelect`, keep advanced validation/search/multi-select on `Km*` until equivalent DS displays exist.
5. **Collapse menu entry points.** Route flat action lists to `DsDropdownMenu`; reserve primitive menu parts for nested/rich menus; leave `KmMenu` only for legacy attachment semantics until removed.
6. **Convert tabs opportunistically.** When touching a tabbed screen, replace `KmTab` child registration with `items`, and remove ignored Quasar visual props from the call site.
7. **Freeze escape hatches.** After the major mappings are complete, fail lint or emit stronger dev warnings for new arbitrary visual props and class-only component lookalikes.

## Dev Gallery Migration Board

The dev gallery now starts with a migration matrix that mirrors the table above. Each card renders the components that will be migrated in the left lane and the replacement target components in the right lane, so reviewers can visually compare what changes before touching production screens. The target chip examples include `shape="square"` to preserve the previous square chip display without exposing arbitrary border-radius styling.

## Recommended Canonical Paths

### Chip

- Keep `DsBadge` as the primitive for status/counter labels.
- Keep `KmChip` for legacy chip semantics: removable, clickable, icon, legacy colors, and select chips.
- Keep `KmBadge` for badge-specific legacy affordances: dot, floating, soft/solid/outline mapping.
- Deprecate class-only chips (`status-chip`, `km-small-chip` used on arbitrary `div/span`) unless they become a named domain component.
- Unify shape tokens: badge defaults to pill, chip may use pill or compact rectangle, but app-level custom border radii should not decide component identity.

### Button

- Use `DsButton` for new low-level UI and primitive compositions.
- Use `KmBtn` for legacy/admin templates that need the Quasar-compatible prop surface: `flat`, `simple`, `secondary`, `loading`, `icon`, `color`, `bg`, `dropdown`, etc.
- Treat `KmIconBtn`, `KmNavBtn`, `KmBtnToggle`, and `KmBtnDropdown` as specialized domain components, not alternative styling systems.
- Prefer `KmBtn` icon-only or `DsButton size="icon"` over new native `<button>` markup for actions.
- Consolidate dropdown buttons around two patterns: `DsDropdownMenu`/primitive menu for new code, `KmBtn dropdown` only for legacy option arrays. `KmBtnDropdown` overlaps with both and should be reviewed for deprecation.

### Input

- Use `DsField + DsInput/DsTextarea` for new forms.
- Use `KmInput` only when a call site needs legacy validation rules, clearable/prefix/suffix/icon affordances, or migration compatibility.
- Keep `KmInputFlat` only for inline table/list editing.
- Native `<input type="file">` is acceptable for hidden file pickers, but visible file upload UX should go through `KmFilePicker`.
- Avoid new local search/input wrappers unless they are promoted into DS as a primitive or domain component.

### Select

- Use `DsSelect` for simple single-value dropdowns with string values.
- Use `KmSelect` for advanced compatibility: multi-select, chips, search, select-all, custom option slots, validation.
- Use `KmSelectFlat` only for toolbar/filter chip triggers.
- Use `DsNativeSelect` only when platform-native behavior is intentional.
- Avoid hand-rolled popover selects. The existing `KmSelect` advanced path already uses Reka Combobox and should be the single advanced select surface.

### Menu

- Use `DsDropdownMenu` object API for simple action lists.
- Use `DsDropdownMenuRoot/Trigger/Content/Item/...` primitives for rich menus, nested menus, custom triggers, or check/radio items.
- Keep `KmMenu` as a legacy shim for old Quasar attachment semantics only.
- Menu visual classes currently split between `.ds-menu` and `.ds-menu-content/.ds-menu-item`; align these names or expose a shared menu style module before adding more menu variants.

### Tab

- Use `DsTabs` for new tabs with colocated panels.
- Use `KmTabs :items="..."` for admin code that still wants the domain wrapper but can avoid child registration.
- Keep `KmTabs + KmTab + KmTabPanels` for legacy migration compatibility only.
- Migrate legacy `km-tab` child registration opportunistically because it hides the actual tab item list from static review.

## Dev Gallery

- Route: `/dev/ui-gallery`
- File: `web/apps/@ipr/magnet-admin/src/components/Dev/UiGallery.vue`
- Registration: `web/apps/@ipr/magnet-admin/src/router.js`, guarded by `import.meta.env.DEV`
- Bundling guard: `web/apps/@ipr/magnet-admin/src/main.js` excludes `components/Dev/**/*.vue` from the global component glob, so the gallery does not ship as a production async chunk.
- Purpose: a lightweight Storybook-like surface using the real app, real global registrations, real DS CSS layers, and no new dependency.

The gallery intentionally shows both canonical and suspicious variants. It should be kept small and biased toward decision-making, not exhaustive documentation.

## Future Audit Candidates

- `Badge` as a first-class sibling of `Chip`, because `KmBadge`, `DsBadge`, and chip-like local spans overlap.
- `Checkbox`, `Switch`, `Radio`, `Toggle`, `OptionGroup`, because they represent one selection-control family.
- `Dialog`, `Popover`, `Tooltip`, `Drawer`, because they share overlay, portal, focus, and z-index behavior.
- `Table`, `DataTable`, `Pagination`, because table controls often create their own buttons/selects/chips.
- `Date`, `Range`, `Calendar`, `NativeSelect`, because date/range controls mix primitive and domain behavior.
- `FilePicker`, `ChipsInput`, `TagsInput`, because they are compound form controls and can drift from base input/select styling.
- `EmptyState`, `Loader`, `Progress`, `Banner`, because status/feedback surfaces often duplicate spacing and tone tokens.

## Migration Rule Of Thumb

New feature code should start from `Ds*` primitives. Existing admin/domain screens can continue using `Km*` wrappers while migrating. Local class-only components and native controls should either become named DS/domain components or be treated as narrow exceptions with a clear reason.

# UI / Design System Audit Roadmap

Date: 2026-05-19

## Scope

Reviewed the Magnet admin UI and `@ds` package for CUBE CSS, design-system component usage, style-token discipline, repeated patterns, and icon consistency.

## Completed In This Pass

- Replaced the remaining rendered legacy `q-chip` in `NoteTaker/Page.vue` with `KmChip` and semantic `tone` values.
- Converted `RAG/Page.vue` to the existing `KmListPage` product pattern.
- Removed inline `min-block-size: 0` from `KmListPage`, `RAG/Page.vue`, `NoteTaker/Page.vue`, `ApiServers/Page.vue`, and `Mcp/Page.vue` where the `min-h-0` utility already exists.
- Replaced duplicated hand-built empty states in `ApiServers/Page.vue` and `Mcp/Page.vue` with `KmEmptyState`.
- Replaced a leftover Quasar compatibility class `q-ml` in `ModelProviders/ModelDrawer.vue` with `ml-sm`.
- Added the `close` Phosphor alias so `icon="close"` and `name="close"` resolve through `KmGlyph` consistently.
- Replaced the raw removable-chip close SVG in `KmChip` with `KmGlyph` and switched its button base to `DsButton`.
- Updated `KmEmptyState` to use `KmBtn` instead of a hand-rolled button and to use the DS gradient token instead of a local hardcoded gradient.
- Updated `packages/ds/COMPONENT_STATUS.md` to reflect the current product-pattern state.
- Added `UI_AGENT_RULES.md` as a short rules file for future UI-editing agents.

## Current Architecture Snapshot

- `packages/ds/src/tokens/` owns public `--ds-*` tokens.
- `packages/ds/src/composition/` owns CUBE layout primitives.
- `packages/ds/src/utilities/` owns token-driven one-purpose helpers.
- `packages/ds/src/components/primitives/` owns Reka-backed `Ds*` components.
- `packages/ds/src/components/domain/` owns Magnet `Km*` wrappers.
- `apps/@ipr/magnet-admin/src/components/shared/` owns app product patterns such as `KmListPage`.
- `packages/themes/` owns brand/theme overrides and should not become a second feature-style layer.

## Priority Roadmap

### P0: Guardrail Cleanliness

- Run `yarn audit:ds-migration:check` and keep baseline from regressing.
- Run `yarn lint:css:errors` before merging UI changes.
- Keep direct Quasar imports, live `q-*` tags, `.q-*` selectors, `:deep(.ds|.km)` feature selectors, `transition: all`, unprefixed radius tokens, numeric spacing utilities, and legacy `--km-*` typography at zero.
- Add an audit metric for raw native interactive controls in app templates, excluding hidden file inputs.

### P1: Product Pattern Extraction

- Extract a shared card-grid product pattern for `Agents/Page.vue` and `AIApps/Page.vue`; both currently duplicate toolbar, progress, card-grid, card styles, and pagination footer.
- Replace raw card `<button>` elements in that extraction with router-link or DS-backed clickable card semantics.
- Extract provider/secret inline-edit controls shared by `ModelProviders/Settings.vue`, `KnowledgeProviders/Settings.vue`, and `base/SecretsItem.vue`.
- Extract `NoteTakerProviderForm.vue` for the repeated bot/provider form in `NoteTaker/tabs/MSTeams.vue`, `NoteTaker/tabs/Bot.vue`, and `NoteTaker/NoteTakerProviders.vue`.

### P2: Style Debt Reduction

- Reduce inline `style` usage in app templates by replacing repeated `min-block-size`, width, padding, and text wrapping with utilities or small block classes.
- Replace remaining raw native controls in Knowledge Graph and retrieval filter components with `KmBtn`, `KmIconBtn`, `KmInput`, or a DS-backed domain wrapper.
- Move repeated Observability trace result-card chrome into a `TraceResultCard.vue` product component.
- Promote categorical visualization palettes currently hardcoded in feature CSS into explicit `--ds-color-viz-*` tokens after UX review.

### P3: Theme And DS Hardening

- Continue shrinking legacy global helpers in `packages/themes/src/base/app.css`; app-facing utility behavior should live in `@ds`.
- Consider cascade layers for tokens, composition, utilities, blocks, and exceptions once current import-order behavior is stable.
- Replace raw inline SVGs inside DS domain components with `KmGlyph` where the component already lives above the domain layer.
- Consider a primitive icon component before changing inline SVGs inside low-level primitives/hosts.

## Specific Remaining Findings

- `Agents/Page.vue` and `AIApps/Page.vue` are intentionally not fixed here because extraction is a behavior-sensitive product-pattern change.
- `KnowledgeGraph/Details.vue`, `MetadataFieldDialog.vue`, `Retrieval/MetadataFilterChip.vue`, `Retrieval/MetadataFilterCondition.vue`, and `KnowledgeGraph/ContentProfiles/ContentConfigDialog.vue` still contain raw interactive controls.
- Many app templates still contain inline styles for min/max sizes, text wrapping, padding, or dynamic timeline positioning.
- Some DS tokens still contain legacy raw palette values by design; feature code should not copy those literals.

## Verification Commands

Run from `web`:

```bash
yarn audit:ds-migration
yarn audit:ds-migration:check
yarn lint:css:errors
yarn audit:theme-overrides
yarn nx run magnet-admin:build
```

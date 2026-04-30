# Agent Guide — Cube CSS + Reka UI Design System

Authoritative rulebook for any agent (Claude, Codex, Cursor, etc.) editing `web/`.
Read this **before** touching templates or CSS. The DS contract lives in
`packages/ds/README.md` — this file is the operational checklist on top of it.

## TL;DR

- Compose with **`Ds*` primitives → `Km*` domain wrappers → product patterns → scoped CSS** (last resort).
- Layout via **CUBE composition primitives** (`stack` / `cluster` / `sidebar` / `switcher` / `center` / `flow` / `frame`). Never re-declare flex+gap recipes in scoped CSS.
- Style only with **`--ds-*` tokens**. No hex, no rgb(), no raw px in scoped CSS, no inline `style=""` for color/spacing.
- State and variants go through **`data-state` / `data-variant` / `data-tone` / `data-display` / `data-shape` / `data-size`**, not modifier classes.
- Run `yarn audit:ds-migration:check` before commit. Baseline must not regress.

---

## Layer cascade (do not break this order)

```
Tokens (--ds-*)            packages/ds/src/tokens/
  → Composition (.stack…)  packages/ds/src/composition/
    → Utilities (.p-md…)   packages/ds/src/utilities/
      → Blocks (.ds-* .km-*) component scoped CSS
        → Exceptions       data-state / data-variant attributes
```

Each layer may consume layers below it; never reach upward. Imports happen in
`packages/ds/src/styles.ts` — do not change that order without explicit approval.

---

## Component decision tree

When you need a UI element, walk the tree top-down. **Stop at the first match.**

1. **Is it a Reka-backed primitive?** → `Ds*` from `@ds/components/primitives` (`DsButton`, `DsDialog`, `DsSelect`, `DsDropdownMenu`, `DsField`, `DsTabs`, `DsTable`, …).
2. **Does Magnet have a domain wrapper?** → `Km*` from `@ds/components/domain` (`KmBtn`, `KmInput`, `KmDataTable`, `KmDialog`, `KmDrawer`, `KmCard`, …). See full inventory in `packages/ds/COMPONENT_STATUS.md`.
3. **Is the composition repeated 3+ screens?** → Promote to a product pattern (e.g., `KmListPage`).
4. **Truly one-off?** → Vue SFC scoped CSS, but built from composition primitives + utilities + tokens.

**Never** introduce `<button>`, `<input>`, `<select>`, `<dialog>`, `<table>` for interactive UI. Hidden `<input type="file">` and form-tag `<input>` are the only sanctioned exceptions.

### Import paths

The `@ds` root entry only re-exports composables and utils (`useNotify`, `useDialog`, `useScreen`, `resolveDsColor`, …). It does **not** re-export components. For components, choose one of:

- **Globally registered** (preferred for `Km*` consumed in templates): no import needed. `@ui-comp/install` registers every export from `@ds/components/domain` under both PascalCase (`<KmBtn>`) and kebab-case (`<km-btn>`).
- **Explicit subpath import** (when global registration isn't enough — JSX, render functions, dynamic component refs): `import KmFoo from '@ds/components/domain/KmFoo.vue'` or `import { DsButton } from '@ds/primitives'`.

Do **not** write `import { KmFoo } from '@ds'` — it will fail at runtime with `does not provide an export named 'KmFoo'`.

---

## Class order (template style)

```html
<section
  class="km-panel stack p-lg bg-white shadow-sm"
  data-gap="md"
  data-state="open"
>
```

1. Block / pattern (`km-*`, `ds-*`, `workspace-tab`)
2. Composition (`stack`, `cluster`, `sidebar`, `switcher`, `center`, `flow`, `frame`)
3. Token utilities (`p-md`, `gap-lg`, `text-primary`, `bg-surface`, `shadow-sm`, `radius-md`)
4. Narrow helpers (`min-w-0`, `overflow-hidden`, `flex-1`, `basis-6`)
5. State/variant via `data-*` attributes — **never** `.is-open`, `.selected`, `.primary`.

---

## Forbidden patterns

These patterns are **rejected on review**. If you find existing offenders, do not copy them.

### CSS / styling

| Smell | Why it's wrong | Do this instead |
|---|---|---|
| `style="…"` inline (color/spacing/size) | Bypasses tokens & cascade | Scoped class + token, or utility (`p-md`, `bg-surface`) |
| `#hex`, `rgb()`, `rgba()` literals | Bypasses theming + dark mode | `var(--ds-color-*)` semantic token |
| Raw `px` in scoped CSS | Off-scale | `var(--ds-space-*)` / `var(--ds-radius-*)` |
| `var(--radius-lg)` | **Token does not exist — silently resolves to `0`.** Real bug. | `var(--ds-radius-lg)` |
| `var(--km-font-*)`, `var(--km-line-height-*)` | Removed in P5. The alias block in `tokens/typography.css` was deleted; references resolve to `inherit` and break typography. | `var(--ds-font-*)`, `var(--ds-line-height-*)` |
| Custom `@keyframes` for spin/pulse/fade/slide/scale | Drift from DS motion | Reuse keyframes from `tokens/motion.css` |
| `transition: all …` | Layout-jank, perf foot-gun | `var(--ds-transition-colors / opacity / transform / shadow)` |
| Hardcoded duration `0.15s ease` | Off-scale | `var(--ds-duration-*)` + `var(--ds-ease-*)` |
| `:deep(.ds-…)` from feature CSS | Reaches into DS internals — Phase 5 debt, baseline-guarded at 0 | Use semantic prop / slot / CSS variable on the component |
| `.row`, `.column`, `.col-*`, `q-*` | Quasar legacy, removed | Composition primitives, or `basis-*` utilities for 12-col proportions |
| Scoped `display: flex; gap: …` recipes | Duplicates `cluster`/`stack` | `cluster` (horizontal) / `stack` (vertical) with `data-gap` |

### Component API

| Smell | Why it's wrong | Do this instead |
|---|---|---|
| `<KmBtn color="primary" text-color="white">` | Quasar-style visual prop | `<KmBtn variant="primary" tone="brand">` |
| `<KmChip color="green">` | Same | `display="status-badge" tone="success"` |
| `<q-tab>`, `<q-input>`, `<q-table>` | Quasar removed | `KmTabs`, `KmInput`, `KmDataTable` |
| Hand-rolled popover/menu/select markup | Loses a11y + portaling | `DsPopover`, `DsDropdownMenu`, `DsSelect` (Reka primitives) |
| Trigger button wrapped in another button | Nested interactive elements | Reka `asChild` + `KmBtn` |

---

## Tokens — what to use

**Canonical prefix is `--ds-*`.** Anything else is either a deprecated alias or a typo.

| Need | Tokens |
|---|---|
| Text color | `--ds-color-text-primary`, `--ds-color-text-muted`, `--ds-color-fg-*` |
| Surface / background | `--ds-color-background`, `--ds-color-surface`, `--ds-color-surface-elevated` |
| Borders | `--ds-color-border`, `--ds-color-border-subtle` |
| Status | `--ds-color-{success,warning,danger,info}` (+ `-bg`, `-border` variants) |
| Brand / focus | `--ds-brand-accent`, `--ds-brand-focus-ring`, `--ds-brand-selection-bg` |
| Spacing | `--ds-space-{2xs,xs,sm,md,lg,xl,2xl,…}` (semantic) — utility classes `.p-md`, `.gap-lg` consume the same scale |
| Radius | `--ds-radius-{xs,sm,md,lg,xl,full}` |
| Shadow | `--ds-shadow-{sm,md,lg,xl,primary}` |
| Z-index | `--ds-z-{base,sticky,dropdown,overlay,modal,toast,tooltip}` |
| Motion duration | `--ds-duration-{fast,base,slow}` |
| Motion ease | `--ds-ease-{out,in,in-out}` |
| Motion preset | `--ds-transition-{colors,opacity,transform,shadow}` |

If the design needs a value not in the scale, **discuss before adding a literal**. Adding to the token file is cheaper than spreading a magic number.

---

## Composition primitives quick reference

| Need | Primitive | Key attrs |
|---|---|---|
| Vertical rhythm between sections | `stack` | `data-gap` |
| Horizontal toolbar / chip row / action group | `cluster` | `data-gap`, `data-align`, `data-wrap="no"` (only if wrapping breaks the control) |
| Two-pane (sidebar + content) layout | `sidebar` | `data-side`, `data-content-min` |
| Equal siblings, switch row↔column by container width | `switcher` | `data-threshold` |
| Constrained centered content | `center` | `max-inline-size` via CSS var |
| Prose / markdown / generated text | `flow` | `--flow-space` |
| Aspect-ratio media frame | `frame` | `--frame-ratio` |

Nest stacks for sub-rhythm rather than adding one-off scoped gap classes. Prefer logical sizing (`flex-basis`, `min-inline-size`, `max-inline-size`, `aspect-ratio`, `ch`) over fixed px or viewport breakpoints.

---

## Reka portaled content

For overlays (Dialog, Popover, Menu, Tooltip, Select):

- Style portaled parts in the **primitive component itself or DS-level CSS**, never via parent scoped selectors. Stable class hooks: `.ds-*__overlay`, `.ds-*__content`, `.ds-*__item`, `.ds-*__viewport`, `.ds-*__arrow`.
- Position state via Reka attributes: `data-state="open|closed"`, `data-side`, `data-align`, `data-highlighted`, `data-disabled`.
- Use `asChild` to compose your `KmBtn`/`DsButton` as a trigger — avoids nested `<button>`s and keeps a11y wiring.

---

## Adding a new screen — checklist

1. Inventory: which existing pattern fits? (`KmListPage` for CRUD lists, `KmDialog` + `DsField` for forms, etc.)
2. Layout via composition primitives. No fixed px widths/heights or viewport breakpoints unless an intrinsic primitive cannot express it.
3. `Ds*` first → `Km*` if domain semantics are clear → scoped CSS as last resort.
4. Tokens only. No hex, rgb, raw px in colors/spacing.
5. State via `data-*`. No `.is-active`, `.selected`, `.error` modifier classes.
6. Run `yarn lint` and `yarn audit:ds-migration:check` from the `web` workspace.
7. Smoke-test light + dark themes (and any active brand theme).

---

## Adding a new primitive — checklist

1. Confirm it's not already covered by an existing `Ds*`/`Km*` with a new prop or slot.
2. Reka first: if behavior already exists in Reka UI, wrap it; do not write custom JS.
3. CSS uses `--ds-*` tokens, composition where applicable, `data-*` for state.
4. Public contract documented: stable class hooks, slots, CSS variables consumers may style.
5. Vitest spec for keyboard, model updates, a11y, state changes.
6. Update `packages/ds/COMPONENT_STATUS.md`.

---

## Audit & guardrails

From the `web` workspace:

```bash
# DS migration audit (textual debt counters)
yarn audit:ds-migration         # snapshot debt counts
yarn audit:ds-migration:check   # fail on regression vs scripts/ds-migration-baseline.json

# Theme override contract
yarn audit:theme-overrides         # validate brand themes
yarn audit:theme-overrides:report  # full per-theme breakdown

# Stylelint (real CSS bugs + token / logical / BEM / defensive-css discipline)
yarn lint:css           # full report (errors block CI; warnings inform)
yarn lint:css:errors    # errors-only (--quiet)
yarn lint:css:fix       # auto-fix where supported
```

**Audit metrics** include `quasarImports`, `templateVisualProps`, `deepDsSelectors`, `transitionAll`, `legacyLayoutClasses`, `kmZIndexTokens`, `unprefixedRadiusTokens`, `inlineStatusHexes`, `varFallbacks`, `legacyNumericSpacing`, `legacyKmFontSize`. New PRs must not regress any of them. When a slice intentionally lowers a count, update the baseline in the same change.

**Stylelint** catches what audit grep'ы не ловят:
- Unknown property/value (typos like `maxheight`, `text-overflow: hidden`, `caption-side: block-end`).
- Duplicate properties (e.g. `backdrop-filter: …` твайс).
- `transition: all` violations.
- Hardcoded `#hex` / named colors in feature CSS (warning) — gradual migration.
- Defensive CSS — accidental `:hover` without `@media (hover: hover)`, list-style:none on nav, unsafe will-change, missing flex-wrap.
- Logical properties — physical `width`/`height`/`margin-left` flagged in favour of `inline-size`/`block-size`/`margin-inline`.
- BEM naming — `<block>__<elem>--<mod>` enforced in feature scoped CSS.
- Selector specificity / nesting depth ceilings.

Token / utility / theme files are exempted from the strict rules (they need raw hex / px / etc.).

---

## Known live issues — do not propagate

These were real bugs found in the codebase. As of Phase 5 they are baseline-guarded at zero — `audit:ds-migration:check` fails if any reappear.

- ~~`var(--radius-*)` instead of `var(--ds-radius-*)`~~ — fixed in 30 files (P0.1). Metric `unprefixedRadiusTokens=0`.
- ~~`var(--km-font-size-*)` / `--km-font-default` / `--km-font-mono` / `--km-line-height-*` / `--km-font-weight-*`~~ — alias block deleted (P5.3). Metric `legacyKmFontSize=0`. Use `var(--ds-font-*)`, `var(--ds-line-height-*)` directly.
- ~~Hardcoded status hexes~~ — fixed (P0.3). Metric `inlineStatusHexes=0`.
- ~~Numeric spacing utilities~~ (`p-16`, `gap-8`, `m-24`, …) — codemod migrated 1022 occurrences to semantic scale (P5.2). Only the 6px step survives in `utilities/legacy.css` (no semantic equivalent yet); use `p-xs` (4px) or `p-sm` (8px) instead in new code.
- ~~Per-page `Header.vue` breadcrumbs~~ — extracted to `KmBreadcrumbNav` (P3.1).
- ~~70 hex literals in feature CSS~~ — codemod migrated #fff / greys / status / brand-anchor (#6840c2) to DS tokens. ~50 hex remain — categorical viz palettes for agent types / trace span types / deep-research stages. They need a UX-design pass (which palette for which semantic) before promotion to `--ds-color-viz-*` tokens.

---

## When in doubt

- Read `packages/ds/README.md` (long-form contract).
- Read `CUBE_CSS_RESEARCH.md` and `CUBE_CSS_ARCHITECTURE_ROADMAP.md` at repo root for rationale and current phase.
- Read `REKA_CUBE_COMPONENT_VARIANTS_AUDIT.md` for the semantic prop vocabulary (`display`, `tone`, `variant`, `shape`, `size`).
- Pick the smallest layer that solves the problem. Composition over utility, utility over block CSS, block CSS over inline `style`.

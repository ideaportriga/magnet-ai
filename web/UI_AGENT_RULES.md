# UI Agent Rules

This file is the short operational checklist for agents editing Magnet UI. The full design-system contract remains in `packages/ds/AGENTS.md` and `packages/ds/README.md`.

## Core Rule

Use the smallest existing layer that solves the problem:

1. `Ds*` Reka-backed primitive for behavior and accessibility.
2. `Km*` domain wrapper for Magnet UI semantics.
3. App product pattern such as `KmListPage` when the composition repeats across screens.
4. Scoped CSS only for a genuinely one-off block.

## CUBE CSS

- Build layout with `stack`, `cluster`, `sidebar`, `switcher`, `center`, `flow`, and `frame` before adding custom CSS.
- Keep class order as block or pattern, composition, token utilities, narrow technical helpers.
- Use `data-gap` with semantic scale values such as `xs`, `sm`, `md`, `lg`; do not introduce numeric spacing values in new code.
- Use utilities like `min-h-0`, `min-w-0`, `overflow-auto`, `p-md`, `bg-white`, and `border-radius-12` instead of inline layout styles.
- State and variants must be expressed with `data-state`, `data-variant`, `data-tone`, `data-display`, `data-shape`, or component props.

## Components

- Do not introduce raw interactive HTML controls (`button`, `input`, `select`, `textarea`, `table`) when a DS/domain component exists.
- Hidden file inputs are allowed only as upload plumbing behind a DS-visible trigger.
- Use `KmBtn`, `KmIconBtn`, `KmInput`, `KmSelect`, `KmDataTable`, `KmChip`, `KmEmptyState`, `KmDialog`, `KmDrawer`, and `KmCard` before hand-rolling equivalent UI.
- Use `KmListPage` for standard admin CRUD list pages with toolbar, table body, and overlays.
- If the same composition appears on 3 or more screens, extract an app product-pattern component under `apps/@ipr/magnet-admin/src/components/shared/` rather than duplicating markup.

## Tokens And Styles

- New styles must use `--ds-*` tokens, semantic utilities, or component CSS variables.
- Do not add hardcoded hex, `rgb()`, `rgba()`, named colors, raw pixel spacing, local `@keyframes`, or `transition: all` in feature CSS.
- Do not use `var(--ds-..., fallback)` in app code; missing tokens should be fixed at the token layer.
- Do not style DS internals from feature CSS with `:deep(.ds-*)` or `:deep(.km-*)`; add a semantic prop, slot, stable part, or DS-level style instead.
- Avoid inline `style`. If a one-off dynamic value is unavoidable, prefer a constrained CSS variable on the block and document why.

## Icons

- Product/action icons go through `KmGlyph`, `KmBtn icon`, or `KmIconBtn icon`.
- SVG sprite, logo, brand, and illustration assets go through `KmIcon` or `svgIcon` props.
- Do not import `@phosphor-icons/vue` outside `packages/ds/src/components/domain/phosphorIcons.ts`.
- Add aliases in `phosphorIcons.ts` for new canonical names before using them widely.
- Material ligatures and FontAwesome class strings are migration fallbacks only; do not add new usages.

## Review Checklist

- Existing DS/domain component used instead of custom markup.
- Repeated layout promoted or reused as a product pattern.
- No new Quasar tags/classes/imports, `q-*`, `.row`, `.column`, or `.col-*` compatibility classes.
- No new hardcoded visual values in templates or scoped CSS.
- Icons follow `KmGlyph`/`KmIcon` split.
- Light/dark and brand theme behavior is preserved by tokens.
- Run from `web`: `yarn audit:ds-migration:check`, `yarn lint:css:errors`, and the relevant app build/test target.

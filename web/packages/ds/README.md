# `@ds` - Magnet design system

`@ds` is the Magnet design-system package for Vue 3 surfaces. It owns shared
tokens, CUBE CSS composition/utilities, Reka-backed primitives, Magnet domain
components, composables, and global hosts.

The package is built on:

- **Reka UI**: headless, accessibility-first Vue primitives.
- **Every Layout**: intrinsic, browser-driven layout patterns for composition.
- **CUBE CSS**: Composition / Utility / Block / Exception as the styling model.
- **CSS custom properties**: the public contract for tokens and theming.

## Package Layout

```
src/
├── tokens/         CSS variables: colors, spacing, typography, radii, motion
├── composition/    Every Layout-inspired CUBE composition primitives
├── utilities/      Token-driven utilities: spacing, color, typography, radius
├── reset/          Browser reset imported separately as @ds/reset
├── components/
│   ├── primitives/ Reka UI wrappers for overlays, forms, navigation, controls
│   └── domain/     Km*: Magnet-flavoured components and product defaults
├── composables/    useNotify, useDialog, useLoading, useScreen
└── hosts/          DsToastHost, DsDialogHost, DsLoadingHost
```

`@ds/styles` imports tokens, composition, and utilities. Apps import `@ds/reset`
separately before their own app styles.

## CUBE Contract

Styles should land in the smallest layer that matches their responsibility:

- **Tokens** define system values and themeable aliases.
- **Composition** defines layout algorithms and rhythm without visual identity.
- **Utilities** provide one-purpose token helpers.
- **Blocks** define component, domain, or product-pattern identity.
- **Exceptions** express state and variants through `data-*` attributes.

Use class order as a review convention:

```html
<section class="km-panel stack p-lg bg-white shadow-sm" data-gap="md" data-state="open">
  ...
</section>
```

Order classes as block or pattern, then composition, then token utilities, then
narrow technical helpers. Prefer `data-state`, `data-variant`, `data-display`,
`data-tone`, `data-shape`, and `data-size` over ad hoc state classes.

## Every Layout Composition Rules

Composition primitives are based on Every Layout's principle that CSS layout
should be algorithmic, intrinsic, and context-aware. Let the browser calculate
from content and available space before adding feature-level fixes.

- Use `stack` for vertical rhythm between semantically distinct blocks. Nest
  smaller stacks for local rhythm instead of adding one-off scoped gap classes.
- Use `flow` for prose, markdown, generated rich text, and typographic rhythm.
- Use `cluster` for inline groups such as toolbars, chips, action rows, and
  header controls. Add `data-wrap="no"` only when wrapping would break the
  control.
- Use `sidebar` for two-part layouts where one side has an intrinsic or target
  width and the main side takes the remaining space.
- Use `switcher` for equal sibling groups that should switch between one row and
  one column based on available container width.
- Use `center` for constrained centered content via `max-inline-size`.
- Use `frame` for media and preview areas that need a stable aspect ratio.

Spacing belongs to relationships between siblings. Prefer `stack` / `flow` /
`cluster` with tokenized `data-gap`, or a single spacing utility on the boundary
element. Avoid child `margin-bottom`, empty spacer nodes, and local scoped CSS
classes whose only job is `gap`, `margin`, `padding`, `flex`, or `min-h-0`.

Layout dimensions should be suggestions, not dictates: prefer `flex-basis`,
`min-inline-size`, `max-inline-size`, `aspect-ratio`, `gap`, `ch`, and logical
properties over fixed pixel widths/heights and viewport breakpoints. Reach for a
viewport media query only after an intrinsic composition primitive cannot express
the behavior.

## Tokens And Themes

- Public tokens use the `--ds-*` prefix.
- New DS code must use semantic tokens, component tokens, or motion presets.
- Brand theme and light/dark mode are separate concerns: themes override
  `--ds-*` values, while color mode is selected with `<html data-theme>`.
- `--q-*` aliases are not part of the public DS surface.

Motion should use `--ds-duration-*`, `--ds-ease-*`, shared transition presets,
and shared keyframes from `tokens/motion.css`. Repeated loaders, status spins,
attention wobble, dot pulse, fade, scale, slide, and collapse effects should
reference the DS keyframes instead of declaring local `@keyframes`. Do not add
new `transition: all` declarations.

## Reka Integration

Reka provides behavior, accessibility, and state attributes. `@ds` owns the
functional and visual styles around those primitives:

- Portaled content must have stable DS classes and be styled in DS CSS or the
  primitive component itself.
- Overlay/menu/popover state should be styled through Reka `data-state`,
  `data-side`, `data-align`, `data-highlighted`, and `data-disabled` attrs.
- Triggers should use `asChild` with `Ds*` or `Km*` buttons when possible to
  avoid nested interactive elements.
- Feature screens should not style private primitive internals with `:deep()`.

Stable primitive parts should use predictable class names so overlays and
portaled content can be changed centrally:

| Part | Class pattern | Notes |
|---|---|---|
| Trigger | `*.ds-*-trigger` or exported `Ds*Trigger` component | Prefer `asChild` with `DsButton`/`KmBtn` for button-like triggers. |
| Overlay | `.ds-*__overlay` | Owns backdrop, z-index, data-state animation, and pointer behavior. |
| Content | `.ds-*`, `.ds-*__content`, or `.ds-*__panel` | Owns sizing, scroll behavior, collision-safe bounds, and surface styling. |
| Item | `.ds-*__item` or shared `.ds-menu-item` | Reads `data-highlighted`, `data-disabled`, and tone/state attrs. |
| Arrow | `.ds-*__arrow` | Uses the same surface token as the content. |
| Viewport | `.ds-*__viewport` | Owns clipping, available-size vars, and state animation. |
| Label / separator | `.ds-*__label`, `.ds-*__separator` | Keep spacing and color token-driven. |

Feature code can pass props, slots, and outer classes to DS/domain components,
but styling of portaled internals should remain in the primitive or DS layer.

## Anti-Quasar Contract

The `@ds/components` and `@ds/composables` layers must not import Quasar, expose
new `q-*` class names, rely on the global `$q` plugin, or present Quasar-style
visual props as the primary public API.

`Km*` components may translate old feature-code shapes while the migration is in
progress, but their target API should use semantic vocabulary: `variant`,
`display`, `tone`, `shape`, `size`, and state.

Icons follow the same contract: Phosphor Icons are the primary glyph set behind
`KmGlyph`, `KmBtn icon`, `KmIconBtn icon`, and icon props on domain wrappers.
Prefer canonical DS names such as `copy`, `thumbs-up`, `thumbs-down`, `search`,
`check`, `info`, `warning`, `link`, `download`, and `stack`; use the explicit
`ph:*` namespace only when introducing a new Phosphor-backed alias before it is
registered. `KmGlyph tone="brand|subtle|muted|weak|info|context|accent|success|warning|danger|inverse|current"`
controls icon colour intent. Material ligatures and FontAwesome class strings
remain compatibility fallbacks only; new code should not add them. The legacy
`color` prop remains a compatibility path for product-specific colours until
those recipes have semantic homes.

Icon-only buttons should expose selected/emphasis state through `KmIconBtn tone`
rather than raw `color` expressions. Legacy `color` remains a compatibility
fallback for unusual recipes.

Buttons follow the same contract: prefer `KmBtn tone="brand|accent|danger|neutral|subtle|muted|weak|inverse|current"`
for rest-state intent, `interaction-tone="brand|danger"` for hover/focus action
recipes, `selected` for active navigation/filter states, and
`icon-tone="brand|subtle|muted|weak|danger"` for glyph-only emphasis. Legacy
`color`, `icon-color`, `hover-color`, and `hover-bg` remain compatibility props
for unusual or dynamic recipes while migration continues.

Button-like wrappers should mirror the same vocabulary. `KmBtnLoader` and
`KmBtnDropdown` accept `tone`; `KmIconBtn` accepts `tone`; `KmTimelineEntry`, `KmToggle`, and
`KmSeparator` expose small semantic tone sets for their repeated active/state
recipes.

Control wrappers should not carry legacy visual props unless the wrapper
explicitly consumes them. Defaults such as primary loaders/progress indicators,
select/input backgrounds, and toggle segment colours should come from DS tokens
and component styles rather than per-call-site `color` / `bg-color` props.

Chips and badges should use `display`, `tone`, and `shape` for repeated status,
tag, filter, token, score, and neutral-strong recipes. Legacy `color` and
`text-color` remain only for dynamic status maps or product-specific colours
that do not yet have a semantic tone.

Avatars should use `KmAvatar tone="brand|brand-soft|danger-soft|neutral"` for
repeated Magnet identity markers. Legacy `color` and `text-color` remain
compatibility fallbacks for dynamic product imagery and source-specific icon
recipes.

Domain wrappers that couple icon colour to another affordance, such as focus
highlighting, should expose a semantic `tone` prop for that combined intent.
Legacy raw colour props can remain as compatibility fallbacks while migration
continues.

Legacy layout helpers such as `.row`, `.column`, and `.col-*` remain only as
compatibility utilities for older screens. New layouts should use `stack`,
`cluster`, `sidebar`, `switcher`, `center`, `flow`, or product patterns.
When an existing screen genuinely needs fixed 12-column proportions, use the
DS `basis-*` utilities (`basis-6`, `basis-12`, `basis-md-6`, and so on) as the
sanctioned replacement for numeric `.col-*` compatibility helpers.

## Migration Audit

Run the design-system migration audit from the `web` workspace before and after
each refactor slice:

```bash
yarn audit:ds-migration
yarn audit:ds-migration:check
```

The first command prints current Quasar/compatibility debt. The second command
compares the current counts with `scripts/ds-migration-baseline.json` and fails
if legacy debt increases. Lower counts are expected as the refactor progresses;
when a slice intentionally removes debt, update the baseline in the same change.

`templateVisualProps` tracks feature/template usage of raw visual props. Feature
code should introduce or use semantic `tone`, `variant`, `display`, `shape`,
`selected`, or state APIs instead.

The temporary DS-wrapper exception list is centralized in
`scripts/template-visual-prop-allowlist.mjs` and reported separately as
`sanctionedTemplateVisualFallbacks`. It is currently empty and baseline-guarded;
compatibility fallbacks should not return without an intentional migration
decision.

`deepDsSelectors` tracks scoped `:deep()` selectors that reach into DS/domain or
headless internals. These are Phase 5 debt: prefer stable primitive parts,
semantic props, product wrappers, or DS-level CSS over parent scoped overrides.
This debt is removed and baseline-guarded at zero.

`kmZIndexTokens` tracks the legacy app z-index scale. New code should use the
public `--ds-z-*` token scale; `--km-z-*` usage is removed and baseline-guarded
at zero.

## Status

See `docs/CUBE_CSS_RESEARCH.md` and `docs/CUBE_CSS_ARCHITECTURE_ROADMAP.md` for
the active CUBE/DS architecture work. `docs/REKA_CUBE_UI_REFACTOR_PLAN.md`
remains the broader Reka/Cube migration history, and
`docs/QUASAR_TO_REKA_MIGRATION_PLAN.md` remains the historical Quasar removal log.

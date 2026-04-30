# Theme Override Contract

Brand themes in `packages/themes/src/themes/{default,salesforce,siebel,...}` may override a narrow surface of `--ds-*` tokens. Anything outside this surface is **read-only** — it forms part of the cross-theme design language and may not diverge per brand.

The contract is enforced by `scripts/check-theme-overrides.mjs`. Pre-commit hooks and CI fail if a theme overrides a forbidden token.

## Allowed overrides

A theme MAY override:

- **Brand signature.** `--ds-brand-accent`, `--ds-brand-accent-soft`, `--ds-brand-focus-ring`, `--ds-brand-selection-bg`, `--ds-brand-motion-emphasis`.
- **Color palette.** Anything matching `--ds-color-*`. Includes the full `--ds-color-{primary,gray,success,warning,danger,info}-{50..950}` ramp, semantic foreground/surface/border roles, status triplets, brand intent, accent, control/button/table/menu/chat tokens, status labels, score chips, and legacy color aliases.
- **Static overrides.** `--ds-color-static-white`, `--ds-color-static-black` may be redefined for brand-specific absolute colors.
- **Font family.** `--ds-font-default`, `--ds-font-mono`. (For loading custom typefaces.)
- **Component-shape mascots.** SVG path data and image paths used for brand-specific assets (these are in `<theme>/svg/` rather than as CSS vars).

## Forbidden overrides — read-only across themes

A theme MUST NOT override:

| Group | Token pattern | Reason |
|---|---|---|
| **Spacing scale** | `--ds-space-*` | Fixed scale (2xs..6xl + numeric) ensures rhythm consistency across brands. Diverging breaks composition primitives. |
| **Radius scale** | `--ds-radius-*` | Card corner language is part of cross-theme system shape. |
| **Elevation** | `--ds-shadow-*` | Uniform depth model prevents jarring per-theme depth perception. |
| **Z-index scale** | `--ds-z-*` | Stacking order is system contract. |
| **Motion timing** | `--ds-duration-*`, `--ds-ease-*` | Animation rhythm is fixed (mid-line emphasis only via `--ds-brand-motion-emphasis`). |
| **Transition presets** | `--ds-transition-*` | Composed from durations + ease above. |
| **Typography scale** | `--ds-font-size-*`, `--ds-line-height-*`, `--ds-font-weight-*`, `--ds-tracking-*`, `--ds-text-*` | Font family is themeable (`--ds-font-default`); the size / weight / line-height ramp is not. |
| **Field component dimensions** | `--ds-field-height`, `--ds-field-radius`, `--ds-btn-height-*`, `--ds-dialog-width-*`, `--ds-table-row-height` | Component sizing follows the spacing scale. |
| **Loading affordances** | `--ds-loader-*` | Loaders use motion + spacing tokens — themed loaders should re-derive, not redefine. |

## Legacy non-namespaced overrides

Some themes still use non-`--ds-` prefixed custom properties (e.g. `--button-sm`, `--field-height`, `--font-default`). These are **grandfathered** for now. The validator warns but does not fail. New themes MUST use the `--ds-*` namespace.

Tracked per theme; aim is zero by Phase 5 (legacy depreciation).

## Adding a new override

1. Read this contract.
2. If the token you want to override is not on the allow-list, open a discussion — a new role token may need to be added to `packages/ds/src/tokens/` first.
3. Update the theme file with the new override.
4. Run `node packages/themes/scripts/check-theme-overrides.mjs`. The validator will confirm the override is in-contract.

## Adding a new token to the contract

1. Define it in `packages/ds/src/tokens/<group>.css` with a sensible default + dark variant.
2. If it should be themeable, ensure its name matches an allowed pattern (or extend the allow-list in `check-theme-overrides.mjs` with rationale).
3. Document its purpose in the relevant section above.

## Glossary

- **Brand theme** — a `data-theme="<name>"` block (e.g., `salesforce`, `siebel`) that re-skins the system. Always layered on top of `:root,[data-theme='light']` defaults.
- **Color mode** — `data-color-mode="dark|light"` (or `[data-theme='dark']`) override block, applies to the brand theme. Color modes are owned by `packages/ds/src/tokens/colors.css`, not by brand themes.

## Status

| Theme | Allowed overrides | Forbidden overrides | Legacy non-namespaced |
|---|---:|---:|---:|
| default | tracked | 0 | tracked |
| salesforce | tracked | 0 | tracked |
| siebel | tracked | 0 | tracked |

Run `node packages/themes/scripts/check-theme-overrides.mjs --report` for current numbers.

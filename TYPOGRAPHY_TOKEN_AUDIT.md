# Typography & Text-Color Token Audit

> Date: 2026-04-27
> Scope: `web/packages/ds/src/tokens/typography.css`, `tokens/colors.css`, `web/packages/themes/src/base/typography.styl`, `web/packages/ds/src/reset/index.css`, plus consumers in `web/packages/ds/src/components/**`, `web/apps/@ipr/magnet-admin/src/**`, `web/apps/@ipr/magnet-panel/src/**`.
> Goal the user asked for: assess consistency of design tokens, starting with **fonts**. Include the "absolute black appeared" observation.

---

## TL;DR

Three concrete defects, in order of impact:

1. **Body text is rendered as `--ds-color-black: #191b23`** by the `@ds` reset (`body { color: var(--ds-color-black, #191b23); }`). Pre-migration, body inherited Quasar's default (`rgba(0,0,0,0.87)` ≈ `#212121`). The new value is ~8 RGB steps darker, blue-tinted, and reads as "absolute black" — exactly what the user noticed. ⚠️ Fix below.
2. **Token name `--ds-color-black` is semantically misleading.** It's the primary text color, not a black swatch. Inviting future regressions where someone "uses black" thinking it'll be `#000`. Recommend an alias.
3. **Two parallel typography aliases (`--ds-font-*` + `--km-font-*`)** are kept in sync by hand. Body-text classes in `themes/typography.styl` reference `--km-*`; new `Ds*` primitives reference `--ds-*`. Living drift surface, no functional bug today but a maintenance burden.

Plus a few smaller annoyances (heading-alias inversion, inconsistent scale steps).

---

## 1. Typography Token Inventory

### 1.1 Sources of truth

| File | What it owns |
|---|---|
| `web/packages/ds/src/tokens/typography.css` | `--ds-font-*` token values + `--km-font-*` legacy aliases (one-to-one var()). |
| `web/packages/themes/src/base/typography.styl` | Class definitions (`.km-h1`, `.km-body`, …) consuming the `--km-*` aliases. |
| `web/packages/ds/src/reset/index.css` | Body default font-family, font-size, color, line-height. |
| `web/packages/ds/src/components/**` (CSS) | Per-component typography from `--ds-*` tokens. |

### 1.2 Scale (sizes)

```
xs       10px
sm       11px
caption  12px
label    13px
body     14px
body-lg  16px
h2       18px
h1       20px
display  24px
```

Steps: `+1, +1, +1, +1, +2, +2, +2, +4`. Two observations:

- The `xs / sm / caption / label` band (10/11/12/13) has 1px steps. That's **too granular** — most apps can't render a meaningful difference between 10 and 11px on standard DPI. In practice, components only use `caption` (12px) and `label` (13px); `xs` and `sm` show up rarely (badge, description-2, tiny). **Consider dropping `sm` (11px)** — collapse to a 7-step scale.
- The `display ↔ h1` jump is 4px (20 → 24). All other steps are 1–2px. Slight inconsistency but practical for the headline tier.

### 1.3 Weights

```
regular    400
medium     500
semibold   600
bold       700
```

Clean, linear, no drift. ✓

### 1.4 Line-heights

```
none      1
tight     1.2
snug      1.3
normal    1.4
relaxed   1.5
```

Clean. ✓

### 1.5 Heading-alias inversion (legacy Quasar parity)

`themes/typography.styl` aliases the legacy `.km-heading-{1..7}` classes onto the new `.km-h{1..5}` scale:

| Legacy class | Aliased to | Resolved size |
|---|---|---|
| `km-heading-1` | `km-h5` | 13px |
| `km-heading-2` | `km-h4` | 14px |
| `km-heading-3` | `km-h4` | 14px (duplicate of 2!) |
| `km-heading-4` | `km-h3` | 16px |
| `km-heading-5` | `km-h3` | 16px (duplicate of 4!) |
| `km-heading-6` | `km-h1` | **20px** |
| `km-heading-7` | `km-h2` | **18px** |

Two issues:
- **Duplicates** (`heading-2 == heading-3`, `heading-4 == heading-5`).
- **Out-of-order** (`heading-6` is *bigger* than `heading-7`).

This is pre-migration debt — the legacy theme defined `.km-heading-7` as the dialog-title size (18px). Keeping the alias preserves visual parity. Recommend leaving alone for now and **deprecating `.km-heading-{1..7}` in favor of `.km-h{1..5}`** at the same time as the broader CSS-class sweep (Phase 4 of the refactor plan).

---

## 2. The "Absolute Black Appeared" Bug

### 2.1 What the user observes

Body text and any element with `class="text-black"` (used in **83 admin/panel templates**) renders darker than before, looking close to pure `#000`.

### 2.2 Root cause

`web/packages/ds/src/reset/index.css:53`:

```css
body {
  color: var(--ds-color-black, #191b23);
  ...
}
```

`web/packages/ds/src/tokens/colors.css:36`:

```css
--ds-color-black: #191b23;   /* RGB(25, 27, 35) */
```

`#191b23` is a near-black with a slight blue tint (HSL: 232°, 17%, 12%).

The legacy stack had:
- `web/packages/themes/src/base/_colors.styl:32`: `black: #191B23` — **same value**, but
- `web/packages/themes/src/base/app.styl`: **no `body { color: … }` rule** — body inherited Quasar's reset default of `rgba(0,0,0,0.87)` ≈ `#212121` (Material/Quasar primary-text).

So the *value* didn't change. The *application* did:
- Pre-migration: `body { color: rgba(0,0,0,0.87) }` (Quasar reset, ~#212121, soft).
- Post-migration: `body { color: #191b23 }` (DS reset, hard, blue-tinted).

`#191b23` vs `#212121`: identical hue family but the new one is darker (12% lightness vs 13%) and slightly blue-tinted. Side-by-side, the new one reads as "more black."

### 2.3 Impact surface

- `body { color }` reset rule → all unstyled text in the entire app.
- 83 templates with `class="text-black"` → resolved to `--ds-color-black`.
- 116 references to `--ds-color-black` / `--km-color-black` inside `@ds` and `@themes` packages (primitive components, domain components, utilities).

So changing `--ds-color-black` value propagates to ~199 spots in one shot, no consumer-side migration required.

### 2.4 Recommended fix

Soften `--ds-color-black` to `#212121` (Material primary-text, legacy Quasar parity, RGB(33, 33, 33) — slightly lighter, no blue tint). This matches what the codebase looked like before the migration without renaming any tokens.

```diff
- --ds-color-black: #191b23;
+ --ds-color-black: #212121;
```

Apply the same change in the dark-theme override block (currently `--ds-color-black: #f4f2f8`, that's fine for dark mode — leave alone).

Alternative: use `rgba(0, 0, 0, 0.87)` for exact Quasar parity, but flat hex is easier to debug.

### 2.5 Naming concern (separate from value fix)

The token is *named* `black` but its semantic role is "primary text color." Two improvements possible — recommend the second:

1. **Rename** to `--ds-color-text-primary`, deprecate `black` alias. **High-effort** — 199 consumer touchpoints.
2. **Add a semantic alias** `--ds-color-text-primary: var(--ds-color-black)` (and corresponding `text-primary` utility class) so new code can use the right name without breaking old call-sites. **Low-effort**, fixes the readability issue going forward without churn.

---

## 3. `--ds-font-*` ↔ `--km-font-*` Drift

### 3.1 Status

`tokens/typography.css` defines both families, perfectly mirrored:

```
--ds-font-default    --km-font-default
--ds-font-mono       --km-font-mono
--ds-font-size-xs    --km-font-size-xs
... etc (×9 sizes, ×4 weights, ×5 line-heights = 18 pairs total)
```

### 3.2 Consumers

- `themes/typography.styl` (legacy class definitions): exclusively `--km-*`.
- `@ds/components/**` (new primitives): exclusively `--ds-*`.
- `@ds/utilities/typography.css` and `@ds/composition/*.css`: mixed.

### 3.3 Risk

The two families are *currently* in sync. If anyone edits one without editing the other (likely during a future restyle), `themes/` and `@ds/` will silently drift — the same `<h1>` would render at different sizes depending on which class is applied.

### 3.4 Recommended fix

Two options, pick one:

1. **Lockstep via alias** — rewrite `tokens/typography.css` so `--km-*` are defined *only* as `var(--ds-*)` (already the case today, ✓ — keep it that way and add a CI guard that rejects standalone `--km-font-*` value definitions).
2. **Migrate `themes/typography.styl` to `--ds-*`** and drop the `--km-*` aliases. This is part of the broader Quasar-cleanup roadmap (Phase 7); not urgent.

The current state is acceptable as long as the alias-only contract holds.

---

## 4. Misc Smaller Findings

| # | Finding | Severity | Action |
|---|---|---|---|
| a | `.km-heading-{1..7}` alias chain is duplicated (2≡3, 4≡5) and out-of-order (6>7). | Low | Deprecate, point new code at `.km-h{1..5}`. |
| b | The 11px (`sm`) tier is rarely used and reads identically to 10px and 12px on most displays. | Low | Drop on the next scale revision. |
| c | `--ds-line-height-none: 1` is set on `.km-label`, `.km-input-label`, `.km-btn`, `.km-chip` etc. — no breathing room. Fine for inline pills, but `.km-input-label` sometimes wraps to 2 lines and gets clipped. | Low | Switch `.km-input-label` to `--ds-line-height-tight`. |
| d | `body { font-family: var(--ds-font-default) }` falls back to `system-ui, sans-serif` — but the actual `--ds-font-default` value is `'Geist', 'Inter', sans-serif`. If the Geist font asset fails to load, the cascade silently picks Inter (system Inter is rarely installed on Windows/Linux). | Low | Bundle Inter as a self-hosted webfont and verify load order, or accept system fallback. |
| e | `text-rendering: optimizeLegibility` on body causes measurable layout cost on long-text pages (markdown, prompt previews). | Very low | Consider switching to `auto`. |

---

## 5. Recommended Action Plan — DONE 2026-04-27

1. ✅ **Softened `--ds-color-black` → `#212121`** (`web/packages/ds/src/tokens/colors.css:36`). Restores legacy text lightness across all 199 consumer touchpoints in one shot.
2. ✅ **Added `--ds-color-text-primary` semantic alias** at the same spot (`var(--ds-color-black)`). New code can use the right name without a rename. Did NOT add a `.text-primary` utility class because that name is already taken by the brand-purple text utility — keep `.text-black` as the legacy class until a wider rename is undertaken.
3. ✅ **Single source of truth for tokens** — deleted the orphaned Stylus token files (`web/packages/themes/src/base/tokens/_colors.styl`, `_components.styl`, `_elevation.styl`, `_radii.styl`, `_spacing.styl`, `_typography.styl`). They were referenced only in stale doc comments, never imported. The single canonical source is now `web/packages/ds/src/tokens/*.css` (which already exposes `--ds-*` canonical names and `--km-*` / unprefixed legacy aliases). Updated the comments in `themes/src/base/typography.styl` and `themes/src/base/fields.styl` to point at the new canonical location.
4. ✅ **`.km-input-label` line-height** → `tight` (`themes/src/base/typography.styl`). Long field labels in dialogs were getting clipped between rows because the previous `line-height: var(--km-line-height-none)` (1.0) gave wrapped labels zero leading.
5. ✅ **Deprecation note** added on the `.km-heading-{1..7}` alias block (`themes/src/base/typography.styl`) explaining the non-monotonic numbering and pointing new code at `.km-h{1..5}`.
6. **Audit-only deliverables** — none of the remaining typography-scale findings (§1.5, §3, §4 b/d/e) need urgent action. Tracked here for the next theme refresh.

---

## 6. Out Of Scope

- Color tokens beyond `--ds-color-black` — would inflate this audit. Separate doc once fonts are signed off.
- Spacing / radii / elevation / motion / z-index audits — same deferral.
- Quasar `--q-*` aliases — covered by `REKA_CUBE_UI_REFACTOR_PLAN.md` Phase 2.2 / 7.6 (already complete; baseline at 0).

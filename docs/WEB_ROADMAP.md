# UI/UX & Code Quality Roadmap

Quick wins with minimal risk for a stable, tested codebase.

---

## Tier 1 — Zero-risk cleanup

### 1. Remove console.log statements
- **Effort:** 1h
- **Risk:** None
- **What:** 280+ `console.log/error/warn` across admin components. `router.js` logs every route transition: `console.log('after each', to)`.
- **Why:** Cleaner dev console, no data leaking in prod logs.

### 2. Unify route lazy-loading in `router.js`
- **Effort:** 30min
- **Risk:** None
- **What:** Some routes use static imports (`component: ApplicationPage`), others use dynamic (`() => import(...)`). Standardize to dynamic imports everywhere.
- **Why:** Better code-splitting, smaller initial bundle, no logic changes.

### 3. Clean up dead TODO comments
- **Effort:** 30min
- **Risk:** None
- **What:**
  - `DrawerPreview.vue`: `// TODO: remove this` — dead code
  - `Prompts/advancedsettings.vue` (2x): `// TODO: remove this when backend is updated`
  - `Agents/Channels.vue` (2x): `// TODO: map to actual secrets when we have them`
- **Why:** Reduces noise, clarifies intent.

---

## Tier 2 — UX polish

### 4. Replace inline styles with scoped CSS
- **Effort:** 2h
- **Risk:** Minimal
- **What:** 5+ components have `style="min-height: 30px; white-space: pre-wrap"` directly in templates.
- **Why:** Better theming support, consistent with the rest of the codebase.

### 5. Add missing error states to list components
- **Effort:** 3h
- **Risk:** Minimal
- **What:** Many components show a spinner on load but render a blank screen if the API fails. The pattern already exists in `ChatWithAssistant.vue` — replicate it to the top 10 most-used list views.
- **Why:** Users see nothing when something breaks instead of an actionable message.


## Tier 3 — Type safety

### 7. Replace `Record<string, any>` with specific types
- **Effort:** 3h
- **Risk:** Low (TypeScript catches regressions at compile time)
- **What:** ContentProfiles, observability traces — e.g. `(row: any) => row?.cost_details?.total`. KnowledgeGraph has 10+ instances of `Record<string, unknown>` where entity types are known from the API.
- **Why:** Fewer runtime surprises, better IDE autocomplete.

---

## Tier 4 — Accessibility

### 8. Add basic aria-labels in magnet-panel
- **Effort:** 1h
- **Risk:** Minimal
- **What:** magnet-panel currently has **zero** accessibility attributes. Start with `aria-label` on buttons in auth forms (Login, Signup, Forgot Password). Quasar handles most of this automatically — just needs to be enabled.
- **Why:** Basic compliance, keyboard navigation support.

---

## Summary

| # | Task | Effort | Risk |
|---|------|--------|------|
| 1 | Remove console.log | 1h | None |
| 2 | Lazy-load all routes | 30min | None |
| 3 | Clean dead TODOs | 30min | None |
| 4 | Inline styles → scoped CSS | 2h | Minimal |
| 5 | Error states in list components | 3h | Minimal |
| 6 | Unify loading spinners | 2h | Minimal |
| 7 | Type `any` → specific types | 3h | Low |
| 8 | aria-labels in panel/auth | 1h | Minimal |

**Total estimated effort: ~13h**

---

## What NOT to touch now (high risk)

- Vuex → Pinia migration in magnet-admin — large operation, breaks store contracts
- Splitting 1000+ line components — changes props/emit contracts
- Renaming store modules — potentially breaks routes and navigation

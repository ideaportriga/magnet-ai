# E2E Run — Log Audit & Remediation Plan

**Run window (UTC):** `2026-04-27T08:05:14Z` → `2026-04-27T08:23:12Z` (~18 min)
**Branch:** `alpha-taskiq-reka-cube-css`
**Trigger:** `npx nx run magnet-admin:e2e --skip-nx-cache`

## Run summary

| Metric | Count |
|---|---|
| Specs total | 21 |
| Specs failed | **18** (86%) |
| Tests total | 113 |
| Tests passed | 92 |
| Tests failed | **21** |
| Tests pending (skipped) | 21 |
| Frontend errors logged | 8 |
| Frontend warnings logged | 35 |
| Backend warnings logged | 26 (asyncio 5 · csrf 20 · auth 1) |

Most failed specs lose exactly **1 of 4 tests** — failures are concentrated, not cascading.

---

## A. Frontend runtime errors (8)

These are real `window.onerror` events shipped to Loki via the `frontend` logger.

### A1. `this.$refs[field]?.validate is not a function` — **4 occurrences** · **HIGH**

Old Quasar form-validation API still being called somewhere after the Reka/CUBE migration. Quasar inputs exposed a per-field `validate()` method on `$refs`; replacements (`KmInput` / DS primitives) do not.

Sample:
```
this.$refs[field]?.validate is not a function
instance.refs[field]?.validate is not a function
```

**Fix plan**
1. `grep -rn "\$refs\[.*\]\.validate\|\$refs\..*\.validate" web/apps/@ipr/magnet-admin/src` to find every call site.
2. Replace each with the new validation idiom — a `KmField`/`KmInput` v-model + `valid` flag, or a `vee-validate`-style hook depending on the form. Several create-dialogs already use the new pattern; cargo-cult them.
3. Add a vitest unit test that mounts the affected form and clicks "Save" with an empty value, asserting the validation message is shown — this is a contract that should not regress again.

### A2. `<SelectItem /> must have a value prop that is not an empty string` — **1 occurrence** · **MEDIUM**

`reka-ui`'s `SelectItem` reserves `value=""` to mean "clear selection / show placeholder", so consumer items cannot pass it. Mirrored as a Vue warning (B4).

**Fix plan**
1. Find the `<SelectItem value="">` (likely a placeholder option in a `KmSelect`/`DsSelect` consumer). `grep -rn 'SelectItem' --include="*.vue"`.
2. Either drop the empty-value option entirely (let placeholder show) or use a sentinel like `__none__` and convert in v-model.

### A3. `ResizeObserver loop completed with undelivered notifications` — **3 occurrences** on `/model-providers` · **LOW (noise)**

Browser-emitted, non-fatal. Often triggered by Reka popovers or autosizing inputs that resize their container in the same frame.

**Fix plan**
1. Add a global filter at the `window.onerror` boundary that drops this exact message before forwarding to Loki — it's well-known noise. Search for the existing onerror handler in `web/apps/@ipr/magnet-admin/src` (likely in `main.js` or an error plugin).
2. Optional: investigate `/model-providers` for the actual offending observer (table column auto-fit?), but only if it correlates with a user-visible jank.

---

## B. Vue compiler/runtime warnings (35)

### B1. `Failed to resolve component: q-checkbox` (9x), `q-icon` (1x) — **HIGH**

Leftover Quasar tags in components rendered by the data table (`<Header>`, `<Cell>`). Quasar is gone after the CUBE migration, so these tags resolve to nothing and the cells render blank.

**Fix plan**
1. `grep -rn "<q-checkbox\|<q-icon\|q-checkbox\|q-icon" web/apps/@ipr/magnet-admin/src --include="*.vue"`.
2. Replace `q-checkbox` with `<KmCheckbox>` / `<DsCheckbox>` and `q-icon` with `<KmGlyph>` / `<KmIcon>`.
3. Most likely files: `components/**/Header.vue` and `components/**/Cell.vue` referenced in `KmDataTable` columns.

### B2. `Invalid prop: type check failed for prop "rows". Expected Number with value N, got String with value "N"` — **9x across many components** · **MEDIUM**

`KmInput` declares `rows: Number` but consumers pass it as a string literal (`rows="10"` instead of `:rows="10"`). Affected sites observed in the warnings: `KmInput` inside `Drawer` (Prompt preview), `KmSection` (Variant parameters), `Information` (API definition), `InputDetails`, `Sampleinput`, `Notes`, `Settings (Welcome message)`, `AlertDialogDescription`.

**Fix plan**
1. Either:
   - **(preferred)** loosen the `KmInput` prop type to `[Number, String]` and coerce internally, OR
   - fix all call sites to use `:rows="10"`.
2. The first option is one PR, the second is a sweep across ~9 templates. Recommend (a) for quick win, then (b) as a follow-up sweep so the types stay tight.

### B3. `Missing 'Description' or aria-describedby="undefined" for DialogContent` — **8x** · **MEDIUM (a11y)**

Reka `DialogContent` requires either a `<DialogDescription>` child or an explicit `aria-describedby="..."` for screen readers.

**Fix plan**
1. Audit all wrappers around Reka `DialogContent`/`AlertDialogContent` (probably in `packages/ds/src/components/primitives/Dialog/*.vue`).
2. Add a default `<DialogDescription>` slot or pass `aria-describedby="undefined"` only when a description is genuinely absent (not a string `"undefined"` — typo guard).

### B4. `Component is missing template or render function: SelectItem` — **1x** · same root cause as A2 · **MEDIUM**

Reka logs the warning when an empty-value `SelectItem` is created. Fixing A2 removes this.

### B5. `Wrong type passed as event handler to onRecord:update — did you forget @ or :` — **1x in EvaluationJobs > Records** · **LOW**

Indicates a `<Records :record:update="..."> `or `<Records record:update="..."> `where the binding is an object literal instead of a function/v-model.

**Fix plan**
1. Open `web/apps/@ipr/magnet-admin/src/components/EvaluationJobs/Records*.vue` (or the parent that renders it).
2. Convert the binding to `@record:update="handler"` or, if it's meant to be a v-model, `v-model:record="..."`.

---

## C. Backend warnings (26)

### C1. `CSRF: Blocked POST request to /test/cleanup — missing Origin/Referer` — **20x** · **HIGH (test infra)**

Cypress task `resetBackendErrors` (and the test cleanup helper) sends `POST /test/cleanup` from Node. The CSRF middleware rejects it because there is no Origin/Referer. Each test run leaks 20 of these warnings, and any cleanup the endpoint was supposed to perform never happens.

**Fix plan**
1. Bypass CSRF for the test-only namespace. In `api/.../middlewares/csrf.py`, add `/test/` to the list of paths exempt from Origin/Referer checks **but only when `DEBUG_MODE` is set**.
2. Alternative: have the Cypress task add `Origin: http://localhost:8000` / `Referer: ...` headers to every `httpPost`/`httpGet` it makes (`cypress.config.ts:51` and `:60`).
3. Pick (1) — it's a one-line gate plus a unit test.

### C2. `asyncio: Executing <Task ...> took 0.X seconds` — **5x** (range 0.15–0.27s) · **MEDIUM**

Python's asyncio debug logger flags tasks that block the event loop. The offending tasks are all `RequestResponseCycle.run_asgi` from uvicorn — i.e., real HTTP request handlers doing slow synchronous work.

**Fix plan**
1. Capture the URL/route of slow requests by enriching the asyncio warning with request context (a small middleware wrapper that attaches `request.url.path` to the log record), then re-run.
2. Most likely culprits given the test surface: rag_tools list/preview, knowledge_graph search. Profile with the `mcp__grafana__fetch_pyroscope_profile` tool once the offending route is identified.
3. If they turn out to be benign (e.g., long DB queries with proper async drivers but slow plans), bump the asyncio slow-task threshold in dev so warnings stop polluting Loki.

### C3. `middlewares.auth: No valid auth data provided` — **1x** · **LOW**

Single anonymous request hit an auth-required path. With Cypress as the only client during the run, this is almost certainly a benign first-page request before login. Keep an eye on it; only act if frequency rises.

---

## D. E2E test failures (21 tests across 18 specs)

The failures cluster into 4 patterns. None of them point at a real product regression — they're test-selector drift after the Reka/CUBE migration.

### D1. C3 "create form shows validation on empty submit" — **13 entities affected** · **HIGH**

Selector: `[data-test="popup-confirm"], [data-test="save-btn"]`. Either the dialog closes silently (no validation popup) or the new dialog uses a different test hook. Affected: agents, ai_apps, api_keys, api_servers, collections, evaluation_jobs, evaluation_sets, knowledge_graph, knowledge_providers, mcp, model_config, model_providers, prompt_templates, rag_tools, retrieval.

**Fix plan**
1. Open one entity's create dialog manually (e.g., `/rag-tools`, click New, click Save with empty form). Confirm whether validation appears at all.
   - If validation is missing → product bug, fix the form's `validate()` chain (related to A1).
   - If validation is shown but with a different `data-test` → update `cypress/support/pages/createDialog.ts` selector to include the new hook (`[data-test="ds-alert-dialog"]`, `[data-test^="popup-confirm-"]`, etc.).
2. The test code already lists multiple hooks (line 102 of `crudContract.ts`); extend that list rather than touching 13 templates.

### D2. `prompt_template_preview.cy.ts` — `[data-test="preview-input"]` not found (3 tests) · **MEDIUM**

The preview input was either renamed or moved. `Search/Prompt.vue` used to carry `data-test="preview-input"`; verify it still does.

**Fix plan**
1. `grep -rn "data-test=\"preview-input\"" web` and confirm the element exists where the test expects it.
2. If it's now `data-test="search-input"` (which Cypress tests for in other places), align — either the template or the test.

### D3. `[data-test="options"]` not found — **3 specs** · **MEDIUM**

Likely a row-action dropdown (the `…` menu) whose hook changed during the data-table refactor.

**Fix plan**
1. Find `data-test="options"` in `KmDataTable.vue` or row action component. Check if it was renamed (e.g., `data-test="row-actions"` or `kebab-button`).
2. Update either the markup or the cypress page-object to match.

### D4. `tables` row-click navigation timeouts (2 tests) · **MEDIUM**

`expected '...#/agents' to match /agents\/[a-f0-9-]+/` — clicking a row didn't navigate to the detail. Could be the agent list's row-click handler regressed, or the URL shape changed.

**Fix plan**
1. Manually click an agent row; if nav works, the test selector is wrong.
2. If nav doesn't work, the row's `@click` listener was lost during the migration — restore it.

---

## Prioritized action list

| # | Item | Impact | Effort |
|---|---|---|---|
| 1 | **A1**: replace legacy `$refs[field].validate()` calls — almost certainly the root cause of D1 | Unblocks 13 failing C3 tests + clears 4 runtime errors | M |
| 2 | **C1**: exempt `/test/*` from CSRF middleware in DEBUG_MODE | Restores test-cleanup, removes 20 noise warnings/run | XS |
| 3 | **B1**: replace remaining `q-checkbox` / `q-icon` tags in table headers/cells | Cells stop rendering blank; clears 10 warnings | S |
| 4 | **B2**: loosen `KmInput.rows` to `[Number, String]` (or sweep call sites) | Clears 9 warnings | XS / M |
| 5 | **D2 / D3 / D4**: align cypress page-objects with current `data-test` hooks | Restores ~5 more tests | S |
| 6 | **A2 / B4**: drop empty-value `SelectItem` | Clears 1 error + 1 warning | XS |
| 7 | **B3**: add `DialogDescription` defaults in DS dialog primitives | A11y win, clears 8 warnings | S |
| 8 | **C2**: add request-context to asyncio slow-task logs, then profile | Performance investigation | M |
| 9 | **B5**: fix `onRecord:update` binding in EvaluationJobs | Clears 1 warning | XS |
| 10 | **A3**: filter `ResizeObserver loop` from frontend-error pipe | Clears 3 noise errors | XS |

## Quick wins (single-PR bundle, ~30 min)

- C1 (csrf gate)
- B2 (loosen `rows` prop)
- A2 / B4 (SelectItem empty value)
- A3 (RO noise filter)
- B5 (onRecord:update)

These are all isolated, low-risk, and remove a meaningful chunk of the noise so the remaining real signals (A1, B1, B3, D1) are easier to chase.

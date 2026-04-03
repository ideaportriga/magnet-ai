# i18n Migration Plan — Magnet AI Admin

## Key Naming Convention

### Structure

Keys follow the pattern: `{scope}_{camelCaseName}`

```
scope_descriptiveName
```

### Scopes

| Scope | Description | Example |
|---|---|---|
| **common** | Shared actions, labels, states used across many pages | `common_save`, `common_search`, `common_name` |
| **nav** | Sidebar navigation sections and menu items | `nav_configure`, `nav_agents`, `nav_ragTools` |
| **auth** | Authentication, login, registration, password | `auth_login`, `auth_forgotPassword` |
| **validation** | Form validation error messages | `validation_required`, `validation_minLength` |
| **entity** | Entity type names (singular/plural) | `entity_agent`, `entity_agents` |
| **dialog** | Dialog/modal titles | `dialog_newAgent`, `dialog_deleteAgent` |
| **confirm** | Confirmation button labels | `confirm_okDelete`, `confirm_yesCancelJob` |
| **section** | Section headers (km-section title) | `section_generalInfo`, `section_secrets` |
| **subtitle** | Section descriptions (km-section subTitle) | `subtitle_yourAccount`, `subtitle_temperature` |
| **hint** | Help text, instructions, notifications | `hint_editAfterSaving`, `hint_credentialsEncrypted` |
| **placeholder** | Input placeholders | `placeholder_enterUserMessage`, `placeholder_selectType` |
| **error** | Error messages | `error_unexpectedError`, `error_callingSearch` |
| **access** | Access control messages | `access_restricted`, `access_noPermissions` |
| **emptyState** | Empty state messages | `emptyState_noAiTabs` |
| **user** | User profile/security page | `user_profile`, `user_enable2fa` |
| **feedback** | User feedback UI | `feedback_thankYou`, `feedback_sendFeedback` |
| **filter** | Filter presets | `filter_last15min`, `filter_last24hours` |
| **panel** | Panel app specific | `panel_clearChat`, `panel_stop` |
| **knowledgeGraph** | Knowledge Graph specific | `knowledgeGraph_sources` |
| **metadata** | Metadata studio specific | `metadata_discovered` |
| **confirmation** | Action confirmation UI | `confirmation_confirmAction` |
| **metadataFilter** | Metadata filter editor | `metadataFilter_valueCondition` |

### Page-specific scopes (NEW — for section titles and strings unique to a page)

| Scope | Page | Files |
|---|---|---|
| **agents** | Agents section | 40 .vue files |
| **prompts** | Prompt Templates | 14 files |
| **ragTools** | RAG Tools (Configuration/) | 15 files |
| **retrievalTools** | Retrieval Tools | 14 files |
| **aiApps** | AI Apps | 8 files |
| **aiAppTabs** | AI App Tabs | 2 files |
| **apiServers** | API Servers | 5 files |
| **apiTools** | API Tools | 5 files |
| **assistantTools** | Assistant Tools | 10 files |
| **collections** | Knowledge Sources | 13 files |
| **knowledgeProviders** | Knowledge Source Providers | 7 files |
| **models** | Models / Model Config | 6 files |
| **modelProviders** | Model Providers | 12 files |
| **mcpServers** | MCP Servers | 6 files |
| **evaluationSets** | Test Sets | 8 files |
| **evaluationJobs** | Evaluations | 12 files |
| **apiKeys** | API Keys | 2 files |
| **noteTaker** | Note Taker | 6 files |
| **deepResearch** | Deep Research | (shared files) |
| **promptQueue** | Prompt Queue | 5 files |
| **jobs** | Jobs | 3 files |
| **files** | File Storage | 1 file |
| **settings** | Import / Export | 1 file |
| **observability** | Traces, Metrics | (shared files) |
| **conversation** | Conversation viewer | 4 files |
| **dashboard** | Dashboard cards | 3 files |

### Naming rules

1. **Reuse `common_` keys** for buttons and labels that appear on 3+ pages (Save, Cancel, Delete, New, Search, Name, Description, etc.)
2. **Use page scope** for strings unique to one section (e.g., `agents_topicSelection`, `ragTools_enableMultilingual`)
3. **Use `section_` and `subtitle_`** for km-section title/subTitle that are reused across entities
4. **Parameters** use `{paramName}` syntax: `"access_loggedInAs": "Logged in as {name}"`
5. **No nesting** — all keys are flat with underscore-separated scope prefix

---

## Migration Phases

### Phase 0: Infrastructure (DONE)
- [x] Paraglide JS installed and configured
- [x] messages/en.json and messages/ru.json created (302 keys)
- [x] Vue reactivity composable (useLocale)
- [x] Vite plugins in both apps
- [x] LocaleSwitcher component
- [x] :key="locale" on App.vue for instant re-render

### Phase 1: Global Shell (HIGH VISIBILITY)
Components visible on every page — maximum impact for minimal effort.

| # | File | Strings | Status |
|---|---|---|---|
| 1.1 | `LayoutDefault.vue` | Search, Help, Profile, Log out | DONE |
| 1.2 | `Toolbar.vue` | All 5 nav sections + 25 menu items | TODO |
| 1.3 | `Layouts/WorkspaceTabBar.vue` | Close, Pin Tab, Unpin, Close Others, Close All, Unsaved Changes | TODO |
| 1.4 | `Layouts/DetailsLayout.vue` | (props only, no hardcoded strings) | SKIP |
| 1.5 | `Layouts/GlobalSearch.vue` | Search placeholder, result labels | TODO |
| 1.6 | `App.vue` | Access restricted, logged in as, logout | DONE |

**Estimated keys to add:** ~40
**Estimated effort:** Small

### Phase 2: Profile Page (DONE)
- [x] `Profile/ProfilePage.vue` — All sections translated

### Phase 3: Common Page Patterns
Most entity pages follow the same pattern: Page.vue (list + Search + New button) + CreateNew.vue (dialog) + details.vue. Migrate the pattern once, then repeat.

| # | Directory | Files | Key strings | Status |
|---|---|---|---|---|
| 3.1 | `Prompts/` | Page.vue + 13 more | Name, System name, Category, Created, Last Updated, Search, New | Page.vue DONE, rest TODO |
| 3.2 | `Agents/` | Page.vue + 39 more | New, Search + massive detail sections | TODO |
| 3.3 | `Configuration/` (RAG Tools) | Page.vue + 14 more | New, Search + detail sections | TODO |
| 3.4 | `Retrieval/` | Page.vue + 13 more | New, Search + detail sections | TODO |
| 3.5 | `AIApps/` | Page.vue + 7 more | New, Search + detail sections | TODO |
| 3.6 | `Collections/` | Page.vue + 12 more | New, Search + detail sections | TODO |
| 3.7 | `KnowledgeProviders/` | 7 files | New, Search + detail sections | TODO |
| 3.8 | `ModelProviders/` | 12 files | New, Search + detail sections | TODO |
| 3.9 | `ModelConfig/` | 6 files | detail sections | TODO |
| 3.10 | `ApiServers/` | 5 files | detail sections | TODO |
| 3.11 | `AssistantTools/` | 10 files | New, Search + detail sections | TODO |
| 3.12 | `Mcp/` | 6 files | New, Search + detail sections | TODO |
| 3.13 | `ApiTools/` | 5 files | detail sections | TODO |
| 3.14 | `ApiKeys/` | 2 files | New, Search, Create API Key | TODO |
| 3.15 | `EvaluationSets/` | 8 files | New, Search + detail sections | TODO |
| 3.16 | `EvaluationJobs/` | 12 files | detail sections | TODO |
| 3.17 | `NoteTaker/` | 6 files | detail sections | TODO |
| 3.18 | `PromptQueue/` | 5 files | Execute, Steps, Add step | TODO |
| 3.19 | `AIAppTabs/` | 2 files | detail sections | TODO |

### Phase 4: Supporting Pages
| # | Directory | Files | Status |
|---|---|---|---|
| 4.1 | `KnowledgeGraph/` | 4 files + nested | TODO |
| 4.2 | `Dashboard/` | 3 files | TODO |
| 4.3 | `Conversation/` | 4 files | TODO |
| 4.4 | `Jobs/` | 3 files | TODO |
| 4.5 | `Files/` | 1 file | TODO |
| 4.6 | `Settings/` (Import/Export) | 1 file | TODO |
| 4.7 | `Observability/` (via shared) | traces, metrics | TODO |
| 4.8 | `DeepResearch/` | (shared components) | TODO |
| 4.9 | `CollectionItems/` | 2 files | TODO |
| 4.10 | `Search/` | 1 file | TODO |

### Phase 5: Shared Components & Utilities
| # | Item | Status |
|---|---|---|
| 5.1 | `base/EncryptedInput.vue` | TODO |
| 5.2 | `base/Secrets.vue` | TODO |
| 5.3 | `shared/TestSetsTable.vue` | TODO |
| 5.4 | `composables/useNotify.ts` | TODO |
| 5.5 | `config/entityFieldConfig.js` | TODO |

### Phase 6: Panel App
| # | Item | Status |
|---|---|---|
| 6.1 | Chat components (Agent/Tab, ChatWith*) | DONE |
| 6.2 | FeedbackModal | DONE |
| 6.3 | LayoutTab, EmptyTab, Multi/Tab | DONE |
| 6.4 | login.vue | DONE |
| 6.5 | ErrorDialog | DONE |
| 6.6 | Search/Tab, Retrieval/Tab | DONE |

---

## Migration Workflow (per file)

### For admin app components (direct import):
```vue
<script>
import { m } from '@/paraglide/messages'
export default {
  setup() {
    return { m, /* ... */ }
  }
}
</script>

<!-- In template: -->
<!-- BEFORE: label='Save' -->
<!-- AFTER:  :label='m.common_save()' -->
```

### For `<script setup>` components:
```vue
<script setup>
import { m } from '@/paraglide/messages'
</script>

<!-- m is auto-available in template -->
```

### Steps per file:
1. Add `import { m } from '@/paraglide/messages'`
2. Return `m` from `setup()` (Options API only)
3. Replace static `label='...'` with `:label='m.key()'`
4. Replace `{{ "text" }}` with `{{ m.key() }}`
5. Replace `title='...'` with `:title='m.key()'` on km-section etc.
6. Add missing keys to `messages/en.json` and `messages/ru.json`
7. Verify no hardcoded strings remain

### Checklist per phase:
- [ ] Add new keys to en.json
- [ ] Add Russian translations to ru.json
- [ ] Migrate all .vue files in the phase
- [ ] Build succeeds (`nx run magnet-admin:build`)
- [ ] Visual check: switch to RU, verify translations appear

---

## File Count Summary

| Category | Files | Status |
|---|---|---|
| Global shell (Layout, Toolbar, App) | 6 | 3 DONE, 3 TODO |
| Profile | 2 | DONE |
| Entity pages (Phase 3) | ~195 | 1 DONE, ~194 TODO |
| Supporting pages (Phase 4) | ~20 | TODO |
| Shared/base (Phase 5) | ~5 | TODO |
| Panel app (Phase 6) | ~15 | DONE |
| **Total** | **~243** | **~20 DONE, ~223 TODO** |

---

## Key Estimation

| Category | Existing | To Add | Total |
|---|---|---|---|
| common_ | 65 | ~20 | ~85 |
| nav_ | 0 | ~35 | ~35 |
| auth_ | 30 | 0 | 30 |
| validation_ | 10 | 0 | 10 |
| entity_ | 40 | ~5 | ~45 |
| dialog_ | 30 | ~10 | ~40 |
| section_ | 55 | ~20 | ~75 |
| subtitle_ | 70 | ~15 | ~85 |
| hint_ | 15 | ~10 | ~25 |
| placeholder_ | 35 | ~15 | ~50 |
| error_ | 15 | ~5 | ~20 |
| agents_ (page-specific) | 0 | ~50 | ~50 |
| ragTools_ | 0 | ~20 | ~20 |
| retrievalTools_ | 0 | ~15 | ~15 |
| Other page scopes | 0 | ~80 | ~80 |
| **Total** | **~302** | **~300** | **~600** |

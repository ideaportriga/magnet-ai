# Paraglide JS — Migration Guide

## Architecture

```
web/
├── project.inlang/settings.json    # Paraglide config (shared)
├── messages/
│   ├── en.json                     # English translations (source)
│   └── ru.json                     # Russian translations
├── packages/shared/src/lib/i18n/
│   ├── index.ts                    # Exports
│   └── useLocale.ts                # Vue reactivity composable
├── apps/@ipr/magnet-admin/
│   ├── src/paraglide/              # Auto-generated (gitignored)
│   └── vite.config.ts              # Paraglide Vite plugin
└── apps/@ipr/magnet-panel/
    ├── src/paraglide/              # Auto-generated (gitignored)
    └── vite.config.ts              # Paraglide Vite plugin
```

## How It Works

1. **Build time**: Paraglide Vite plugin reads `messages/*.json` and compiles them into typed JS functions in `src/paraglide/`
2. **Runtime**: You import `m` from `@/paraglide/messages` and call functions like `m.common_save()`
3. **Reactivity**: The `useLocale()` composable from `@shared/i18n` provides reactive locale switching without page reload

## Usage Examples

### Basic text replacement

**Before:**
```vue
<template>
  <km-btn label="Save" @click="save" />
  <km-btn label="Cancel" @click="cancel" />
  <h2>General info</h2>
</template>
```

**After:**
```vue
<script setup>
import { m } from '@/paraglide/messages'
</script>

<template>
  <km-btn :label="m.common_save()" @click="save" />
  <km-btn :label="m.common_cancel()" @click="cancel" />
  <h2>{{ m.section_generalInfo() }}</h2>
</template>
```

### With parameters

**Before:**
```vue
<template>
  <span>Logged in as {{ userDisplayName }}</span>
</template>
```

**After:**
```vue
<script setup>
import { m } from '@/paraglide/messages'
</script>

<template>
  <span>{{ m.access_loggedInAs({ name: userDisplayName }) }}</span>
</template>
```

### In JavaScript/TypeScript

**Before:**
```js
notify.success('Copied to clipboard')
```

**After:**
```js
import { m } from '@/paraglide/messages'
notify.success(m.common_copiedToClipboard())
```

### Locale switching

```vue
<script setup>
import { useLocale } from '@shared/i18n'
const { locale, setLocale, locales } = useLocale()
</script>

<template>
  <div>Current: {{ locale }}</div>
  <button v-for="loc in locales" :key="loc" @click="setLocale(loc)">
    {{ loc }}
  </button>
</template>
```

Or use the ready-made component:

```vue
<template>
  <locale-switcher />
</template>
```

### In shared components (ui-comp)

Shared UI components should accept translated strings via **props** rather than importing `m` directly. This keeps them decoupled from the translation keys:

```vue
<!-- ui-comp/components/base/PopupConfirm.vue -->
<template>
  <km-btn :label="confirmLabel" @click="confirm" />
  <km-btn :label="cancelLabel" @click="cancel" />
</template>

<script setup>
defineProps({
  confirmLabel: { type: String, default: 'Confirm' },
  cancelLabel: { type: String, default: 'Cancel' },
})
</script>
```

The **consuming app** passes translated labels:

```vue
<popup-confirm
  :confirm-label="m.common_confirm()"
  :cancel-label="m.common_cancel()"
/>
```

## Adding a New Translation Key

1. Add the key to `web/messages/en.json`:
   ```json
   "myFeature_newKey": "Hello {name}!"
   ```

2. Add the Russian translation to `web/messages/ru.json`:
   ```json
   "myFeature_newKey": "Привет, {name}!"
   ```

3. The Vite dev server auto-recompiles — `m.myFeature_newKey({ name })` is immediately available with full autocomplete.

## Adding a New Language

1. Add the language tag to `web/project.inlang/settings.json`:
   ```json
   "languageTags": ["en", "ru", "de"]
   ```

2. Create `web/messages/de.json` with translations

3. Update `LocaleSwitcher.vue` locale labels:
   ```js
   const localeLabels = {
     en: 'English',
     ru: 'Русский',
     de: 'Deutsch',
   }
   ```

## Key Naming Convention

Keys use `category_camelCaseName` format:

| Prefix | Usage |
|---|---|
| `common_` | Shared buttons, labels, actions |
| `auth_` | Authentication & login |
| `validation_` | Form validation messages |
| `entity_` | Entity type names |
| `dialog_` | Dialog/modal titles |
| `confirm_` | Confirmation button labels |
| `section_` | Section headers |
| `subtitle_` | Section descriptions/help text |
| `hint_` | Help text, tooltips, instructions |
| `placeholder_` | Input placeholders |
| `panel_` | Panel app specific |
| `feedback_` | User feedback UI |
| `error_` | Error messages |
| `access_` | Access control messages |
| `emptyState_` | Empty state messages |
| `user_` | User profile/security |
| `knowledgeGraph_` | Knowledge Graph specific |
| `metadata_` | Metadata studio specific |
| `filter_` | Filter presets |
| `confirmation_` | Action confirmation UI |
| `metadataFilter_` | Metadata filter editor |

## Migration Strategy

Migrate gradually, one component at a time:

1. **Start with shared UI components** (`ui-comp`) — ensure props accept translated strings
2. **Migrate page by page** in `magnet-admin` — begin with high-traffic pages
3. **Migrate `magnet-panel`** — fewer components, faster to complete
4. **Migrate validation messages** in `shared/utils/validationRules.js`
5. **Migrate error messages** in services/composables

Each component migration is a small, reviewable PR. No big-bang rewrite needed.

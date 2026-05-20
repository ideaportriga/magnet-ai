<template>
  <DsDialog v-model:open="openLocal" size="lg" :dismissible="!isLoading">
    <template #title>{{ m.aiEdit_title() }} · {{ entityType }}</template>
    <template #description>
      {{ m.aiEdit_description() }}
    </template>

    <div class="stack" data-gap="md">
      <div class="stack" data-gap="2xs">
        <div class="km-field text-secondary-text pb-xs pl-sm">Model</div>
        <km-select
          v-model="selectedModel"
          height="auto"
          min-height="36px"
          placeholder="Use tenant default"
          :options="modelOptions"
          :disable="isLoading || modelsLoading"
          option-label="display_name"
          option-value="system_name"
          emit-value
          has-dropdown-search
          clearable
        >
          <template #option="{ opt }">
            <!-- Mirrors the slot used by `Prompts/advancedsettings.vue`
                 so both LLM pickers feel identical. The legacy
                 `<li class="km-item ba-border">` wrapper would
                 otherwise paint a stray 1px frame around the label —
                 the base `KmSelect.vue` now neutralises that compat
                 case for every call site. -->
            <li class="km-item ba-border">
              <div class="km-item-section">
                <span class="km-item-label km-label">
                  {{ opt.display_name || opt.name || opt.system_name }}
                  <span v-if="opt.is_default" class="text-grey">· default</span>
                </span>
                <div v-if="opt.provider_system_name" class="cluster mt-xs">
                  <km-chip tone="brand" size="sm" dense>{{ opt.provider_system_name }}</km-chip>
                </div>
              </div>
            </li>
          </template>
        </km-select>
        <div v-if="modelsError" class="km-description ai-edit__error">
          {{ m.aiEdit_modelLoadFailed({ error: modelsError }) }}
        </div>
        <div v-else-if="!modelsLoading && modelOptions.length === 0" class="km-description text-grey">
          {{ m.aiEdit_noModels() }}
        </div>
      </div>

      <km-input
        v-model="instruction"
        type="textarea"
        rows="6"
        autogrow
        :placeholder="placeholder"
        :disable="isLoading"
        @keydown.meta.enter="submit"
        @keydown.ctrl.enter="submit"
      />

      <div v-if="lastUsage" class="km-description text-grey">
        {{ lastUsage.total_tokens }} tokens ·
        ${{ lastUsage.cost_usd.toFixed(4) }} ·
        {{ lastUsage.latency_ms }} ms
        <span v-if="lastUsage.model"> · {{ lastUsage.model }}</span>
      </div>

      <div v-if="errorMessage" class="km-description ai-edit__error">
        {{ errorMessage }}
      </div>

      <div v-if="lastDiffEntries.length" class="stack" data-gap="xs">
        <div class="km-heading-7">
          {{ m.aiEdit_proposedChange() }} · {{ m.audit_fieldCount({ count: lastDiffEntries.length }) }}
        </div>
        <div class="ai-edit__diff-list">
          <div
            v-for="[path, change] in lastDiffEntries"
            :key="path"
            class="ai-edit__diff-row"
          >
            <div class="ai-edit__diff-path font-mono">{{ path }}</div>
            <div class="ai-edit__diff-values font-mono">
              <span class="ai-edit__diff-from">{{ formatScalar(change.from) }}</span>
              <km-glyph name="arrow-right" size="12px" tone="muted" />
              <span class="ai-edit__diff-to">{{ formatScalar(change.to) }}</span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <template #footer>
      <km-btn flat :label="m.common_close()" :disable="isLoading" @click="openLocal = false" />
      <km-btn
        icon="magic"
        :label="m.aiEdit_generate()"
        :loading="isLoading"
        :disable="isLoading || !instruction.trim()"
        @click="submit"
      />
    </template>
  </DsDialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { DsDialog } from '@ds/primitives'
import { notify } from '@shared/utils/notify'
import { useEntityQueries } from '@/queries/entities'
import {
  proposeEntityAiEdit,
  type AIEditResponse,
  type AIEditUsage,
  type AIEditDiffValue,
} from '@/api/aiEdit'
import type { Model } from '@/types'
import { m } from '@/paraglide/messages'

const props = defineProps<{
  open: boolean
  entityType: string
  entityId: string
  /** Initial model selection (system_name). null/undefined = tenant default. */
  model?: string | null
  placeholder?: string
}>()

const emit = defineEmits<{
  (e: 'update:open', value: boolean): void
  /** Fires when the LLM produced a valid new state. Host applies it
   *  to its editBuffer.draft via `applyAiPatch`. */
  (e: 'apply', payload: AIEditResponse): void
}>()

const openLocal = computed<boolean>({
  get: () => props.open,
  set: (v) => emit('update:open', v),
})

const instruction = ref('')
const isLoading = ref(false)
const errorMessage = ref('')
const lastUsage = ref<AIEditUsage | null>(null)
const lastResult = ref<AIEditResponse | null>(null)

// ── Model selector ─────────────────────────────────────────────────
const selectedModel = ref<string | null>(props.model ?? null)

const queries = useEntityQueries()
// Same query the Prompt Template's advanced-settings model picker uses —
// kept identical so the TanStack cache key matches and the user gets
// instant results if they've recently visited that page.
const modelsQuery = queries.model.useList()
const modelsLoading = computed(() => modelsQuery.isLoading.value)
const modelsError = computed(() =>
  modelsQuery.error.value ? String(modelsQuery.error.value.message ?? modelsQuery.error.value) : '',
)

const modelOptions = computed<Model[]>(() => {
  const items = (modelsQuery.data.value?.items ?? []) as Model[]
  return items
    .filter((m) => m.type === 'prompts' && (m.is_active ?? true) && m.system_name)
    .sort((a, b) => {
      // Default model first, then alphabetical by display_name (or name/
      // system_name fallback).
      if ((a.is_default ?? false) !== (b.is_default ?? false)) {
        return (b.is_default ? 1 : 0) - (a.is_default ? 1 : 0)
      }
      const an = (a.display_name || a.name || a.system_name || '').toString()
      const bn = (b.display_name || b.name || b.system_name || '').toString()
      return an.localeCompare(bn)
    })
})

// When the model list arrives, default the picker to the tenant
// default unless the host supplied an initial value or the user already
// chose one in this dialog session.
watch(
  () => modelsQuery.data.value,
  () => {
    if (selectedModel.value) return
    const items = (modelsQuery.data.value?.items ?? []) as Model[]
    const def = items.find((m) => m.is_default)
    if (def?.system_name) selectedModel.value = def.system_name
  },
  { immediate: true },
)

const lastDiffEntries = computed<[string, AIEditDiffValue][]>(() => {
  const diff = lastResult.value?.diff
  if (!diff) return []
  return Object.entries(diff).sort(([a], [b]) => a.localeCompare(b))
})

const placeholder = computed(
  () =>
    props.placeholder ||
    m.aiEdit_defaultPlaceholder(),
)

watch(
  () => props.open,
  (v) => {
    // Clear transient state every time the drawer is reopened, but keep
    // the last instruction so the user can refine it.
    if (v) {
      errorMessage.value = ''
    }
  },
)

function formatScalar(v: unknown): string {
  if (v === null || v === undefined) return '∅'
  if (typeof v === 'string') {
    return v.length > 80 ? JSON.stringify(v.slice(0, 80) + '…') : JSON.stringify(v)
  }
  if (typeof v === 'object') {
    try {
      const s = JSON.stringify(v)
      return s.length > 80 ? s.slice(0, 80) + '…' : s
    } catch {
      return '[object]'
    }
  }
  return String(v)
}

async function submit() {
  const text = instruction.value.trim()
  if (!text) return
  isLoading.value = true
  errorMessage.value = ''
  try {
    const result = await proposeEntityAiEdit(props.entityType, props.entityId, {
      instruction: text,
      model: selectedModel.value || null,
    })
    lastResult.value = result
    lastUsage.value = result.usage
    emit('apply', result)
    notify.success(
      m.aiEdit_applied({ count: Object.keys(result.diff || {}).length }),
    )
  } catch (err: unknown) {
    const msg =
      err instanceof Error
        ? err.message
        : m.aiEdit_failed()
    errorMessage.value = msg
    notify.error(msg)
  } finally {
    isLoading.value = false
  }
}
</script>

<style scoped>
.ai-edit__error {
  color: var(--ds-color-danger-on-soft);
  background: var(--ds-color-danger-soft);
  border: 1px solid var(--ds-color-danger-solid);
  border-radius: var(--ds-radius-md);
  padding: var(--ds-space-sm) var(--ds-space-md);
}
.ai-edit__diff-list {
  display: flex;
  flex-direction: column;
  gap: var(--ds-space-xs);
  max-block-size: 15rem;
  overflow: auto;
}
.ai-edit__diff-row {
  display: flex;
  flex-direction: column;
  gap: var(--ds-space-2xs);
  padding: var(--ds-space-xs) var(--ds-space-sm);
  border-radius: var(--ds-radius-md);
  background: var(--ds-color-surface-sunken);
}
.ai-edit__diff-path {
  font-size: 0.75rem;
  color: var(--ds-color-fg-muted);
  word-break: break-all;
}
.ai-edit__diff-values {
  display: flex;
  align-items: center;
  gap: var(--ds-space-xs);
  font-size: var(--ds-font-size-md);
  flex-wrap: wrap;
}
.ai-edit__diff-from {
  color: var(--ds-color-danger-on-soft);
  text-decoration: line-through;
  text-decoration-color: var(--ds-color-danger-solid);
}
.ai-edit__diff-to {
  color: var(--ds-color-success-on-soft);
  font-weight: 600;
}
.ai-edit__link {
  color: var(--ds-color-primary);
  text-decoration: underline;
}
</style>

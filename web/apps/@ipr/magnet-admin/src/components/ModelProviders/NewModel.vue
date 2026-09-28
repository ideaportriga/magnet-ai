<template lang="pug">
q-dialog(:model-value='showNewDialog', @update:model-value='onOpenChange')
  q-card.new-model.column.no-wrap
    q-card-section.row.items-center.q-pb-none
      .km-heading-7 {{ step === 'review' ? 'Review Model Info' : 'New Model' }}
      q-space
      q-btn(icon='close', flat, round, dense, :disable='isBusy', @click='emit("cancel")')

    q-card-section.new-model__body.scroll
      .column.q-gap-16(v-show='step === "form"', data-test='new-model-form')
        .row.q-col-gutter-md
          .col-12.col-sm-6
            .km-field.text-secondary-text.q-pb-xs.q-pl-8 Provider model name
            km-input(
              ref='modelRef',
              v-model='model',
              data-test='name-input',
              height='30px',
              placeholder='E.g. gpt-4o-mini',
              :rules='config?.model?.rules || []'
            )
            .km-description.text-secondary-text.q-pl-8 The exact model or deployment name used by the provider (case-sensitive).
          .col-12.col-sm-6
            .km-field.text-secondary-text.q-pb-xs.q-pl-8 Type
            km-select(
              ref='typeRef',
              v-model='newRow.type',
              data-test='type-select',
              height='auto',
              minHeight='30px',
              placeholder='Type',
              :options='categoryOptions',
              :rules='config?.type?.rules || []',
              emit-value,
              map-options
            )
            .km-description.text-secondary-text.q-pl-8 {{ typeDescription }}
          .col-12.col-sm-6
            .km-field.text-secondary-text.q-pb-xs.q-pl-8 Display name
            km-input(
              ref='displayNameRef',
              v-model='displayName',
              data-test='display-name-input',
              height='30px',
              placeholder='E.g. GPT 4o mini',
              :rules='config?.display_name?.rules || []'
            )
          .col-12.col-sm-6
            .km-field.text-secondary-text.q-pb-xs.q-pl-8 System name
            km-input(
              ref='systemNameRef',
              v-model='systemName',
              data-test='system-name-input',
              height='30px',
              placeholder='E.g. GPT-4O-MINI',
              :rules='config?.system_name?.rules || []'
            )

        q-separator

        .column.q-gap-8
          .column.q-gap-4
            .row.items-baseline.q-gap-8
              span.new-model__section-title Model info from docs
              span.km-description.text-secondary-text Optional
            .km-description.text-secondary-text
              | Paste the model's docs or pricing pages. The description, capabilities and prices are read from them when you click Create, and you review them before the model is saved.
          model-source-blocks(v-model='fill.blocks.value')

      .column.q-gap-16(v-if='step === "review"', data-test='new-model-review')
        .km-description.text-secondary-text Choose what to save with the new model. Everything can be changed later on the model card.
        extraction-review(:entries='fill.entries.value', :sources='fill.resultSources.value')

    q-card-actions.q-pa-md(align='right')
      km-btn(v-if='step === "review"', flat, label='Back', data-test='back-btn', :disable='isBusy', @click='step = "form"')
      km-btn(v-else, flat, label='Cancel', data-test='cancel-btn', @click='emit("cancel")')
      km-btn(label='Create', data-test='save-btn', :disable='step === "form" && fill.overLimit.value', :loading='isBusy', @click='onCreate')
</template>

<script setup lang="ts">
/**
 * New Model dialog — only what a model needs to exist (#466).
 *
 * Name, type, display name and system name. Capabilities are still prefilled
 * silently from the provider's `available-models` probe, and everything else
 * (capabilities, pricing, routing) lives in the model drawer after saving.
 *
 * Optionally the user pastes the model's docs and/or pricing pages — as
 * blocks, one per page, plus typed notes for the extraction. Then Create
 * reads them first and switches the dialog to a review step — the same
 * dialog, not a second one on top — where the pricing option is picked;
 * Create there saves the model with what was kept. Without a pasted page,
 * Create saves right away.
 */
import { computed, onMounted, reactive, ref } from 'vue'
import { useStore } from 'vuex'
import { useChroma } from '@shared'

import { categoryOptions } from '../../config/model/model.js'
import ExtractionReview from './ExtractionReview.vue'
import ModelSourceBlocks from './ModelSourceBlocks.vue'
import { toModelSystemName } from './modelSystemName'
import type { FillTarget } from './modelTextFill'
import { useModelTextFill } from './useModelTextFill'

interface AvailableModel {
  id: string
  supports_json_mode?: boolean
  supports_response_schema?: boolean
  supports_function_calling?: boolean
  supports_reasoning?: boolean
}

interface Validatable {
  validate?: () => boolean
}

defineProps<{
  showNewDialog: boolean
}>()

const emit = defineEmits<{
  (e: 'cancel'): void
}>()

const FILL_TARGET_KEY = 'new'

const store = useStore()
const { config, create, requiredFields } = useChroma('model')

const provider = computed(() => store.getters.provider as { id?: string; name?: string; system_name?: string } | null)

const autoChangeCode = ref(true)
const autoChangeDisplayName = ref(true)
const availableModels = ref<AvailableModel[]>([])
const step = ref<'form' | 'review'>('form')
const creating = ref(false)

const modelRef = ref<Validatable>()
const typeRef = ref<Validatable>()
const systemNameRef = ref<Validatable>()
const displayNameRef = ref<Validatable>()

const newRow = reactive<Record<string, any>>({
  name: '',
  provider_name: '',
  provider_system_name: '',
  ai_model: '',
  system_name: '',
  display_name: '',
  type: 'prompts',
  json_mode: false,
  json_schema: false,
  tool_calling: false,
  reasoning: false,
  diarization: false,
  keyterms: false,
  price_input: '',
  price_output: '',
  price_cached: '',
  price_cache_write: '',
  price_cache_write_1h: '',
  price_scheme: 'basic',
  price_standard_input_unit_count: 1000000,
  price_cached_input_unit_count: 1000000,
  price_standard_output_unit_count: 1000000,
  price_input_unit_name: 'tokens',
  price_output_unit_name: 'tokens',
  resources: '',
  description: '',
  configs: {},
})

const TYPE_DESCRIPTIONS: Record<string, string> = {
  prompts: 'Chat completion models for generating text responses (e.g., GPT-4, Claude).',
  embeddings: 'Vector embedding models for text similarity and search (e.g., text-embedding-3-large).',
  're-ranking': 'Re-ranking models for improving search result relevance.',
}
const typeDescription = computed(() => TYPE_DESCRIPTIONS[newRow.type] ?? 'Select the type of model based on its purpose.')

function formatProviderName(name?: string): string {
  if (!name) return ''
  // Replace underscores with spaces and convert to proper case
  return name
    .replace(/_/g, ' ')
    .toLowerCase()
    .split(' ')
    .map((word) => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

const model = computed({
  get: () => newRow.ai_model || '',
  set: (val: string) => {
    newRow.ai_model = val
    newRow.name = val

    // Auto-detect capabilities
    checkModelCapabilities(val)

    if (autoChangeCode.value && provider.value?.system_name) {
      newRow.system_name = toModelSystemName(provider.value.system_name, val)
    }
    if (autoChangeDisplayName.value && provider.value?.name && val) {
      newRow.display_name = `${formatProviderName(provider.value.name)}: ${val}`
    }
  },
})

const systemName = computed({
  get: () => newRow.system_name || '',
  set: (val: string) => {
    newRow.system_name = val
    autoChangeCode.value = false
  },
})

const displayName = computed({
  get: () => newRow.display_name || '',
  set: (val: string) => {
    newRow.display_name = val
    autoChangeDisplayName.value = false
  },
})

const fillTargets = computed<FillTarget[]>(() => [
  {
    key: FILL_TARGET_KEY,
    ai_model: newRow.ai_model,
    display_name: newRow.display_name || null,
    type: newRow.type,
    configs: newRow.configs,
  },
])
const fill = useModelTextFill(
  fillTargets,
  computed(() => provider.value?.name ?? provider.value?.system_name ?? null)
)
const isBusy = computed(() => fill.isExtracting.value || creating.value)

onMounted(() => {
  if (provider.value?.system_name) {
    newRow.provider_system_name = provider.value.system_name
    newRow.provider_name = provider.value.system_name
  }

  // Fetch available models for auto-detection
  if (provider.value?.id) {
    store
      .dispatch('chroma/availableModels', { payload: provider.value.id, entity: 'provider' })
      .then((result) => {
        if (result?.models) availableModels.value = result.models
      })
      .catch(console.error)
  }
})

function checkModelCapabilities(modelName: string) {
  if (!modelName || !availableModels.value.length) return

  const found = availableModels.value.find((item) => item.id === modelName)
  if (found && newRow.type === 'prompts') {
    newRow.json_mode = found.supports_json_mode || false
    newRow.json_schema = found.supports_response_schema || false
    newRow.tool_calling = found.supports_function_calling || false
    // reasoning is not typically returned by litellm yet, but if it is:
    if (found.supports_reasoning !== undefined) {
      newRow.reasoning = found.supports_reasoning
    }
  }
}

function validateFields(): boolean {
  const fields = requiredFields?.value
  if (!Array.isArray(fields)) return true
  const refs: Record<string, Validatable | undefined> = {
    model: modelRef.value,
    type: typeRef.value,
    system_name: systemNameRef.value,
    display_name: displayNameRef.value,
  }
  return !fields.map((field: string) => refs[field]?.validate?.()).includes(false)
}

async function createModel() {
  // Ensure provider is set
  if (provider.value?.system_name) {
    newRow.provider_system_name = provider.value.system_name
    newRow.provider_name = provider.value.system_name
  }

  // Values kept in the review step win over the prefilled defaults.
  const fromText = step.value === 'review' ? fill.patches.value[FILL_TARGET_KEY] : undefined
  const payload: Record<string, any> = { ...newRow, ...(fromText ?? {}) }
  if (!payload.provider_system_name) {
    delete payload.provider_system_name
  }
  // Clean up empty strings - convert to null
  for (const field of ['description', 'resources', 'price_input', 'price_output', 'price_cached', 'price_cache_write', 'price_cache_write_1h']) {
    if (!payload[field]) payload[field] = null
  }

  // Handle configs - only include if not empty
  if (payload.configs && Object.keys(payload.configs).length === 0) {
    delete payload.configs
  }

  creating.value = true
  try {
    // `create` shows the error itself and resolves to `false` on failure.
    const created = await create(JSON.stringify(payload))
    if (created) emit('cancel')
  } finally {
    creating.value = false
  }
}

async function onCreate() {
  if (isBusy.value) return
  if (step.value === 'form') {
    if (!validateFields() || fill.overLimit.value) return
    if (fill.hasText.value) {
      // Read the pasted pages first; the pricing option is picked on review.
      if (await fill.extract()) step.value = 'review'
      return
    }
  }
  await createModel()
}

function onOpenChange(open: boolean) {
  if (!open) emit('cancel')
}
</script>

<style scoped>
.new-model {
  inline-size: 900px;
  max-inline-size: 90vw;
  max-block-size: 85vh;
}
.new-model__body {
  flex: 1;
  min-block-size: 0;
}
.new-model__section-title {
  font-size: 12px;
  font-weight: 600;
  color: var(--q-secondary-text);
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
</style>

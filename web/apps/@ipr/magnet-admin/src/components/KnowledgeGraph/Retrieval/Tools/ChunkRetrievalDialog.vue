<template>
  <kg-dialog-base
    :model-value="modelValue"
    :title="localTool?.label"
    confirm-label="Apply"
    size="md"
    @update:model-value="$emit('update:modelValue', $event)"
    @cancel="$emit('update:modelValue', false)"
    @confirm="save"
  >
    <!-- Tool Description -->
    <kg-prompt-section
      v-model="localTool.description"
      title="Tool Description"
      description="Explain when the agent should use this tool. This description will be used to generate a prompt for the agent."
    />

    <!-- Search Settings Section -->
    <kg-dialog-section
      title="Search Settings"
      description="Choose how the tool searches the graph and, for hybrid search, how many candidates are pooled and how aggressively their rankings are fused."
      icon="tune"
      icon-color="teal-7"
    >
      <div class="column q-gap-16">
        <kg-field-row :cols="1">
          <div>
            <div class="km-input-label q-pb-sm">Method</div>
            <kg-dropdown-field v-model="localTool.searchMethod" :options="searchMethodOptions" dense />
          </div>
        </kg-field-row>

        <kg-field-row :cols="2">
          <div v-if="localTool.searchMethod === 'keyword' || localTool.searchMethod === 'hybrid'">
            <div class="km-input-label q-pb-sm" title="Constant in 1/(k+rank). Higher k = less aggressive rank discrimination. Typical: 60.">
              RRF k
            </div>
            <km-input
              :model-value="localTool.rrfK"
              type="number"
              :min="1"
              :max="200"
              @update:model-value="localTool.rrfK = clampInt($event, 1, 200)"
            />
          </div>
          <div :class="{ 'col-span-2': localTool.searchMethod === 'vector' || localTool.searchMethod === 'full_text' }">
            <div class="km-input-label q-pb-sm" title="Maximum number of candidates considered. Each ranked sub-query fetches up to this many rows before they are merged and fused, and it is the upper bound for the Result Limit.">
              Candidate Pool
            </div>
            <km-input
              :model-value="localTool.candidatePoolSize"
              type="number"
              :min="1"
              :max="200"
              @update:model-value="localTool.candidatePoolSize = clampInt($event, 1, 200)"
            />
          </div>
        </kg-field-row>
      </div>
    </kg-dialog-section>

    <!-- Query Reformulation Section -->
    <kg-dialog-section
      title="Query Reformulation"
      description="Select the prompt template used to turn the agent's intent and context into keyword-friendly terms and vector-friendly phrases before searching, and how many search queries to generate per search type. Leave the template empty to search the intent directly."
      icon="auto_fix_high"
      icon-color="indigo-7"
    >
      <div class="column q-gap-16">
        <div>
          <div class="km-input-label q-pb-sm">Prompt Template</div>
          <kg-dropdown-field
            v-model="localTool.promptTemplateName"
            :options="promptTemplateOptions"
            :loading="loadingPromptTemplates"
            placeholder="No reformulation"
            option-meta="value"
            searchable
            clearable
            dense
          />
        </div>

        <kg-field-row :cols="2">
          <div v-if="localTool.searchMethod !== 'vector'" :class="{ 'col-span-2': localTool.searchMethod === 'keyword' || localTool.searchMethod === 'full_text' }">
            <div class="km-input-label row justify-between q-pb-12">
              <span title="How many distinct keyword queries to generate from the intent. Each adds a full-text (and fuzzy, if enabled) search.">Keyword Queries to Generate</span>
              <span class="text-primary text-weight-bold">{{ localTool.keywordVariants }}</span>
            </div>
            <q-slider v-model="localTool.keywordVariants" :min="1" :max="5" :step="1" snap markers color="primary" />
          </div>
          <div v-if="localTool.searchMethod === 'vector' || localTool.searchMethod === 'hybrid'" :class="{ 'col-span-2': localTool.searchMethod === 'vector' }">
            <div class="km-input-label row justify-between q-pb-12">
              <span title="How many distinct semantic queries to generate from the intent. Each adds a vector search.">Vector Queries to Generate</span>
              <span class="text-primary text-weight-bold">{{ localTool.vectorVariants }}</span>
            </div>
            <q-slider v-model="localTool.vectorVariants" :min="1" :max="5" :step="1" snap markers color="primary" />
          </div>
        </kg-field-row>
      </div>
    </kg-dialog-section>

    <!-- Result Filtering Section -->
    <kg-dialog-section
      title="Result Filtering"
      description="Set the minimum score and cap how many results are returned to the agent."
      icon="filter_alt"
      icon-color="blue-7"
    >
      <kg-field-row :cols="2">
        <div>
          <div class="km-input-label row justify-between q-pb-12">
            <span>Score Threshold</span>
            <span class="text-primary text-weight-bold">{{ localTool.scoreThreshold }}</span>
          </div>
          <q-slider v-model="localTool.scoreThreshold" :min="0" :max="1" :step="0.01" color="primary" />
        </div>
        <div>
          <div class="km-input-label row justify-between q-pb-12">
            <span title="Final number of results returned to the agent after fusion. Capped at the Candidate Pool.">Result Limit</span>
            <span class="text-primary text-weight-bold">{{ localTool.limit }}</span>
          </div>
          <q-slider v-model="localTool.limit" :min="1" :max="limitMax" :step="1" snap color="primary" />
        </div>
      </kg-field-row>
    </kg-dialog-section>

    <!-- Context Expansion Section -->
    <kg-dialog-section
      title="Context Expansion"
      description="Enrich search results by including related chunks from the knowledge graph. Choose whether the agent can override the context expansion or must follow this configuration."
      icon="hub"
      icon-color="purple-7"
    >
      <template #title-badge>
        <q-badge color="orange-1" text-color="orange-9" label="Coming Soon" class="text-weight-medium q-mt-xs" />
      </template>
      <template #header-actions>
        <kg-section-control v-model="localTool.contextControl" :disabled="true" />
      </template>

      <div class="column q-gap-16 section-fields-disabled">
        <kg-field-row :cols="2">
          <kg-toggle-field
            :model-value="false"
            title="Include Referenced Chunks"
            description="Include chunks, referenced by the matched chunks."
            disabled
          />
          <kg-toggle-field
            :model-value="false"
            title="Include Adjacent Chunks"
            description="Include adjacent chunks that share the same parent."
            disabled
          />
        </kg-field-row>
      </div>
    </kg-dialog-section>
  </kg-dialog-base>
</template>

<script setup lang="ts">
import { useChroma } from '@shared'
import { computed, onMounted, ref, watch } from 'vue'
import { KgDialogBase, KgDialogSection, KgDropdownField, KgFieldRow, KgPromptSection, KgSectionControl, KgToggleField } from '../../common'
import { searchMethodOptions } from '../models'

const props = defineProps<{
  modelValue: boolean
  tool: any
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'save', tool: any): void
}>()

const localTool = ref<any>(null)

const clampInt = (val: unknown, min: number, max: number): number => {
  const n = Math.round(Number(val))
  if (!Number.isFinite(n)) return min
  return Math.min(max, Math.max(min, n))
}

// Result Limit is bounded by the Candidate Pool: you cannot return more results
// than were pooled for fusion.
const limitMax = computed(() => Math.max(1, Number(localTool.value?.candidatePoolSize) || 1))

const { items: promptTemplateItems, get: fetchPromptTemplates } = useChroma('promptTemplates')
const loadingPromptTemplates = ref(false)

const promptTemplateOptions = computed(() => {
  const list = (promptTemplateItems.value || []) as any[]
  const options = list
    .filter((p) => p?.system_name)
    .map((p) => ({ label: p.display_name || p.name || p.system_name, value: p.system_name }))
    .sort((a, b) => a.label.localeCompare(b.label))

  // Keep the currently configured template selectable even if not yet loaded.
  const current = localTool.value?.promptTemplateName
  if (current && !options.some((o) => o.value === current)) {
    options.unshift({ label: current, value: current })
  }
  return options
})

watch(
  () => props.tool,
  (newVal) => {
    if (newVal) {
      localTool.value = JSON.parse(JSON.stringify(newVal))
    }
  },
  { immediate: true, deep: true }
)

// Keep Result Limit within the Candidate Pool when the pool is lowered.
watch(
  () => localTool.value?.candidatePoolSize,
  (pool) => {
    const max = Math.max(1, Number(pool) || 1)
    if (localTool.value && Number(localTool.value.limit) > max) {
      localTool.value.limit = max
    }
  }
)

onMounted(async () => {
  if ((promptTemplateItems.value || []).length === 0) {
    loadingPromptTemplates.value = true
    try {
      await fetchPromptTemplates()
    } finally {
      loadingPromptTemplates.value = false
    }
  }
})

const save = () => {
  emit('save', localTool.value)
  emit('update:modelValue', false)
}
</script>

<style scoped>
.section-fields-disabled {
  opacity: 0.5;
  pointer-events: none;
  transition: opacity 0.2s ease;
}
</style>

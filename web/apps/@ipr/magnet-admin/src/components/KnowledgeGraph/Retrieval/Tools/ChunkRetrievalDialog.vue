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
      description="Defines when and why the agent should invoke this tool. The text is injected into the agent's system prompt, so clear, specific wording directly improves retrieval accuracy."
    />

    <!-- Search Settings Section -->
    <kg-dialog-section
      title="Search Settings"
      description="Select the retrieval algorithm and control how many candidates each sub-query fetches before results are merged and ranked."
      icon="tune"
      icon-color="teal-7"
    >
      <div class="column q-gap-16">
        <kg-field-row :cols="1">
          <div>
            <div class="km-input-label q-pb-sm">Method</div>
            <kg-dropdown-field v-model="localTool.searchMethod" :options="searchMethodOptions" option-description="description" dense />
          </div>
        </kg-field-row>

        <kg-field-row :cols="2">
          <kg-field-row
            :class="{ 'col-span-2': localTool.searchMethod === 'vector' || localTool.searchMethod === 'full_text' }"
            label="Candidate Pool"
            hint="Maximum number of candidate chunks each sub-query retrieves before results are merged and re-ranked. Increasing this value improves recall (fewer relevant chunks are missed) but adds latency and compute cost. This value also serves as the upper bound for Result Limit — you cannot return more results than were pooled. Typical range: 20–50 for focused searches, 50–100 when broad coverage matters."
          >
            <km-input
              :model-value="localTool.candidatePoolSize"
              type="number"
              :min="1"
              :max="200"
              @update:model-value="localTool.candidatePoolSize = clampInt($event, 1, 200)"
            />
          </kg-field-row>
          <kg-field-row
            v-if="localTool.searchMethod === 'hybrid'"
            label="RRF k"
            hint="Reciprocal Rank Fusion constant used in the formula 1 / (k + rank). A higher value flattens rank differences, giving lower-ranked results more influence. A lower value amplifies the gap between top and bottom ranks. The default of 60 is the standard RRF constant and works well for most cases. Lower it (e.g. 10–30) to favor top-ranked results more aggressively; raise it (e.g. 80–150) when you want broader, more balanced fusion across search methods."
          >
            <km-input
              :model-value="localTool.rrfK"
              type="number"
              :min="1"
              :max="200"
              @update:model-value="localTool.rrfK = clampInt($event, 1, 200)"
            />
          </kg-field-row>
        </kg-field-row>
      </div>
    </kg-dialog-section>

    <!-- Query Reformulation Section -->
    <kg-dialog-section
      title="Query Reformulation"
      description="Before searching, the agent's raw intent can be rewritten into optimized keyword and semantic queries using an LLM prompt template. This improves recall by generating diverse phrasings that match different indexing strategies. Leave the template empty to pass the agent's query directly to the search engine without reformulation."
      icon="auto_fix_high"
      icon-color="indigo-7"
    >
      <div class="column q-gap-16">
        <kg-field-row
          label="Prompt Template"
          hint="The LLM prompt used to rewrite the agent's intent into search-optimized queries. The template receives the original query and context, and outputs keyword-friendly terms (for full-text search) and semantically rephrased sentences (for vector search). Select 'No reformulation' to skip this step and search the raw intent directly — useful when queries are already well-formed or latency is critical."
        >
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
        </kg-field-row>

        <kg-field-row :cols="2">
          <kg-field-row
            v-if="localTool.searchMethod !== 'vector'"
            :class="{ 'col-span-2': localTool.searchMethod === 'full_text' }"
            label="Keyword Queries to Generate"
            hint="Number of distinct keyword query variants the reformulation prompt should produce. Each variant runs a separate full-text search. More variants improve recall by covering synonyms, abbreviations, and alternate phrasings, but increase latency proportionally. Start with 1–2 for focused lookups; use 3–5 for exploratory or ambiguous queries."
          >
            <q-slider v-model="localTool.keywordVariants" :min="1" :max="5" :step="1" label snap markers color="primary" />
          </kg-field-row>
          <kg-field-row
            v-if="localTool.searchMethod === 'vector' || localTool.searchMethod === 'hybrid'"
            :class="{ 'col-span-2': localTool.searchMethod === 'vector' }"
            label="Vector Queries to Generate"
            hint="Number of distinct semantic query variants the reformulation prompt should produce. Each variant is embedded and runs a separate vector similarity search. Multiple variants help capture different aspects of the intent — e.g. a question rephrased as a statement, or a concept expressed with domain-specific vs. general terminology. Start with 1–2; use 3–5 when the query is complex or multi-faceted."
          >
            <q-slider v-model="localTool.vectorVariants" :min="1" :max="5" :step="1" label snap markers color="primary" />
          </kg-field-row>
        </kg-field-row>
      </div>
    </kg-dialog-section>

    <!-- Result Filtering Section -->
    <kg-dialog-section
      title="Result Filtering"
      description="Control the quality and quantity of results returned to the agent. Chunks below the score threshold are discarded, and the remaining results are capped at the result limit."
      icon="filter_alt"
      icon-color="blue-7"
    >
      <kg-field-row :cols="2">
        <kg-field-row
          label="Score Threshold"
          hint="Minimum normalized relevance score (0–1) a chunk must reach to be included in the results. Chunks scoring below this value are discarded. A higher threshold returns fewer but more relevant results; a lower threshold increases recall at the risk of including noise. Typical values: 0.5–0.6 for broad searches, 0.7–0.8 for precise lookups. Set to 0 to disable filtering."
        >
          <q-slider v-model="localTool.scoreThreshold" :min="0" :max="1" :step="0.01" label color="primary" />
        </kg-field-row>
        <kg-field-row
          label="Result Limit"
          hint="Maximum number of chunks returned to the agent after scoring and filtering. Capped by the Candidate Pool size — you cannot return more results than were pooled. A smaller limit reduces token usage in the agent's context window; a larger limit gives the agent more material to reason over. Typical range: 3–5 for focused answers, 5–10 for comprehensive retrieval."
        >
          <q-slider v-model="localTool.limit" :min="1" :max="limitMax" :step="1" label snap color="primary" />
        </kg-field-row>
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

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
      description="Select the retrieval algorithm and configure scoring and result limits to control search precision and recall against document summaries."
      icon="tune"
      icon-color="teal-7"
    >
      <div class="column q-gap-16">
        <kg-field-row :cols="2">
          <div :class="{ 'col-span-2': localTool.searchMethod === 'vector' || localTool.searchMethod === 'full_text' }">
            <div class="km-input-label q-pb-sm">Method</div>
            <kg-dropdown-field v-model="localTool.searchMethod" :options="searchMethodOptions" option-description="description" dense />
          </div>
          <kg-field-row
            v-if="localTool.searchMethod === 'hybrid'"
            label="RRF k"
            hint="Reciprocal Rank Fusion constant used in the formula 1 / (k + rank). A higher value flattens rank differences, giving lower-ranked results more influence. A lower value amplifies the gap between top and bottom ranks. The default of 60 is the standard RRF constant and works well for most cases. Lower it (e.g. 10–30) to favor top-ranked results more aggressively; raise it (e.g. 80–150) when you want broader, more balanced fusion across search methods."
          >
            <km-input v-model.number="localTool.rrfK" type="number" :min="1" :max="200" />
          </kg-field-row>
        </kg-field-row>

        <kg-field-row :cols="2">
          <kg-field-row
            label="Score Threshold"
            hint="Minimum normalized relevance score (0–1) a document must reach to be included in the results. Documents scoring below this value are discarded. A higher threshold returns fewer but more relevant documents; a lower threshold increases recall at the risk of including noise. Typical values: 0.5–0.6 for broad searches, 0.7–0.8 for precise lookups. Set to 0 to disable filtering."
          >
            <q-slider v-model="localTool.scoreThreshold" :min="0" :max="1" :step="0.01" label color="primary" />
          </kg-field-row>
          <kg-field-row
            label="Result Limit"
            hint="Maximum number of documents returned to the agent after scoring and filtering. Matching documents are used to narrow the scope for subsequent chunk retrieval, so a smaller limit focuses the search while a larger limit gives broader coverage. Typical range: 3–5 for targeted lookups, 5–10 for exploratory searches."
          >
            <km-input v-model.number="localTool.limit" type="number" :min="1" :max="20" />
          </kg-field-row>
        </kg-field-row>
      </div>
    </kg-dialog-section>
  </kg-dialog-base>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { KgDialogBase, KgDialogSection, KgDropdownField, KgFieldRow, KgPromptSection } from '../../common'
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

watch(
  () => props.tool,
  (newVal) => {
    if (newVal) {
      localTool.value = JSON.parse(JSON.stringify(newVal))
    }
  },
  { immediate: true, deep: true }
)

const save = () => {
  emit('save', localTool.value)
  emit('update:modelValue', false)
}
</script>

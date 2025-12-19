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
      description="Tune tool settings to control the scope and precision of the search. Choose whether the agent can override the search method or must follow this configuration."
      icon="tune"
      icon-color="teal-7"
    >
      <template #header-actions>
        <kg-section-control v-model="localTool.searchControl" />
      </template>

      <div class="column q-gap-16" :class="{ 'section-fields-disabled': localTool.searchControl === 'agent' }">
        <kg-field-row :cols="2">
          <div :class="{ 'col-span-2': localTool.searchMethod !== 'hybrid' }">
            <div class="row items-center q-gutter-x-sm q-pb-sm">
              <div class="km-input-label">Method</div>
              <q-badge color="orange-1" text-color="orange-9" label="Coming Soon" class="text-weight-medium" />
            </div>
            <km-select v-model="localTool.searchMethod" :options="searchMethodOptions" emit-value map-options disable />
          </div>
          <div v-if="localTool.searchMethod === 'hybrid'">
            <div class="km-input-label q-pb-12">
              <span>Hybrid Score Distribution</span>
            </div>
            <div class="row items-center q-gutter-x-md">
              <span class="km-input-label text-primary text-weight-bold">Keyword {{ ((1 - localTool.hybridWeight) * 100).toFixed(0) }}%</span>
              <q-slider v-model="localTool.hybridWeight" :min="0" :max="1" :step="0.05" color="primary" class="col" />
              <span class="km-input-label text-primary text-weight-bold">{{ (localTool.hybridWeight * 100).toFixed(0) }}% Vector</span>
            </div>
          </div>
        </kg-field-row>

        <kg-field-row :cols="2">
          <div>
            <div class="km-input-label row justify-between q-pb-12">
              <span>Score Threshold</span>
              <span class="text-primary text-weight-bold">{{ localTool.scoreThreshold }}</span>
            </div>
            <q-slider v-model="localTool.scoreThreshold" :min="0" :max="1" :step="0.01" color="primary" />
          </div>
          <div>
            <div class="km-input-label q-pb-sm">Result Limit</div>
            <km-input v-model.number="localTool.limit" type="number" :min="1" :max="20" />
          </div>
        </kg-field-row>
      </div>
    </kg-dialog-section>
  </kg-dialog-base>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { KgDialogBase, KgDialogSection, KgFieldRow, KgPromptSection, KgSectionControl } from '../../common'
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

<style scoped>
.section-fields-disabled {
  opacity: 0.5;
  pointer-events: none;
  transition: opacity 0.2s ease;
}
</style>

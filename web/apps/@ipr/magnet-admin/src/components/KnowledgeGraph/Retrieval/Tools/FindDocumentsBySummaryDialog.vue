<template>
  <kg-dialog-base
    :model-value="modelValue"
    :title="localTool?.label"
    :confirm-label="m.common_apply()"
    size="md"
    @update:model-value="$emit('update:modelValue', $event)"
    @cancel="$emit('update:modelValue', false)"
    @confirm="save"
  >
    <!-- Tool Description -->
    <kg-prompt-section
      v-model="localTool.description"
      :title="m.retrieval_toolDescription()"
      :description="m.retrieval_toolDescriptionHint()"
    />

    <!-- Search Settings Section -->
    <kg-dialog-section
      :title="m.retrieval_searchSettings()"
      :description="m.retrieval_searchSettingsDesc()"
      icon="tune"
      tone="accent"
    >
      <template #header-actions>
        <kg-section-control v-model="localTool.searchControl" />
      </template>

      <div class="stack" data-gap="lg" :class="{ 'section-fields-disabled': localTool.searchControl === 'agent' }">
        <kg-field-row :cols="2">
          <div :class="{ 'col-span-2': localTool.searchMethod !== 'hybrid' }">
            <div class="cluster pb-sm gap-x-sm">
              <div class="km-input-label">{{ m.retrieval_method() }}</div>
              <km-badge tone="warning" :label="m.common_comingSoon()" class="text-weight-medium" />
            </div>
            <km-select v-model="localTool.searchMethod" :options="searchMethodOptions" emit-value map-options disable />
          </div>
          <div v-if="localTool.searchMethod === 'hybrid'">
            <div class="km-input-label pb-md">
              <span>{{ m.retrieval_hybridScoreDistribution() }}</span>
            </div>
            <div class="cluster gap-x-md">
              <span class="km-input-label text-primary text-weight-bold">{{ m.retrieval_keyword() }} {{ ((1 - localTool.hybridWeight) * 100).toFixed(0) }}%</span>
              <km-slider v-model="localTool.hybridWeight" :min="0" :max="1" :step="0.05" class="flex-1" />
              <span class="km-input-label text-primary text-weight-bold">{{ (localTool.hybridWeight * 100).toFixed(0) }}% {{ m.retrieval_vector() }}</span>
            </div>
          </div>
        </kg-field-row>

        <kg-field-row :cols="2">
          <div>
            <div class="km-input-label cluster pb-md" data-justify="between">
              <span>{{ m.retrieval_scoreThreshold() }}</span>
              <span class="text-primary text-weight-bold">{{ localTool.scoreThreshold }}</span>
            </div>
            <km-slider v-model="localTool.scoreThreshold" :min="0" :max="1" :step="0.01" />
          </div>
          <div>
            <div class="km-input-label pb-sm">{{ m.retrieval_resultLimit() }}</div>
            <km-input v-model.number="localTool.limit" type="number" :min="1" :max="20" />
          </div>
        </kg-field-row>
      </div>
    </kg-dialog-section>
  </kg-dialog-base>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { m } from '@/paraglide/messages'
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

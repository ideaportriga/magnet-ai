<template>
  <q-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)">
    <q-card class="q-pa-sm" style="min-width: 1000px; max-width: 1000px; height: 820px; display: flex; flex-direction: column">
      <q-card-section>
        <div class="row items-center">
          <div class="col row items-center no-wrap">
            <div class="km-heading-7">{{ tool?.label }}</div>
          </div>
          <q-btn icon="close" flat round dense color="grey-6" @click="$emit('update:modelValue', false)" />
        </div>
      </q-card-section>

      <q-card-section class="q-pa-md scrollable-content">
        <div class="column q-gap-16">
          <!-- Tool Description -->
          <DialogPromptSection
            v-model="localTool.description"
            title="Tool Description"
            description="Describe when the agent should call the exit tool to terminate the ReAct loop and deliver the final answer."
          />

          <!-- Exit Instructions -->
          <dialog-section
            title="Exit Instructions"
            description="Configure the strategy and iteration limits for the retrieval loop."
            icon="logout"
            color="deep-orange-7"
          >
            <div class="row q-col-gutter-md">
              <div v-for="strategy in strategyOptions" :key="strategy.value" class="col-12 col-md-4">
                <q-card
                  flat
                  bordered
                  class="strategy-card cursor-pointer full-height"
                  :class="{ 'strategy-card--selected': localTool.strategy === strategy.value }"
                  @click="localTool.strategy = strategy.value"
                >
                  <q-card-section class="q-pa-md">
                    <div class="row items-center q-gutter-x-sm q-mb-sm">
                      <q-icon :name="strategy.icon" :color="localTool.strategy === strategy.value ? 'primary' : ''" size="20px" />
                      <div class="text-weight-medium" :class="localTool.strategy === strategy.value ? 'primary' : ''">
                        {{ strategy.label }}
                      </div>
                    </div>
                    <div class="text-caption text-secondary-text">{{ strategy.description }}</div>
                  </q-card-section>
                </q-card>
              </div>
            </div>
            <div class="q-mt-32 q-mx-sm">
              <div class="km-input-label row justify-between q-pb-8">
                <span>Max Iterations</span>
                <span class="text-primary text-weight-bold">{{ localTool.maxIterations }}</span>
              </div>
              <q-slider v-model="localTool.maxIterations" :min="1" :max="15" :step="1" markers :marker-labels-class="'text-caption'" />
            </div>
          </dialog-section>

          <dialog-section
            title="Output Instructions"
            description="Define the structure and presentation of the final answer, including format and source attribution."
            icon="output"
            color="green-7"
          >
            <div class="column q-gap-16">
              <!-- Output Format, Answer Mode & Source Attribution - Horizontal -->
              <div class="row q-col-gutter-md">
                <div class="col-4">
                  <div class="km-input-label q-pb-sm">Output Format</div>
                  <km-select v-model="localTool.outputFormat" :options="outputFormatOptions" emit-value map-options />
                </div>
                <div class="col-4">
                  <div class="km-input-label q-pb-sm">Answer Mode</div>
                  <km-select v-model="localTool.answerMode" :options="answerModeOptions" emit-value map-options />
                </div>
                <div class="col-4">
                  <div class="q-pb-sm row items-center q-gutter-x-sm">
                    <span class="km-input-label text-grey-6">Source Attribution</span>
                    <q-badge color="orange-1" text-color="orange-9" label="Coming Soon" class="text-weight-medium" />
                  </div>
                  <km-select
                    :model-value="isAnswerOnly ? 'none' : localTool.sourceAttribution"
                    :options="sourceAttributionOptions"
                    :disable="isAnswerOnly || true"
                    emit-value
                    map-options
                  />
                </div>
              </div>

              <!-- Additional Output Instructions (Collapsible) -->
              <DialogPromptSection
                v-model="localTool.additionalOutputInstructions"
                v-model:expanded="additionalInstructionsExpanded"
                title="Additional Output Instructions"
                placeholder="Define additional guidelines or constraints for the response..."
                variant="field"
                collapse
              />
            </div>
          </dialog-section>
        </div>
      </q-card-section>

      <q-card-actions class="q-pa-md">
        <km-btn label="Cancel" flat color="primary" @click="$emit('update:modelValue', false)" />
        <q-space />
        <km-btn label="Apply" @click="save" />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import DialogSection from '../DialogSection.vue'
import DialogPromptSection from '../DialogPromptSection.vue'

// We define the interface locally or import it. For now, we can use `any` or match the Tool interface partially.
// Since this component is now generic-ish, we expect a `tool` prop.
// We can keep the ExitToolConfig interface for internal typing but the prop should be generic.

export interface ExitToolConfig {
  description: string
  outputInstructions: string
  additionalOutputInstructions: string
  strategy: 'confidence' | 'exhaustive' | 'efficient'
  maxIterations: number
  outputFormat: 'markdown' | 'plain'
  answerMode: 'answer_only' | 'sources_only' | 'answer_with_sources'
  sourceAttribution: 'none' | 'used' | 'all' | 'all_highlighted'
  enabled: boolean
  // It will also have other Tool properties but we only care about these for editing
}

const props = defineProps<{
  modelValue: boolean
  tool: any // Changed from config: ExitToolConfig
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'save', tool: any): void
}>()

const strategyOptions = [
  {
    value: 'confidence' as const,
    label: 'Confidence-based',
    icon: 'psychology',
    description: 'Exit when confident enough to answer, balancing thoroughness with efficiency.',
  },
  {
    value: 'exhaustive' as const,
    label: 'Exhaustive',
    icon: 'search',
    description: 'Explore all available tools before exiting, ensuring comprehensive coverage.',
  },
  {
    value: 'efficient' as const,
    label: 'Efficient',
    icon: 'bolt',
    description: 'Exit as soon as a satisfactory answer is found, prioritizing speed.',
  },
]

const outputFormatOptions = [
  { label: 'Markdown', value: 'markdown' },
  { label: 'Plain Text', value: 'plain' },
]

const answerModeOptions = [
  { label: 'Answer Only', value: 'answer_only' },
  { label: 'Sources Only', value: 'sources_only' },
  { label: 'Answer + Sources', value: 'answer_with_sources' },
]

const sourceAttributionOptions = [
  { label: 'None', value: 'none' },
  { label: 'Used sources only', value: 'used' },
  { label: 'All queried sources', value: 'all' },
  { label: 'All sources (highlight used)', value: 'all_highlighted' },
]

const isAnswerOnly = computed(() => localTool.value.answerMode === 'answer_only')

const additionalInstructionsExpanded = ref(false)

const localTool = ref<ExitToolConfig>({
  description: '',
  outputInstructions: '',
  additionalOutputInstructions: '',
  strategy: 'confidence',
  maxIterations: 5,
  outputFormat: 'markdown',
  answerMode: 'answer_with_sources',
  sourceAttribution: 'all',
  enabled: true,
})

watch(
  () => props.tool,
  (newVal) => {
    if (newVal) {
      // We copy the properties we care about, or just clone the whole object if it matches
      // Since newVal is the Tool object, it contains id, name, etc.
      // We'll just clone it and treat it as our local state.
      const toolData = JSON.parse(JSON.stringify(newVal))

      // Handle variable rename: outputGuidelines -> additionalOutputInstructions
      if (toolData.outputGuidelines && !toolData.additionalOutputInstructions) {
        toolData.additionalOutputInstructions = toolData.outputGuidelines
      }

      localTool.value = toolData

      // Ensure defaults for exit specific fields if missing (though they should be in the model)
      if (!localTool.value.outputInstructions) localTool.value.outputInstructions = ''
      if (!localTool.value.additionalOutputInstructions) localTool.value.additionalOutputInstructions = ''
      if (!localTool.value.strategy) localTool.value.strategy = 'confidence'
      if (!localTool.value.maxIterations) localTool.value.maxIterations = 5
      if (!localTool.value.outputFormat) localTool.value.outputFormat = 'markdown'
      if (!localTool.value.answerMode) localTool.value.answerMode = 'answer_with_sources'
      if (!localTool.value.sourceAttribution) localTool.value.sourceAttribution = 'all'

      additionalInstructionsExpanded.value = !localTool.value.additionalOutputInstructions
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
.scrollable-content {
  flex: 1 1 auto;
  overflow: auto;
  max-height: calc(90vh - 140px);
}

.strategy-card {
  transition: all 0.2s ease;
  border-color: #e0e0e0;
}

.strategy-card--selected,
.strategy-card:hover {
  color: var(--q-primary);
  border-color: var(--q-primary);
  background-color: color-mix(in srgb, var(--q-primary) 10%, white);
}
.strategy-card:hover :deep(.q-icon) {
  color: var(--q-primary);
}
</style>

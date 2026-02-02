<template>
  <kg-dialog-base
    :model-value="modelValue"
    :title="tool?.label"
    confirm-label="Apply"
    size="xl"
    scrollable
    max-height="820px"
    @update:model-value="$emit('update:modelValue', $event)"
    @cancel="$emit('update:modelValue', false)"
    @confirm="save"
  >
    <!-- Tool Description -->
    <kg-prompt-section
      v-model="localTool.description"
      title="Tool Description"
      description="Describe when the agent should call the exit tool to terminate the ReAct loop and deliver the final answer."
    />

    <!-- Exit Instructions -->
    <kg-dialog-section
      title="Exit Instructions"
      description="Configure the strategy and iteration limits for the retrieval loop."
      icon="logout"
      icon-color="deep-orange-7"
    >
      <kg-tile-select v-model="localTool.strategy" :options="strategyOptions" :cols="3" />
      <div class="q-mt-32 q-mx-sm">
        <div class="km-input-label row justify-between q-pb-8">
          <span>Max Iterations</span>
          <span class="text-primary text-weight-bold">{{ localTool.maxIterations }}</span>
        </div>
        <q-slider v-model="localTool.maxIterations" :min="1" :max="15" :step="1" markers :marker-labels-class="'text-caption'" />
      </div>
    </kg-dialog-section>

    <kg-dialog-section
      title="Output Instructions"
      description="Define the structure and presentation of the final answer, including format and source attribution."
      icon="output"
      icon-color="green-7"
    >
      <div class="column q-gap-16">
        <!-- Output Format, Answer Mode & Source Attribution - Horizontal -->
        <kg-field-row :cols="3">
          <div>
            <div class="km-input-label q-pb-sm">Output Format</div>
            <km-select v-model="localTool.outputFormat" :options="outputFormatOptions" emit-value map-options />
          </div>
          <div>
            <div class="km-input-label q-pb-sm">Answer Mode</div>
            <km-select v-model="localTool.answerMode" :options="answerModeOptions" emit-value map-options />
          </div>
          <div>
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
        </kg-field-row>

        <!-- Additional Output Instructions (Collapsible) -->
        <kg-prompt-section
          v-model="localTool.additionalOutputInstructions"
          v-model:expanded="additionalInstructionsExpanded"
          title="Additional Output Instructions"
          placeholder="Define additional guidelines or constraints for the response..."
          variant="field"
          collapse
        />
      </div>
    </kg-dialog-section>
  </kg-dialog-base>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { KgDialogBase, KgDialogSection, KgFieldRow, KgPromptSection, KgTileSelect, type TileOption } from '../../common'

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
}

const props = defineProps<{
  modelValue: boolean
  tool: any
}>()

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'save', tool: any): void
}>()

const strategyOptions: TileOption[] = [
  {
    value: 'confidence',
    label: 'Confidence-based',
    icon: 'psychology',
    description: 'Exit when confident enough to answer, balancing thoroughness with efficiency.',
  },
  {
    value: 'exhaustive',
    label: 'Exhaustive',
    icon: 'search',
    description: 'Explore all available tools before exiting, ensuring comprehensive coverage.',
  },
  {
    value: 'efficient',
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
      const toolData = JSON.parse(JSON.stringify(newVal))

      // Handle variable rename: outputGuidelines -> additionalOutputInstructions
      if (toolData.outputGuidelines && !toolData.additionalOutputInstructions) {
        toolData.additionalOutputInstructions = toolData.outputGuidelines
      }

      localTool.value = toolData

      // Ensure defaults for exit specific fields if missing
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

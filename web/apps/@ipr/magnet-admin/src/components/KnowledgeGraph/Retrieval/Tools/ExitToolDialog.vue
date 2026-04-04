<template>
  <kg-dialog-base
    :model-value="modelValue"
    :title="tool?.label"
    :confirm-label="m.common_apply()"
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
      :title="m.retrieval_toolDescription()"
      :description="m.retrieval_exitToolDescriptionHint()"
    />

    <!-- Exit Instructions -->
    <kg-dialog-section
      :title="m.retrieval_exitInstructions()"
      :description="m.retrieval_exitInstructionsDesc()"
      icon="logout"
      icon-color="deep-orange-7"
    >
      <kg-tile-select v-model="localTool.strategy" :options="strategyOptions" :cols="3" />
      <div class="q-mt-32 q-mx-sm">
        <div class="km-input-label row justify-between q-pb-8">
          <span>{{ m.retrieval_maxIterationsLabel() }}</span>
          <span class="text-primary text-weight-bold">{{ localTool.maxIterations }}</span>
        </div>
        <q-slider v-model="localTool.maxIterations" :min="1" :max="15" :step="1" markers :marker-labels-class="'text-caption'" />
      </div>
    </kg-dialog-section>

    <kg-dialog-section
      :title="m.retrieval_outputInstructions()"
      :description="m.retrieval_outputInstructionsDesc()"
      icon="output"
      icon-color="green-7"
    >
      <div class="column q-gap-16">
        <!-- Output Format, Answer Mode & Source Attribution - Horizontal -->
        <kg-field-row :cols="3">
          <div>
            <div class="km-input-label q-pb-sm">{{ m.retrieval_outputFormat() }}</div>
            <km-select v-model="localTool.outputFormat" :options="outputFormatOptions" emit-value map-options />
          </div>
          <div>
            <div class="km-input-label q-pb-sm">{{ m.retrieval_answerMode() }}</div>
            <km-select v-model="localTool.answerMode" :options="answerModeOptions" emit-value map-options />
          </div>
          <div>
            <div class="q-pb-sm row items-center q-gutter-x-sm">
              <span class="km-input-label text-grey-6">{{ m.retrieval_sourceAttribution() }}</span>
              <q-badge color="orange-1" text-color="orange-9" :label="m.common_comingSoon()" class="text-weight-medium" />
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
          :title="m.retrieval_additionalOutputInstructions()"
          :placeholder="m.retrieval_additionalOutputPlaceholder()"
          variant="field"
          collapse
        />
      </div>
    </kg-dialog-section>
  </kg-dialog-base>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { m } from '@/paraglide/messages'
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
    label: m.retrieval_confidenceBased(),
    icon: 'psychology',
    description: m.retrieval_confidenceBasedDesc(),
  },
  {
    value: 'exhaustive',
    label: m.retrieval_exhaustive(),
    icon: 'search',
    description: m.retrieval_exhaustiveDesc(),
  },
  {
    value: 'efficient',
    label: m.retrieval_efficient(),
    icon: 'bolt',
    description: m.retrieval_efficientDesc(),
  },
]

const outputFormatOptions = [
  { label: m.retrieval_outputMarkdown(), value: 'markdown' },
  { label: m.retrieval_outputPlainText(), value: 'plain' },
]

const answerModeOptions = [
  { label: m.retrieval_answerOnly(), value: 'answer_only' },
  { label: m.retrieval_sourcesOnly(), value: 'sources_only' },
  { label: m.retrieval_answerWithSources(), value: 'answer_with_sources' },
]

const sourceAttributionOptions = [
  { label: m.retrieval_sourceNone(), value: 'none' },
  { label: m.retrieval_sourceUsed(), value: 'used' },
  { label: m.retrieval_sourceAll(), value: 'all' },
  { label: m.retrieval_sourceAllHighlighted(), value: 'all_highlighted' },
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

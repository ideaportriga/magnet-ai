<template>
  <kg-dialog-base
    :model-value="props.showDialog"
    title="Smart Extraction Settings"
    subtitle="Configure how AI extracts metadata from your documents"
    confirm-label="Save Settings"
    :loading="loading"
    size="md"
    @update:model-value="emit('update:showDialog', $event)"
    @cancel="emit('cancel')"
    @confirm="onConfirm"
  >
    <div class="column q-gap-16">
      <!-- Extraction Settings -->
      <kg-dialog-section
        title="Extraction Settings"
        description="Configure extraction mode and the prompt used to generate JSON metadata."
        icon="auto_awesome"
      >
        <div class="column q-gap-16">
          <kg-field-row label="Extraction Mode" hint="Choose when AI should extract metadata.">
            <kg-tile-select v-model="approach" :options="approachOptions" :cols="2" />
          </kg-field-row>

          <kg-field-row label="Extraction Prompt" hint="Select a prompt template that returns JSON with metadata fields.">
            <kg-dropdown-field
              v-model="promptTemplateSystemName"
              placeholder="Select a prompt template"
              :options="promptTemplateOptions"
              :loading="loadingPromptTemplates"
              option-value="system_name"
              option-label="name"
              searchable
              clearable
            />
          </kg-field-row>
        </div>
      </kg-dialog-section>

      <!-- Segmentation Settings -->
      <kg-dialog-section
        title="Segmentation Settings"
        :description="
          approach === 'document'
            ? 'Split large documents into overlapping segments before extraction.'
            : 'Chunk-based extraction uses already segmented chunks (segmentation settings are ignored).'
        "
        icon="content_cut"
      >
        <template v-if="approach === 'document'">
          <div class="row q-col-gutter-lg">
            <div class="col-12 col-md-5">
              <kg-field-row label="Segment size (characters)">
                <km-input v-model.number="segmentSize" type="number" min="100" height="36px" />
              </kg-field-row>
            </div>
            <div class="col-12 col-md-7">
              <kg-field-row label="Segment overlap">
                <div class="row items-center q-gap-md">
                  <q-slider
                    v-model="segmentOverlap"
                    :min="0"
                    :max="0.9"
                    :step="0.02"
                    label
                    :label-value="`${Math.round((segmentOverlap || 0) * 100)}%`"
                    class="col"
                  />
                  <span class="overlap-value">{{ Math.round((segmentOverlap || 0) * 100) }}%</span>
                </div>
              </kg-field-row>
            </div>
          </div>
        </template>
        <template v-else>
          <kg-warning-banner variant="neutral">
            Segmentation is not needed for chunk-based extraction. Each chunk is already small enough to be processed directly by the AI.
          </kg-warning-banner>
        </template>
      </kg-dialog-section>
    </div>
  </kg-dialog-base>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { KgDialogBase, KgDialogSection, KgDropdownField, KgFieldRow, KgTileSelect, KgWarningBanner, type TileOption } from '../common'

export type MetadataExtractionApproach = 'chunks' | 'document'

export interface SmartExtractionSettings {
  approach: MetadataExtractionApproach
  prompt_template_system_name: string
  segment_size: number
  segment_overlap: number
}

const approachOptions: TileOption[] = [
  {
    label: 'Document Based',
    value: 'document',
    description: 'Extract metadata from the entire document in parallel to chunking. Recommended for most use cases.',
  },
  {
    label: 'Chunk Based',
    value: 'chunks',
    description: 'Extract metadata from each ingested chunk. Works slower, but metadata is linked with the chunk.',
  },
]

const props = defineProps<{
  showDialog: boolean
  settings?: SmartExtractionSettings | null
  promptTemplateOptions?: any[]
  loadingPromptTemplates?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:showDialog', value: boolean): void
  (e: 'cancel'): void
  (e: 'save', settings: SmartExtractionSettings): void
}>()

// Form state
const approach = ref<MetadataExtractionApproach>('document')
const promptTemplateSystemName = ref('')
const segmentSize = ref(18000)
const segmentOverlap = ref(0.1)
const loading = ref(false)

// Initialize form when dialog opens
watch(
  () => [props.showDialog, props.settings] as const,
  () => {
    if (props.showDialog && props.settings) {
      approach.value = props.settings.approach || 'document'
      promptTemplateSystemName.value = props.settings.prompt_template_system_name || ''
      segmentSize.value = props.settings.segment_size || 18000
      segmentOverlap.value = props.settings.segment_overlap ?? 0.1
    } else if (props.showDialog) {
      // Reset to defaults for new settings
      approach.value = 'document'
      promptTemplateSystemName.value = ''
      segmentSize.value = 18000
      segmentOverlap.value = 0.1
    }
  },
  { immediate: true }
)

const onConfirm = () => {
  const settings: SmartExtractionSettings = {
    approach: approach.value,
    prompt_template_system_name: promptTemplateSystemName.value.trim(),
    segment_size: segmentSize.value,
    segment_overlap: segmentOverlap.value,
  }
  emit('save', settings)
}
</script>

<style scoped>
/* Overlap value display */
.overlap-value {
  font-size: 13px;
  font-weight: 500;
  color: #4b5563;
  min-width: 40px;
  text-align: right;
}
</style>

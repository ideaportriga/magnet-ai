<template>
  <kg-dialog-base
    :model-value="props.showDialog"
    :title="m.knowledgeGraph_smartExtractionSettings()"
    :subtitle="m.knowledgeGraph_smartExtractionSettingsDesc()"
    :confirm-label="m.knowledgeGraph_saveSettings()"
    :loading="loading"
    size="md"
    @update:model-value="emit('update:showDialog', $event)"
    @cancel="emit('cancel')"
    @confirm="onConfirm"
  >
    <div class="column q-gap-16">
      <!-- Extraction Settings -->
      <kg-dialog-section
        :title="m.knowledgeGraph_extractionSettings()"
        :description="m.knowledgeGraph_extractionSettingsDesc()"
        icon="auto_awesome"
      >
        <div class="column q-gap-16">
          <kg-field-row :label="m.knowledgeGraph_extractionMode()" :hint="m.knowledgeGraph_extractionModeHint()">
            <kg-tile-select v-model="approach" :options="approachOptions" :cols="2" />
          </kg-field-row>

          <kg-field-row :label="m.knowledgeGraph_extractionPrompt()" :hint="m.knowledgeGraph_extractionPromptHint()">
            <kg-dropdown-field
              v-model="promptTemplateSystemName"
              :placeholder="m.knowledgeGraph_selectPromptTemplate()"
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
        :title="m.knowledgeGraph_segmentationSettings()"
        :description="
          approach === 'document'
            ? m.knowledgeGraph_segmentationDesc()
            : m.knowledgeGraph_chunkSegmentationDesc()
        "
        icon="content_cut"
      >
        <template v-if="approach === 'document'">
          <div class="row q-col-gutter-lg">
            <div class="col-12 col-md-5">
              <kg-field-row :label="m.knowledgeGraph_segmentSizeChars()">
                <km-input v-model.number="segmentSize" type="number" min="100" height="36px" />
              </kg-field-row>
            </div>
            <div class="col-12 col-md-7">
              <kg-field-row :label="m.knowledgeGraph_segmentOverlap()">
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
            {{ m.knowledgeGraph_chunkSegmentationNote() }}
          </kg-warning-banner>
        </template>
      </kg-dialog-section>
    </div>
  </kg-dialog-base>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { m } from '@/paraglide/messages'
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
    label: m.knowledgeGraph_documentBased(),
    value: 'document',
    description: m.knowledgeGraph_documentBasedDesc(),
  },
  {
    label: m.knowledgeGraph_chunkBased(),
    value: 'chunks',
    description: m.knowledgeGraph_chunkBasedDesc(),
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
  font-size: var(--km-font-size-label);
  font-weight: 500;
  color: var(--q-secondary-text);
  min-width: 40px;
  text-align: right;
}
</style>

<template>
  <kg-dialog-base
    :model-value="props.showDialog"
    :title="m.knowledgeGraph_entityExtractionSettings()"
    :subtitle="m.knowledgeGraph_entityExtractionSettingsSubtitle()"
    :confirm-label="m.knowledgeGraph_saveSettings()"
    :loading="loading"
    size="md"
    @update:model-value="emit('update:showDialog', $event)"
    @cancel="emit('cancel')"
    @confirm="onConfirm"
  >
    <div class="column q-gap-16">
      <kg-dialog-section
        :title="m.knowledgeGraph_extractionSettingsSection()"
        :description="m.knowledgeGraph_extractionSettingsSectionDesc()"
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

      <kg-dialog-section
        :title="m.knowledgeGraph_segmentationSettings()"
        :description="
          approach === 'document'
            ? m.knowledgeGraph_segmentationDocDesc()
            : m.knowledgeGraph_segmentationChunkDesc()
        "
        icon="content_cut"
      >
        <template v-if="approach === 'document'">
          <div class="row q-col-gutter-lg">
            <div class="col-12 col-md-5">
              <kg-field-row :label="m.knowledgeGraph_segmentSize()">
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
            {{ m.knowledgeGraph_chunkBasedSegmentationNote() }}
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
import {
  createDefaultEntityExtractionRunSettings,
  type EntityExtractionApproach,
  type EntityExtractionRunSettings,
} from './models'

const approachOptions: TileOption[] = [
  {
    label: m.knowledgeGraph_approachDocumentLabel(),
    value: 'document',
    description: m.knowledgeGraph_approachDocumentDesc(),
  },
  {
    label: m.knowledgeGraph_approachChunkLabel(),
    value: 'chunks',
    description: m.knowledgeGraph_approachChunkDesc(),
  },
]

const props = defineProps<{
  showDialog: boolean
  settings?: EntityExtractionRunSettings | null
  promptTemplateOptions?: any[]
  loadingPromptTemplates?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:showDialog', value: boolean): void
  (e: 'cancel'): void
  (e: 'save', settings: EntityExtractionRunSettings): void
}>()

const defaults = createDefaultEntityExtractionRunSettings()
const approach = ref<EntityExtractionApproach>(defaults.approach)
const promptTemplateSystemName = ref(defaults.prompt_template_system_name)
const segmentSize = ref(defaults.segment_size)
const segmentOverlap = ref(defaults.segment_overlap)
const loading = ref(false)

watch(
  () => [props.showDialog, props.settings] as const,
  () => {
    if (props.showDialog && props.settings) {
      approach.value = props.settings.approach || defaults.approach
      promptTemplateSystemName.value = props.settings.prompt_template_system_name || defaults.prompt_template_system_name
      segmentSize.value = props.settings.segment_size || defaults.segment_size
      segmentOverlap.value = props.settings.segment_overlap ?? defaults.segment_overlap
    } else if (props.showDialog) {
      approach.value = defaults.approach
      promptTemplateSystemName.value = defaults.prompt_template_system_name
      segmentSize.value = defaults.segment_size
      segmentOverlap.value = defaults.segment_overlap
    }
  },
  { immediate: true }
)

function onConfirm() {
  emit('save', {
    approach: approach.value,
    prompt_template_system_name: promptTemplateSystemName.value.trim(),
    segment_size: segmentSize.value,
    segment_overlap: segmentOverlap.value,
  })
}
</script>

<style scoped>
.overlap-value {
  font-size: var(--km-font-size-label);
  font-weight: 500;
  color: var(--q-label);
  min-width: 40px;
  text-align: right;
}
</style>

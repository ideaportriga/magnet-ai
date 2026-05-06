<template>
  <kg-dialog-base
    :model-value="props.showDialog"
    title="Entity Extraction Settings"
    subtitle="Configure how AI extracts structured entities from your documents"
    confirm-label="Save Settings"
    :loading="loading"
    size="md"
    @update:model-value="emit('update:showDialog', $event)"
    @cancel="emit('cancel')"
    @confirm="onConfirm"
  >
    <div class="column q-gap-16">
      <kg-dialog-section
        title="Extraction Settings"
        description="Choose when entity extraction runs and which prompt template should produce the structured entity output."
        icon="auto_awesome"
      >
        <div class="column q-gap-16">
          <kg-field-row
            label="Extraction Approach"
            hint="Choose whether entities are extracted from full documents or from already-generated chunks."
          >
            <kg-tile-select v-model="approach" :options="approachOptions" :cols="2" />
          </kg-field-row>

          <kg-field-row label="Extraction Mode">
            <kg-dropdown-field v-model="mode" :options="modeOptions" option-value="value" option-label="label" option-description="description" />
          </kg-field-row>

          <div v-if="mode === 'advanced'" class="row q-col-gutter-md">
            <div class="col">
              <kg-field-row label="Analysis Prompt" hint="Prompt that builds the running global analysis used by the extraction pass.">
                <kg-dropdown-field
                  v-model="analysisPromptTemplateSystemName"
                  placeholder="Select an analysis prompt template"
                  :options="promptTemplateOptions"
                  :loading="loadingPromptTemplates"
                  option-value="system_name"
                  option-label="name"
                  searchable
                  clearable
                />
              </kg-field-row>
            </div>
            <div class="col">
              <kg-field-row label="Extraction Prompt" hint="Select a prompt template that returns structured entity records.">
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
          </div>
          <div v-else>
            <kg-field-row label="Extraction Prompt" hint="Select a prompt template that returns structured entity records.">
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

          <kg-field-row label="Schema Format">
            <kg-dropdown-field
              v-model="schemaFormat"
              :options="schemaFormatOptions"
              option-value="value"
              option-label="label"
              option-description="description"
            />
          </kg-field-row>

          <kg-field-row
            label="Max Extraction Iterations"
            hint="Number of extraction passes per segment (1 = single pass, 3 = initial pass + 2 verification passes)."
          >
            <km-input
              v-model.number="maxExtractionIterations"
              type="number"
              :min="MIN_ENTITY_EXTRACTION_MAX_ITERATIONS"
              :max="MAX_ENTITY_EXTRACTION_MAX_ITERATIONS"
              height="36px"
            />
          </kg-field-row>
        </div>
      </kg-dialog-section>

      <kg-dialog-section
        title="Segmentation Settings"
        :description="
          approach === 'document'
            ? 'Split large documents into overlapping segments before extraction.'
            : 'Chunk-based extraction uses the existing chunks, so segmentation settings are ignored.'
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
            Chunk-based extraction reuses the graph's chunks directly, so document segmentation is not applied here.
          </kg-warning-banner>
        </template>
      </kg-dialog-section>
    </div>
  </kg-dialog-base>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { KgDialogBase, KgDialogSection, KgDropdownField, KgFieldRow, KgTileSelect, KgWarningBanner, type TileOption } from '../common'
import {
  createDefaultEntityExtractionRunSettings,
  MAX_ENTITY_EXTRACTION_MAX_ITERATIONS,
  MIN_ENTITY_EXTRACTION_MAX_ITERATIONS,
  type EntityExtractionApproach,
  type EntityExtractionMode,
  type EntityExtractionRunSettings,
  type EntityExtractionSchemaFormat,
} from './models'

const approachOptions: TileOption[] = [
  {
    label: 'Document Based',
    value: 'document',
    description: 'Extract entities from full documents with automatic segmentation for large inputs. Recommended for most graphs.',
  },
  {
    label: 'Chunk Based',
    value: 'chunks',
    description: 'Extract entities from each existing chunk. Useful when chunk-level provenance matters most.',
  },
]

const modeOptions = [
  { label: 'Basic', value: 'basic', description: 'Single extraction pass per segment with verification iterations. Fast and predictable.' },
  {
    label: 'Advanced',
    value: 'advanced',
    description:
      'Pre-analyses the document for cross-segment context, then extracts with that analysis as input. Better recall for global attributes; uses more tokens.',
  },
]

const schemaFormatOptions = [
  { label: 'JSON Schema', value: 'json_schema', description: 'Send a strict JSON Schema as the structured-output format on the request.' },
  { label: 'TypeScript', value: 'typescript', description: 'Describe entities using a TypeScript class-style block embedded in the prompt.' },
  { label: 'Markdown', value: 'markdown', description: 'Describe entities using a simple markdown listing embedded in the prompt.' },
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
const mode = ref<EntityExtractionMode>(defaults.mode)
const schemaFormat = ref<EntityExtractionSchemaFormat>(defaults.schema_format)
const promptTemplateSystemName = ref(defaults.prompt_template_system_name)
const analysisPromptTemplateSystemName = ref(defaults.analysis_prompt_template_system_name)
const segmentSize = ref(defaults.segment_size)
const segmentOverlap = ref(defaults.segment_overlap)
const maxExtractionIterations = ref(defaults.max_extraction_iterations)
const loading = ref(false)

watch(
  () => [props.showDialog, props.settings] as const,
  () => {
    if (props.showDialog && props.settings) {
      approach.value = props.settings.approach || defaults.approach
      mode.value = props.settings.mode || defaults.mode
      schemaFormat.value = props.settings.schema_format || defaults.schema_format
      promptTemplateSystemName.value = props.settings.prompt_template_system_name || defaults.prompt_template_system_name
      analysisPromptTemplateSystemName.value = props.settings.analysis_prompt_template_system_name || defaults.analysis_prompt_template_system_name
      segmentSize.value = props.settings.segment_size || defaults.segment_size
      segmentOverlap.value = props.settings.segment_overlap ?? defaults.segment_overlap
      maxExtractionIterations.value = props.settings.max_extraction_iterations ?? defaults.max_extraction_iterations
    } else if (props.showDialog) {
      approach.value = defaults.approach
      mode.value = defaults.mode
      schemaFormat.value = defaults.schema_format
      promptTemplateSystemName.value = defaults.prompt_template_system_name
      analysisPromptTemplateSystemName.value = defaults.analysis_prompt_template_system_name
      segmentSize.value = defaults.segment_size
      segmentOverlap.value = defaults.segment_overlap
      maxExtractionIterations.value = defaults.max_extraction_iterations
    }
  },
  { immediate: true }
)

function onConfirm() {
  emit('save', {
    approach: approach.value,
    mode: mode.value,
    schema_format: schemaFormat.value,
    prompt_template_system_name: promptTemplateSystemName.value.trim(),
    analysis_prompt_template_system_name: analysisPromptTemplateSystemName.value.trim(),
    segment_size: segmentSize.value,
    segment_overlap: segmentOverlap.value,
    max_extraction_iterations: maxExtractionIterations.value,
  })
}
</script>

<style scoped>
.overlap-value {
  font-size: 13px;
  font-weight: 500;
  color: #4b5563;
  min-width: 40px;
  text-align: right;
}
</style>

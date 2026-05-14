<template>
  <kg-dialog-base
    :model-value="props.showDialog"
    title="Entity Extraction Settings"
    subtitle="Control how the AI identifies and pulls structured entities from documents"
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
        description="Define how entity extraction runs and which prompt templates drive the structured output."
        icon="auto_awesome"
      >
        <template #header-actions>
          <kg-section-control v-model="approach" :options="approachControlOptions" />
        </template>
        <div class="column q-gap-16">
          <kg-field-row
            label="Extraction Strategy"
            hint="Determines how many reasoning steps the model uses per segment. Single-Pass is the fastest option."
          >
            <kg-dropdown-field
              v-model="mode"
              :options="modeOptions"
              option-value="value"
              option-label="label"
              option-description="description"
              dense
            />
          </kg-field-row>

          <div v-if="mode === 'reflective'">
            <kg-field-row label="Extraction Prompt">
              <kg-dropdown-field
                v-model="reflectivePromptTemplateSystemName"
                placeholder="Select a reflective prompt template"
                :options="promptTemplateOptions"
                :loading="loadingPromptTemplates"
                option-value="system_name"
                option-label="name"
                searchable
                clearable
                dense
              />
            </kg-field-row>
          </div>
          <div v-else-if="mode === 'self-tuning'" class="row q-col-gutter-md">
            <div class="col">
              <kg-field-row
                label="Analysis Prompt"
                hint="Emits per-segment delta operations (Add/Replace/Remove) on the running instructions, shared values, and example bank — or a 'no-change' marker when the segment teaches nothing new."
              >
                <kg-dropdown-field
                  v-model="selfTuningAnalysisPromptTemplateSystemName"
                  placeholder="Select a self-tuning analysis prompt template"
                  :options="promptTemplateOptions"
                  :loading="loadingPromptTemplates"
                  option-value="system_name"
                  option-label="name"
                  searchable
                  clearable
                  dense
                />
              </kg-field-row>
            </div>
            <div class="col">
              <kg-field-row
                label="Extraction Prompt"
                hint="Must reference {TUNED_INSTRUCTIONS}, {SHARED_VALUES}, and {EXAMPLES} so the accumulated self-tuning state can be injected into the prompt body."
              >
                <kg-dropdown-field
                  v-model="selfTuningPromptTemplateSystemName"
                  placeholder="Select a self-tuning extraction prompt template"
                  :options="promptTemplateOptions"
                  :loading="loadingPromptTemplates"
                  option-value="system_name"
                  option-label="name"
                  searchable
                  clearable
                  dense
                />
              </kg-field-row>
            </div>
          </div>
          <div v-else>
            <kg-field-row label="Extraction Prompt">
              <kg-dropdown-field
                v-model="promptTemplateSystemName"
                placeholder="Select a prompt template"
                :options="promptTemplateOptions"
                :loading="loadingPromptTemplates"
                option-value="system_name"
                option-label="name"
                searchable
                clearable
                dense
              />
            </kg-field-row>
          </div>
        </div>
      </kg-dialog-section>

      <kg-dialog-section
        v-if="approach === 'document'"
        title="Segmentation Settings"
        description="Control how documents are split into overlapping segments before extraction runs."
        icon="content_cut"
      >
        <div class="row q-col-gutter-lg">
          <div class="col-12 col-md-5">
            <kg-field-row label="Segment Size (Characters)">
              <km-input v-model.number="segmentSize" type="number" min="100" height="36px" />
            </kg-field-row>
          </div>
          <div class="col-12 col-md-7">
            <kg-field-row label="Segment Overlap">
              <div class="row items-center q-gap-md">
                <q-slider
                  v-model="segmentOverlap"
                  :min="0"
                  :max="0.9"
                  :step="0.02"
                  label
                  :label-value="`${Math.round((segmentOverlap || 0) * 100)}%`"
                  class="col q-mt-4"
                />
                <span class="overlap-value">{{ Math.round((segmentOverlap || 0) * 100) }}%</span>
              </div>
            </kg-field-row>
          </div>
        </div>
      </kg-dialog-section>

      <kg-dialog-section
        title="Advanced Settings"
        description="Control schema format, iteration count, relevance filtering, and analysis coverage to balance extraction quality, cost, and speed."
        icon="tune"
      >
        <div class="column q-gap-16">
          <div class="row q-col-gutter-md">
            <div class="col">
              <kg-field-row
                label="Schema Format"
                hint="How entity types are communicated to the model. JSON Schema is the most precise; TypeScript and Markdown trade strictness for brevity."
              >
                <kg-dropdown-field
                  v-model="schemaFormat"
                  :options="schemaFormatOptions"
                  option-value="value"
                  option-label="label"
                  option-description="description"
                  dense
                />
              </kg-field-row>
            </div>
            <div class="col">
              <kg-field-row
                label="Max Extraction Iterations"
                hint="How many passes the model runs on each segment. The first pass extracts entities; additional passes refine and verify them."
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
          </div>

          <kg-field-row
            label="Relevance Filter Prompt"
            hint="When set, runs a small LLM check on each chunk to drop boilerplate before extraction. Clear to disable the filter."
          >
            <kg-dropdown-field
              v-model="relevanceFilterPromptTemplateSystemName"
              placeholder="Select a prompt template to enable the filter"
              :options="promptTemplateOptions"
              :loading="loadingPromptTemplates"
              option-value="system_name"
              option-label="name"
              searchable
              clearable
              dense
            />
          </kg-field-row>

          <kg-field-row
            label="Coverage Mode"
            hint="Which section of the document's chunks the analysis pass should learn from. Set to Full to process whole document."
          >
            <kg-dropdown-field v-model="documentCoverageMode" :options="coverageModeOptions" option-value="value" option-label="label" dense />
          </kg-field-row>

          <div v-if="documentCoverageMode !== 'full'" class="row q-col-gutter-md">
            <div class="col-12 col-md-6">
              <kg-field-row label="Coverage">
                <div class="row items-center q-gap-md q-pl-4">
                  <q-slider
                    v-model="documentCoverage"
                    :min="MIN_DOCUMENT_COVERAGE"
                    :max="MAX_DOCUMENT_COVERAGE"
                    :step="0.02"
                    label
                    :label-value="`${Math.round(documentCoverage * 100)}%`"
                    class="col q-mt-4"
                  />
                  <span class="coverage-value">{{ Math.round(documentCoverage * 100) }}%</span>
                </div>
              </kg-field-row>
            </div>
            <div class="col-12 col-md-6">
              <kg-field-row label="Coverage Preview">
                <div class="column q-gap-4 full-width">
                  <div class="coverage-preview">
                    <div class="coverage-preview__bar">
                      <div
                        v-for="(seg, i) in coverageBarSegments"
                        :key="i"
                        :class="[
                          'coverage-preview__segment',
                          seg.analyzed ? 'coverage-preview__segment--analyzed' : 'coverage-preview__segment--skipped',
                        ]"
                        :style="{ flex: seg.width }"
                      />
                    </div>
                  </div>
                </div>
              </kg-field-row>
            </div>
          </div>
        </div>
      </kg-dialog-section>
    </div>
  </kg-dialog-base>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { KgDialogBase, KgDialogSection, KgDropdownField, KgFieldRow, KgSectionControl, type ControlOption } from '../common'
import {
  createDefaultEntityExtractionRunSettings,
  createDefaultPerformanceTuningSettings,
  DEFAULT_DOCUMENT_COVERAGE,
  DEFAULT_DOCUMENT_COVERAGE_MODE,
  MAX_DOCUMENT_COVERAGE,
  MAX_ENTITY_EXTRACTION_MAX_ITERATIONS,
  MIN_DOCUMENT_COVERAGE,
  MIN_ENTITY_EXTRACTION_MAX_ITERATIONS,
  type DocumentCoverageMode,
  type EntityExtractionApproach,
  type EntityExtractionMode,
  type EntityExtractionPerformanceTuningSettings,
  type EntityExtractionRunSettings,
  type EntityExtractionSchemaFormat,
} from './models'

export interface EntityExtractionDialogPayload {
  extraction: EntityExtractionRunSettings
  advanced_settings: EntityExtractionPerformanceTuningSettings
}

const approachControlOptions: ControlOption[] = [
  {
    label: 'Document Based',
    value: 'document',
    hint: 'Process full documents and split them into overlapping segments automatically. Recommended for most graphs.',
  },
  {
    label: 'Chunk Based',
    value: 'chunks',
    hint: 'Process each existing chunk on its own. Use when chunk-level provenance is the priority.',
  },
]

const modeOptions = [
  {
    label: 'Basic (Single-Pass)',
    value: 'basic',
    description: 'Extracts entities directly from each segment in one prompt. Fast, predictable, and economical on tokens.',
  },
  {
    label: 'Reflective (Single-Pass)',
    value: 'reflective',
    description: "Each segment's call returns reasoning and records together; the reasoning carries forward to the next segment.",
  },
  {
    label: 'Self-Tuning (Double-Pass)',
    value: 'self-tuning',
    description:
      'A pre-analysis pass tailors the extraction prompt segment by segment - accumulating document-specific instructions, shared values, and few-shot examples.',
  },
]

const schemaFormatOptions = [
  {
    label: 'JSON Schema',
    value: 'json_schema',
    description: 'Enforces output via a strict JSON Schema attached to the model request.',
  },
  {
    label: 'TypeScript',
    value: 'typescript',
    description: 'Describes entities as a TypeScript class-style definition embedded in the prompt.',
  },
  {
    label: 'Markdown',
    value: 'markdown',
    description: 'Describes entities as a lightweight markdown outline embedded in the prompt.',
  },
]

const coverageModeOptions = [
  {
    value: 'full',
    label: 'Full',
    description: 'Analysis pass covers all chunks. Coverage slider is ignored.',
  },
  {
    value: 'beginning',
    label: 'Beginning',
    description: 'Tunes the prompt using the first N% of chunks. Best for reports or papers where key entity patterns are introduced upfront.',
  },
  {
    value: 'middle',
    label: 'Middle',
    description: 'Tunes the prompt using the central N% of chunks. Useful when key content is in the body and headers/footers carry less signal.',
  },
  {
    value: 'end',
    label: 'End',
    description: 'Tunes the prompt using the last N% of chunks. Useful when conclusions and entity summaries appear at the end.',
  },
  {
    value: 'outer',
    label: 'Outer Sections',
    description: 'Tunes the prompt using the first and last N/2% of chunks equally. Effective when introductions and conclusions both carry signal.',
  },
]

const props = defineProps<{
  showDialog: boolean
  settings?: EntityExtractionRunSettings | null
  performanceTuning?: EntityExtractionPerformanceTuningSettings | null
  promptTemplateOptions?: any[]
  loadingPromptTemplates?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:showDialog', value: boolean): void
  (e: 'cancel'): void
  (e: 'save', payload: EntityExtractionDialogPayload): void
}>()

const defaults = createDefaultEntityExtractionRunSettings()
const tuningDefaults = createDefaultPerformanceTuningSettings()
const approach = ref<EntityExtractionApproach>(defaults.approach)
const mode = ref<EntityExtractionMode>(defaults.mode)
const schemaFormat = ref<EntityExtractionSchemaFormat>(tuningDefaults.schema_format)
const promptTemplateSystemName = ref(defaults.prompt_template_system_name)
const reflectivePromptTemplateSystemName = ref(defaults.reflective_prompt_template_system_name)
const selfTuningPromptTemplateSystemName = ref(defaults.self_tuning_prompt_template_system_name)
const selfTuningAnalysisPromptTemplateSystemName = ref(defaults.self_tuning_analysis_prompt_template_system_name)
const segmentSize = ref(defaults.segment_size)
const segmentOverlap = ref(defaults.segment_overlap)
const maxExtractionIterations = ref(tuningDefaults.max_extraction_iterations)
const relevanceFilterPromptTemplateSystemName = ref(tuningDefaults.relevance_filter.prompt_template_system_name)
const documentCoverageMode = ref<DocumentCoverageMode>(DEFAULT_DOCUMENT_COVERAGE_MODE)
const documentCoverage = ref(DEFAULT_DOCUMENT_COVERAGE)
const loading = ref(false)

const coverageBarSegments = computed(() => {
  const mode = documentCoverageMode.value
  const cov = documentCoverage.value
  const total = 100
  const count = Math.round(total * cov)

  if (mode === 'full') {
    return [{ analyzed: true, width: total }]
  }
  if (mode === 'beginning') {
    return [
      { analyzed: true, width: count },
      { analyzed: false, width: total - count },
    ]
  }
  if (mode === 'middle') {
    const start = Math.floor((total - count) / 2)
    return [
      { analyzed: false, width: start },
      { analyzed: true, width: count },
      { analyzed: false, width: total - start - count },
    ]
  }
  if (mode === 'end') {
    return [
      { analyzed: false, width: total - count },
      { analyzed: true, width: count },
    ]
  }
  if (mode === 'outer') {
    const half = Math.floor(count / 2)
    const other = count - half
    return [
      { analyzed: true, width: half },
      { analyzed: false, width: total - count },
      { analyzed: true, width: other },
    ]
  }
  return [{ analyzed: true, width: total }]
})

watch(
  () => [props.showDialog, props.settings, props.performanceTuning] as const,
  () => {
    if (props.showDialog && props.settings) {
      approach.value = props.settings.approach || defaults.approach
      mode.value = props.settings.mode || defaults.mode
      promptTemplateSystemName.value = props.settings.prompt_template_system_name || defaults.prompt_template_system_name
      reflectivePromptTemplateSystemName.value =
        props.settings.reflective_prompt_template_system_name || defaults.reflective_prompt_template_system_name
      selfTuningPromptTemplateSystemName.value =
        props.settings.self_tuning_prompt_template_system_name || defaults.self_tuning_prompt_template_system_name
      selfTuningAnalysisPromptTemplateSystemName.value =
        props.settings.self_tuning_analysis_prompt_template_system_name || defaults.self_tuning_analysis_prompt_template_system_name
      segmentSize.value = props.settings.segment_size || defaults.segment_size
      segmentOverlap.value = props.settings.segment_overlap ?? defaults.segment_overlap
    } else if (props.showDialog) {
      approach.value = defaults.approach
      mode.value = defaults.mode
      promptTemplateSystemName.value = defaults.prompt_template_system_name
      reflectivePromptTemplateSystemName.value = defaults.reflective_prompt_template_system_name
      selfTuningPromptTemplateSystemName.value = defaults.self_tuning_prompt_template_system_name
      selfTuningAnalysisPromptTemplateSystemName.value = defaults.self_tuning_analysis_prompt_template_system_name
      segmentSize.value = defaults.segment_size
      segmentOverlap.value = defaults.segment_overlap
    }

    if (props.showDialog) {
      const tuning = props.performanceTuning
      schemaFormat.value = tuning?.schema_format ?? tuningDefaults.schema_format
      maxExtractionIterations.value = tuning?.max_extraction_iterations ?? tuningDefaults.max_extraction_iterations
      relevanceFilterPromptTemplateSystemName.value = tuning?.relevance_filter?.prompt_template_system_name ?? ''
      documentCoverageMode.value = (tuning?.document_coverage?.mode ?? DEFAULT_DOCUMENT_COVERAGE_MODE) as DocumentCoverageMode
      documentCoverage.value = tuning?.document_coverage?.coverage ?? DEFAULT_DOCUMENT_COVERAGE
    }
  },
  { immediate: true }
)

function onConfirm() {
  emit('save', {
    extraction: {
      approach: approach.value,
      mode: mode.value,
      prompt_template_system_name: promptTemplateSystemName.value.trim(),
      reflective_prompt_template_system_name: reflectivePromptTemplateSystemName.value.trim(),
      self_tuning_prompt_template_system_name: selfTuningPromptTemplateSystemName.value.trim(),
      self_tuning_analysis_prompt_template_system_name: selfTuningAnalysisPromptTemplateSystemName.value.trim(),
      segment_size: segmentSize.value,
      segment_overlap: segmentOverlap.value,
    },
    advanced_settings: {
      schema_format: schemaFormat.value,
      max_extraction_iterations: maxExtractionIterations.value,
      relevance_filter: {
        prompt_template_system_name: relevanceFilterPromptTemplateSystemName.value.trim(),
      },
      document_coverage: {
        mode: documentCoverageMode.value,
        coverage: documentCoverage.value,
      },
    },
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

.coverage-value {
  font-size: 13px;
  font-weight: 500;
  color: #4b5563;
  min-width: 40px;
  text-align: right;
}

.coverage-preview {
  display: flex;
  align-items: center;
  margin-top: 8px;
  padding-left: 4px;
}

.coverage-preview__bar {
  display: flex;
  flex: 1;
  height: 18px;
  border-radius: 3px;
  overflow: hidden;
  gap: 1px;
  background: #e5e7eb;
}

.coverage-preview__segment {
  transition: flex 0.25s ease;
}

.coverage-preview__segment--analyzed {
  background: var(--q-primary);
}

.coverage-preview__segment--skipped {
  background: transparent;
}
</style>

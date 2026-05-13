<template>
  <kg-dialog-base
    :model-value="props.showDialog"
    title="Extraction Settings"
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
            hint="Determines how many reasoning steps the model uses per segment. Single-Pass is faster; Context-Aware improves accuracy on complex documents."
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

          <div v-if="mode === 'advanced'" class="row q-col-gutter-md">
            <div class="col">
              <kg-field-row
                label="Context Analysis Prompt"
                hint="Builds a document-wide summary that gives the extraction pass cross-segment context."
              >
                <kg-dropdown-field
                  v-model="analysisPromptTemplateSystemName"
                  placeholder="Select a context analysis prompt template"
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
          <div v-else-if="mode === 'reflective'">
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
                label="Self-Tuning Analysis Prompt"
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
        title="Performance Optimizations"
        description="Optimize cost and speed by skipping irrelevant content. May slightly reduce extraction quality on edge cases."
        icon="tune"
      >
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
      </kg-dialog-section>
    </div>
  </kg-dialog-base>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { KgDialogBase, KgDialogSection, KgDropdownField, KgFieldRow, KgSectionControl, type ControlOption } from '../common'
import {
  createDefaultEntityExtractionRunSettings,
  createDefaultPerformanceOptimizationsSettings,
  MAX_ENTITY_EXTRACTION_MAX_ITERATIONS,
  MIN_ENTITY_EXTRACTION_MAX_ITERATIONS,
  type EntityExtractionApproach,
  type EntityExtractionMode,
  type EntityExtractionPerformanceOptimizationsSettings,
  type EntityExtractionRunSettings,
  type EntityExtractionSchemaFormat,
} from './models'

export interface EntityExtractionDialogPayload {
  extraction: EntityExtractionRunSettings
  performance_optimizations: EntityExtractionPerformanceOptimizationsSettings
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
    label: 'Single-Pass',
    value: 'basic',
    description: 'Extracts entities directly from each segment in one prompt. Fast, predictable, and economical on tokens.',
  },
  {
    label: 'Reflective',
    value: 'reflective',
    description:
      "Each segment's call returns reasoning and records together; the reasoning carries forward to the next segment. A middle ground between Single-Pass and Context-Aware.",
  },
  {
    label: 'Context-Aware',
    value: 'advanced',
    description:
      'First builds a document-wide analysis, then feeds it into the extraction pass. Improves recall on cross-segment attributes at the cost of additional tokens.',
  },
  {
    label: 'Self-Tuning',
    value: 'self-tuning',
    description:
      'A pre-analysis pass tailors the extraction prompt itself segment by segment — accumulating document-specific instructions, shared values, and few-shot examples. Each analysis call emits only deltas (or a no-change marker) to keep token cost low.',
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

const props = defineProps<{
  showDialog: boolean
  settings?: EntityExtractionRunSettings | null
  performanceOptimizations?: EntityExtractionPerformanceOptimizationsSettings | null
  promptTemplateOptions?: any[]
  loadingPromptTemplates?: boolean
}>()

const emit = defineEmits<{
  (e: 'update:showDialog', value: boolean): void
  (e: 'cancel'): void
  (e: 'save', payload: EntityExtractionDialogPayload): void
}>()

const defaults = createDefaultEntityExtractionRunSettings()
const performanceDefaults = createDefaultPerformanceOptimizationsSettings()
const approach = ref<EntityExtractionApproach>(defaults.approach)
const mode = ref<EntityExtractionMode>(defaults.mode)
const schemaFormat = ref<EntityExtractionSchemaFormat>(defaults.schema_format)
const promptTemplateSystemName = ref(defaults.prompt_template_system_name)
const analysisPromptTemplateSystemName = ref(defaults.analysis_prompt_template_system_name)
const reflectivePromptTemplateSystemName = ref(defaults.reflective_prompt_template_system_name)
const selfTuningPromptTemplateSystemName = ref(defaults.self_tuning_prompt_template_system_name)
const selfTuningAnalysisPromptTemplateSystemName = ref(defaults.self_tuning_analysis_prompt_template_system_name)
const segmentSize = ref(defaults.segment_size)
const segmentOverlap = ref(defaults.segment_overlap)
const maxExtractionIterations = ref(defaults.max_extraction_iterations)
const relevanceFilterPromptTemplateSystemName = ref(
  performanceDefaults.relevance_filter.prompt_template_system_name
)
const loading = ref(false)

watch(
  () => [props.showDialog, props.settings, props.performanceOptimizations] as const,
  () => {
    if (props.showDialog && props.settings) {
      approach.value = props.settings.approach || defaults.approach
      mode.value = props.settings.mode || defaults.mode
      schemaFormat.value = props.settings.schema_format || defaults.schema_format
      promptTemplateSystemName.value = props.settings.prompt_template_system_name || defaults.prompt_template_system_name
      analysisPromptTemplateSystemName.value = props.settings.analysis_prompt_template_system_name || defaults.analysis_prompt_template_system_name
      reflectivePromptTemplateSystemName.value =
        props.settings.reflective_prompt_template_system_name || defaults.reflective_prompt_template_system_name
      selfTuningPromptTemplateSystemName.value =
        props.settings.self_tuning_prompt_template_system_name || defaults.self_tuning_prompt_template_system_name
      selfTuningAnalysisPromptTemplateSystemName.value =
        props.settings.self_tuning_analysis_prompt_template_system_name ||
        defaults.self_tuning_analysis_prompt_template_system_name
      segmentSize.value = props.settings.segment_size || defaults.segment_size
      segmentOverlap.value = props.settings.segment_overlap ?? defaults.segment_overlap
      maxExtractionIterations.value = props.settings.max_extraction_iterations ?? defaults.max_extraction_iterations
    } else if (props.showDialog) {
      approach.value = defaults.approach
      mode.value = defaults.mode
      schemaFormat.value = defaults.schema_format
      promptTemplateSystemName.value = defaults.prompt_template_system_name
      analysisPromptTemplateSystemName.value = defaults.analysis_prompt_template_system_name
      reflectivePromptTemplateSystemName.value = defaults.reflective_prompt_template_system_name
      selfTuningPromptTemplateSystemName.value = defaults.self_tuning_prompt_template_system_name
      selfTuningAnalysisPromptTemplateSystemName.value = defaults.self_tuning_analysis_prompt_template_system_name
      segmentSize.value = defaults.segment_size
      segmentOverlap.value = defaults.segment_overlap
      maxExtractionIterations.value = defaults.max_extraction_iterations
    }

    if (props.showDialog) {
      const perf = props.performanceOptimizations
      relevanceFilterPromptTemplateSystemName.value =
        perf?.relevance_filter?.prompt_template_system_name ?? ''
    }
  },
  { immediate: true }
)

function onConfirm() {
  emit('save', {
    extraction: {
      approach: approach.value,
      mode: mode.value,
      schema_format: schemaFormat.value,
      prompt_template_system_name: promptTemplateSystemName.value.trim(),
      analysis_prompt_template_system_name: analysisPromptTemplateSystemName.value.trim(),
      reflective_prompt_template_system_name: reflectivePromptTemplateSystemName.value.trim(),
      self_tuning_prompt_template_system_name: selfTuningPromptTemplateSystemName.value.trim(),
      self_tuning_analysis_prompt_template_system_name: selfTuningAnalysisPromptTemplateSystemName.value.trim(),
      segment_size: segmentSize.value,
      segment_overlap: segmentOverlap.value,
      max_extraction_iterations: maxExtractionIterations.value,
    },
    performance_optimizations: {
      relevance_filter: {
        prompt_template_system_name: relevanceFilterPromptTemplateSystemName.value.trim(),
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
</style>

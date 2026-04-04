<template>
  <div class="q-px-md">
    <!-- Header with Prompt Controls -->
    <div class="row items-center q-mb-md">
      <div class="col">
        <div class="km-heading-7">{{ m.retrieval_agentConfiguration() }}</div>
        <div class="km-description text-secondary-text">
          {{ m.retrieval_agentConfigurationDesc() }}
        </div>
      </div>
      <div class="col-auto">
        <tab-controls
          :validation-errors="validationErrors"
          :available-variants="availableVariants"
          :current-variant="currentVariant"
          :current-variant-label="currentVariantLabel"
          :has-unsaved-changes="hasUnsavedChanges"
          :is-modified="formModifiedSinceLoad"
          :saving="saving"
          :current-prompt-text="currentPromptText"
          :graph-name="props.graphDetails?.name || ''"
          @switch-variant="switchVariant"
          @open-variant="openPromptVariant"
          @save-current="saveToCurrentVariant"
          @save-new="saveAsNewVariant"
        />
      </div>
    </div>

    <q-separator class="q-my-md" />

    <q-form class="column q-gap-32" @submit.prevent="saveToCurrentVariant">
      <!-- Agent Prompt Cards -->
      <km-section :title="m.retrieval_promptConfiguration()" :sub-title="m.retrieval_promptConfigurationDesc()">
        <div class="column q-gutter-y-sm">
          <kg-expandable-prompt
            v-model="persona"
            :title="m.retrieval_agentIdentity()"
            :description="m.retrieval_agentIdentityDesc()"
            placeholder="You are an advanced ReAct agent..."
            @update:model-value="markAsChanged"
          />
          <kg-expandable-prompt
            v-model="instructions"
            :title="m.retrieval_reactInstructions()"
            :description="m.retrieval_reactInstructionsDesc()"
            placeholder="## ReAct Instructions..."
            @update:model-value="markAsChanged"
          />
        </div>
      </km-section>

      <!-- Document Filtering Tools -->
      <km-section :title="m.retrieval_filteringTools()" :sub-title="m.retrieval_filteringToolsDesc()" class="retrieval-section">
        <div class="column q-gap-8">
          <tool-section
            v-for="tool in filterTools"
            :key="tool.id"
            icon="filter_alt"
            icon-color="primary-light"
            icon-text-color="primary"
            variant="search"
            :label="tool.label"
            :description="tool.description"
            :badge="tool.isStub ? m.common_comingSoon() : ''"
            :disabled="!tool.enabled || tool.isStub"
            :show-toggle="true"
            :enabled="tool.enabled"
            :toggle-disabled="tool.isStub"
            @click="onToolClick($event, tool)"
            @update:enabled="handleToolEnabledChange(tool, $event)"
          >
            <template v-if="!tool.isStub" #stats>
              <!-- Metadata tool shows control mode -->
              <template v-if="tool.id === 'findDocumentsByMetadata'" />
              <!-- Other filter tools show search method, score, limit -->
              <template v-else>
                <tool-stat icon="search" :label="getSearchMethodLabel(tool.searchMethod)" />
                <tool-stat icon="tune" :label="m.retrieval_minScore({ value: ((tool.scoreThreshold || 0) * 100).toFixed(0) })" />
                <tool-stat icon="format_list_numbered" :label="m.retrieval_limit({ value: tool.limit })" />
              </template>
            </template>
          </tool-section>
        </div>
      </km-section>

      <!-- Chunk Retrieval Tools -->
      <km-section :title="m.retrieval_chunkRetrievalTools()" :sub-title="m.retrieval_chunkRetrievalToolsDesc()">
        <div class="column q-gap-8">
          <tool-section
            v-for="tool in retrievalTools"
            :key="tool.id"
            icon="search"
            icon-color="primary-light"
            icon-text-color="primary"
            variant="search"
            :label="tool.label"
            :description="tool.description"
            :show-toggle="true"
            :enabled="true"
            :toggle-disabled="true"
            @click="onToolClick($event, tool)"
          >
            <template #stats>
              <tool-stat icon="search" :label="getSearchMethodLabel(tool.searchMethod)" />
              <tool-stat icon="tune" :label="m.retrieval_minScore({ value: ((tool.scoreThreshold || 0) * 100).toFixed(0) })" />
              <tool-stat icon="format_list_numbered" :label="m.retrieval_limit({ value: tool.limit })" />
            </template>
          </tool-section>
        </div>
      </km-section>

      <!-- Loop Termination (Exit Tool) -->
      <km-section :title="m.retrieval_loopTermination()" :sub-title="m.retrieval_loopTerminationDesc()">
        <tool-section
          v-if="exitTool"
          icon="logout"
          icon-color="deep-orange-1"
          icon-text-color="deep-orange-9"
          variant="exit"
          :label="exitTool.label"
          :description="exitTool.description"
          @click="onToolClick($event, exitTool)"
        >
          <template #stats>
            <tool-stat :icon="getStrategyIcon(exitTool.strategy)" :label="getStrategyLabel(exitTool.strategy)" />
            <tool-stat icon="repeat" :label="m.retrieval_maxIterationsValue({ value: exitTool.maxIterations })" />
            <tool-stat icon="description" :label="getOutputFormatLabel(exitTool.outputFormat)" />
            <tool-stat icon="output" :label="getAnswerModeLabel(exitTool.answerMode)" />
          </template>
        </tool-section>
      </km-section>

      <!-- Generation Parameters -->
      <km-section :title="m.retrieval_generationSettings()" :sub-title="m.retrieval_generationSettingsDesc()">
        <div class="row q-col-gutter-x-xl">
          <!-- Model Selection -->
          <div class="col-6">
            <div class="row items-center q-gutter-xs q-mb-xs">
              <span class="km-input-label">{{ m.retrieval_languageModel() }}</span>
              <q-icon v-if="!model" name="o_info" color="grey-6" size="xs">
                <q-tooltip class="text-body2">{{ m.retrieval_selectLlmTooltip() }}</q-tooltip>
              </q-icon>
            </div>
            <kg-dropdown-field
              v-model="model"
              :options="availableModels"
              :placeholder="m.retrieval_selectLanguageModel()"
              :no-options-label="m.retrieval_noLanguageModels()"
              option-value="value"
              option-label="label"
              :option-meta="formatModelPrice"
              :clearable="true"
              @update:model-value="markAsChanged"
            />

            <!-- Reasoning Effort -->
            <div class="q-mt-md">
              <div class="row items-center q-gutter-xs q-mb-xs">
                <span class="km-input-label text-grey-6">{{ m.retrieval_reasoningEffort() }}</span>
                <q-badge color="orange-1" text-color="orange-9" :label="m.common_comingSoon()" class="text-weight-medium" />
              </div>
              <kg-dropdown-field model-value="" :options="reasoningEffortOptions" :placeholder="m.retrieval_selectReasoningEffort()" :disable="true" />
            </div>
          </div>

          <!-- Sampling Parameters -->
          <div class="col-6 q-pr-md">
            <div class="column q-col-gutter-lg">
              <div class="col-12 col-md-6">
                <div class="row items-center justify-between q-mb-6">
                  <div class="km-input-label">{{ m.evaluation_temperature() }}</div>
                  <div class="param-value">{{ temperature.toFixed(2) }}</div>
                </div>
                <q-slider
                  v-model="temperature"
                  :min="0"
                  :max="2"
                  :step="0.05"
                  color="primary"
                  label
                  :label-value="temperature.toFixed(1)"
                  @update:model-value="markAsChanged"
                />
              </div>
              <div class="col-12 col-md-6">
                <div class="row items-center justify-between q-mb-6">
                  <div class="km-input-label">{{ m.retrieval_topPNucleus() }}</div>
                  <div class="param-value">{{ topP.toFixed(2) }}</div>
                </div>
                <q-slider
                  v-model="topP"
                  :min="0"
                  :max="1"
                  :step="0.05"
                  color="primary"
                  label
                  :label-value="topP.toFixed(2)"
                  @update:model-value="markAsChanged"
                />
              </div>
            </div>
          </div>
        </div>
      </km-section>

      <!-- Guided Examples -->
      <km-section :title="m.retrieval_guidedExamples()" :sub-title="m.retrieval_guidedExamplesDesc()">
        <guided-examples-table :examples="examples" @save="saveExample" @remove="removeExample" />
      </km-section>
    </q-form>

    <!-- Tool Configuration Dialog -->
    <component :is="getToolComponent(editingTool?.id)" v-if="showToolDialog" v-model="showToolDialog" :tool="editingTool" @save="onSaveTool" />

    <!-- Unsaved Changes Variant Switch Warning -->
    <km-popup-confirm
      :visible="showVariantWarning"
      :confirm-button-label="m.retrieval_saveAndSwitch()"
      :confirm-button-label2="m.retrieval_discardAndSwitch()"
      confirm-button-type2="secondary"
      :cancel-button-label="m.common_cancel()"
      notification-icon="fas fa-triangle-exclamation"
      :loading="saving"
      @confirm="saveAndSwitchVariant"
      @confirm2="discardAndSwitchVariant"
      @cancel="cancelVariantSwitch"
    >
      <div class="row item-center justify-center km-heading-7 q-mb-md">{{ m.retrieval_unsavedChanges() }}</div>
      <div class="row text-center justify-center">{{ m.retrieval_unsavedChangesDesc() }}</div>
    </km-popup-confirm>
  </div>
</template>

<script setup lang="ts">
import { uid } from 'quasar'
import { m } from '@/paraglide/messages'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useEntityQueries } from '@/queries/entities'
import { useNotify } from '@/composables/useNotify'
import { useQueryClient } from '@tanstack/vue-query'
import { useKnowledgeGraphPageStore } from '@/stores/entityDetailStores'
import { KgDropdownField, KgExpandablePrompt } from '../common'
import type { KnowledgeGraphDetails, KnowledgeGraphSettings } from '../types'
import GuidedExamplesTable from './GuidedExamplesTable.vue'
import TabControls from './RetrievalTabControls.vue'
import ToolSection from './ToolSection.vue'
import ToolStat from './ToolStat.vue'
import ComingSoonToolDialog from './Tools/ComingSoonToolDialog.vue'
import ExitToolDialog from './Tools/ExitToolDialog.vue'
import FindChunksBySimilarityDialog from './Tools/FindChunksBySimilarityDialog.vue'
import FindDocumentsByMetadataDialog from './Tools/FindDocumentsByMetadataDialog.vue'
import FindDocumentsBySummaryDialog from './Tools/FindDocumentsBySummaryDialog.vue'
import {
  tools as defaultTools,
  RetrievalExample,
  searchMethodOptions,
  Tool,
  type PromptTemplate,
  type PromptTemplateVariant,
  type RetrievalConfig,
  type ToolDefinition,
  type ValidationError,
} from './models'
import {
  BASE_VARIANT_NAME,
  createGraphVariantName,
  createVariantFromConfig,
  findVariant,
  PROMPT_SYSTEM_NAME,
  promptToConfig,
} from './promptConfigConverter'

const emit = defineEmits<{
  (e: 'unsaved-change', value: boolean): void
  (e: 'update-graph', payload: KnowledgeGraphSettings): void
}>()

const props = defineProps<{
  graphId: string
  graphDetails?: KnowledgeGraphDetails
}>()

const { notifySuccess, notifyError } = useNotify()
const router = useRouter()
const queries = useEntityQueries()
const queryClient = useQueryClient()
const kgPageStore = useKnowledgeGraphPageStore()
const { mutateAsync: updatePromptTemplate } = queries.promptTemplates.useUpdate()
const { data: modelListData } = queries.model.useList()
const { data: promptTemplatesListData } = queries.promptTemplates.useList()
const promptItems = computed(() => promptTemplatesListData.value?.items ?? [])
const modelItems = computed(() => modelListData.value?.items ?? [])

// --- State ---
const saving = ref(false)
const loading = ref(false)
const hasUnsavedChanges = ref(false)
const validationErrors = ref<ValidationError[]>([])

// --- Tools State ---
const tools = ref<Tool[]>(JSON.parse(JSON.stringify(defaultTools)))

// --- Prompt Template State ---
const promptTemplate = ref<PromptTemplate | null>(null)
const currentVariant = ref<string>(BASE_VARIANT_NAME)
const graphVariantName = computed(() => createGraphVariantName(props.graphId))

// --- Dialog State ---
const showToolDialog = ref(false)
const showVariantWarning = ref(false)

const editingTool = ref<Tool | null>(null)
const editingToolIndex = ref(-1)

const pendingVariantSwitch = ref<string | null>(null)

const getSearchMethodLabel = (value?: string) => {
  const option = searchMethodOptions.find((o) => o.value === value)
  return option?.label || value
}

const getOutputFormatLabel = (value?: string) => {
  const map: Record<string, string> = {
    markdown: m.retrieval_outputMarkdown(),
    plain: m.retrieval_outputPlainText(),
  }
  return value ? map[value] || value : m.retrieval_outputMarkdown()
}

const getAnswerModeLabel = (value?: string) => {
  const map: Record<string, string> = {
    answer_only: m.retrieval_answerOnly(),
    sources_only: m.retrieval_sourcesOnly(),
    answer_with_sources: m.retrieval_answerWithSources(),
  }
  return value ? map[value] || value : m.retrieval_answerWithSources()
}

const getStrategyLabel = (value?: string) => {
  if (value === 'confidence') return m.retrieval_confidenceBased()
  if (value === 'exhaustive') return m.retrieval_exhaustive()
  if (value === 'efficient') return m.retrieval_efficient()
  return value || m.retrieval_confidenceBased()
}

const getStrategyIcon = (value?: string) => {
  if (value === 'confidence') return 'psychology'
  if (value === 'exhaustive') return 'search'
  if (value === 'efficient') return 'bolt'
  return 'psychology'
}

// --- Prompt Sections ---
const persona = ref('')
const instructions = ref('')

// Store the saved variant name for this graph (from API)
const savedGraphVariant = ref<string>('')

// Track if form fields have been modified since last variant switch/load
const formModifiedSinceLoad = ref(false)
// Track if graph-specific settings (scoreThreshold, limit, etc.) have been modified
const hasGraphSettingsChanges = ref(false)

// --- Guided Examples ---
const examples = ref<RetrievalExample[]>([])

// --- Generation Parameters ---
const temperature = ref(0.7)
const topP = ref(0.9)
const model = ref<string | undefined>(undefined)

// --- Computed ---
const availableModels = computed(() => {
  return (modelItems.value || [])
    .filter((m: any) => m.type === 'prompts')
    .map((m: any) => ({
      label: m.display_name || m.name,
      value: m.system_name,
      provider: m.provider_system_name,
      priceInput: m.price_input,
      priceOutput: m.price_output,
    }))
    .sort((a: any, b: any) => a.label.localeCompare(b.label))
})

const formatModelPrice = (opt: any): string | undefined => {
  const input = opt?.priceInput
  const output = opt?.priceOutput
  if (!input && !output) return undefined
  const parts = []
  if (input) parts.push(`$${input}`)
  if (output) parts.push(`$${output}`)
  return parts.join('/')
}

const selectedModelLabel = computed(() => {
  if (!model.value) return null
  const found = availableModels.value.find((m: any) => m.value === model.value)
  return found?.label || model.value
})

const reasoningEffortOptions = [
  { label: 'Low', value: 'low' },
  { label: 'Medium', value: 'medium' },
  { label: 'High', value: 'high' },
]

const filterTools = computed(() => tools.value.filter((t) => t.category === 'filter'))
const retrievalTools = computed(() => tools.value.filter((t) => t.category === 'retrieval'))
const exitTool = computed(() => tools.value.find((t) => t.category === 'exit'))

const availableVariants = computed(() => {
  const variants: Array<{ name: string; label: string; description: string }> = []

  if (promptTemplate.value) {
    for (const v of promptTemplate.value.variants) {
      variants.push({
        name: v.variant,
        label: v.display_name || (v.variant === BASE_VARIANT_NAME ? m.knowledgeGraph_baseVariantLabel() : v.variant),
        description: v.description || (v.variant === BASE_VARIANT_NAME ? m.knowledgeGraph_defaultConfiguration() : m.knowledgeGraph_customVariant()),
      })
    }
  }

  return variants
})

const currentVariantLabel = computed(() => {
  const variant = availableVariants.value.find((v) => v.name === currentVariant.value)
  return variant?.label || currentVariant.value
})

const currentPromptText = computed(() => {
  const v = promptTemplate.value ? findVariant(promptTemplate.value, currentVariant.value) : undefined
  return v?.text || ''
})

const enabledToolDefinitions = computed((): ToolDefinition[] => {
  return tools.value
    .filter((t) => t.enabled && !t.isStub)
    .map((t) => ({
      name: t.name,
      description: t.description,
      enabled: true,
    }))
})

// --- Methods ---

function serializeToolSettings() {
  const settings: Record<string, any> = {}

  tools.value.forEach((tool) => {
    if (tool.category === 'exit') {
      settings.exit = {
        description: tool.description,
        strategy: tool.strategy,
        maxIterations: tool.maxIterations,
        outputFormat: tool.outputFormat,
        answerMode: tool.answerMode,
      }
    } else {
      // Common properties for filter/retrieval
      settings[tool.name] = {
        searchControl: tool.searchControl,
        scoreThreshold: tool.scoreThreshold,
        limit: tool.limit,
        hybridWeight: tool.hybridWeight,
        searchMethod: tool.searchMethod,
        description: tool.description,
        enabled: tool.enabled,
        metadataMergeStrategy: tool.metadataMergeStrategy,
      }
    }
  })

  return settings
}

function applyGraphSettings(settings: any) {
  if (!settings) return

  if (settings.retrieval_examples) {
    examples.value = JSON.parse(JSON.stringify(settings.retrieval_examples))
  }

  if (!settings.retrieval_tools) return

  const toolSettings = settings.retrieval_tools

  tools.value.forEach((tool) => {
    // Apply settings safely
    const applySettings = (target: any, source: any, keys: string[]) => {
      if (!source) return
      keys.forEach((key) => {
        if (source[key] !== undefined) target[key] = source[key]
      })
    }

    if (tool.category === 'exit') {
      if (toolSettings.exit) {
        applySettings(tool, toolSettings.exit, ['description', 'strategy', 'maxIterations', 'answerMode', 'outputFormat'])
      }
    } else {
      applySettings(tool, toolSettings[tool.name], [
        'searchControl',
        'scoreThreshold',
        'limit',
        'hybridWeight',
        'searchMethod',
        'description',
        'enabled',
        'metadataMergeStrategy',
      ])
    }
  })
}

function getCurrentConfig(): RetrievalConfig {
  return {
    promptSections: {
      persona: persona.value,
      instructions: instructions.value,
      additionalOutputInstructions: exitTool.value?.additionalOutputInstructions || '',
    },
    temperature: temperature.value,
    topP: topP.value,
    model: model.value,
    examples: examples.value,
    enabledTools: enabledToolDefinitions.value,
  }
}

function markAsChanged() {
  formModifiedSinceLoad.value = true
  updateUnsavedState()
}

function markGraphChanged() {
  hasGraphSettingsChanges.value = true
  updateUnsavedState()
}

function updateUnsavedState() {
  hasUnsavedChanges.value = currentVariant.value !== savedGraphVariant.value || formModifiedSinceLoad.value || hasGraphSettingsChanges.value
}

function resetChangeTracking(updateSavedVariant = true) {
  if (updateSavedVariant) {
    savedGraphVariant.value = currentVariant.value
  }
  hasUnsavedChanges.value = false
  formModifiedSinceLoad.value = false
  hasGraphSettingsChanges.value = false
}

// --- API Methods ---

function loadPromptTemplate() {
  loading.value = true
  try {
    const prompts = promptItems.value || []
    const template = prompts.find((p: PromptTemplate) => p.system_name === PROMPT_SYSTEM_NAME)

    if (template) {
      promptTemplate.value = template

      const configuredVariantName = props.graphDetails?.settings?.retrieval_variant
      const configuredVariant = configuredVariantName ? findVariant(promptTemplate.value!, configuredVariantName) : undefined

      if (configuredVariant) {
        currentVariant.value = configuredVariantName
        savedGraphVariant.value = configuredVariantName
        applyVariantToConfig(configuredVariant)
      } else {
        const graphVariant = findVariant(promptTemplate.value!, graphVariantName.value)
        if (graphVariant) {
          currentVariant.value = graphVariantName.value
          savedGraphVariant.value = graphVariantName.value
          applyVariantToConfig(graphVariant)
        } else {
          const activeVariant =
            findVariant(promptTemplate.value!, promptTemplate.value!.active_variant) || findVariant(promptTemplate.value!, BASE_VARIANT_NAME)
          if (activeVariant) {
            currentVariant.value = activeVariant.variant
            savedGraphVariant.value = ''
            applyVariantToConfig(activeVariant)
          }
        }
      }

      applyGraphSettings(props.graphDetails?.settings)
    } else {
      validationErrors.value = [
        {
          type: 'not_found',
          message: m.knowledgeGraph_defaultConfiguration(),
        },
      ]
    }
  } catch (error) {

    notifyError(m.knowledgeGraph_failedToLoadPromptTemplate())
  } finally {
    loading.value = false
    resetChangeTracking(false)
  }
}

function applyVariantToConfig(variant: PromptTemplateVariant) {
  if (variant.temperature !== undefined) {
    temperature.value = variant.temperature
  }
  if (variant.topP !== undefined) {
    topP.value = variant.topP
  }
  if (variant.system_name_for_model !== undefined) {
    model.value = variant.system_name_for_model
  }

  if (variant.text) {
    const result = promptToConfig(variant.text, {
      temperature: temperature.value,
      topP: topP.value,
      model: model.value,
      enabledTools: enabledToolDefinitions.value,
      examples: examples.value,
    })

    if (result.data) {
      persona.value = result.data.promptSections.persona
      instructions.value = result.data.promptSections.instructions

      if (exitTool.value) {
        exitTool.value.additionalOutputInstructions = result.data.promptSections.additionalOutputInstructions
      }

      // Only update examples if the prompt template contains them (legacy support)
      // For new format, examples are managed via graph settings and shouldn't be cleared when switching variants
      if (result.data.examples && result.data.examples.length > 0) {
        examples.value = result.data.examples
      }
    }
    validationErrors.value = result.errors
  }
}

async function saveToCurrentVariant() {
  if (!hasUnsavedChanges.value) return

  saving.value = true
  try {
    const config = getCurrentConfig()
    const variantResult = createVariantFromConfig(
      currentVariant.value,
      config,
      promptTemplate.value?.variants.find((v) => v.variant === currentVariant.value)
    )

    if (!variantResult.success || !variantResult.data) {
      validationErrors.value = variantResult.errors

      notifyError(m.knowledgeGraph_failedToGeneratePrompt())
      return
    }

    await saveVariant(variantResult.data)

    emit('update-graph', {
      settings: {
        ...(props.graphDetails?.settings || {}),
        retrieval_variant: currentVariant.value,
        retrieval_tools: serializeToolSettings(),
        retrieval_examples: examples.value,
      },
    })

    notifySuccess(m.knowledgeGraph_settingsSavedSuccessfully())

    resetChangeTracking()
  } catch (error) {

    notifyError(m.knowledgeGraph_failedToSaveSettingsMsg())
  } finally {
    saving.value = false
  }
}

async function saveAsNewVariant(payload: { name: string; displayName: string; description: string }) {
  saving.value = true
  try {
    const config = getCurrentConfig()
    const variantResult = createVariantFromConfig(payload.name, config, undefined, payload.displayName, payload.description)

    if (!variantResult.success || !variantResult.data) {
      validationErrors.value = variantResult.errors
      notifyError(m.knowledgeGraph_failedToGeneratePrompt())
      return
    }

    await saveVariant(variantResult.data)
    currentVariant.value = payload.name

    emit('update-graph', {
      settings: {
        ...(props.graphDetails?.settings || {}),
        retrieval_variant: currentVariant.value,
        retrieval_tools: serializeToolSettings(),
        retrieval_examples: examples.value,
      },
    })

    notifySuccess(m.knowledgeGraph_createdNewVariant({ name: currentVariant.value }))

    resetChangeTracking()
  } catch (error) {

    notifyError(m.knowledgeGraph_failedToCreateVariant())
  } finally {
    saving.value = false
  }
}

async function saveVariant(variant: PromptTemplateVariant, isNew = false) {
  if (!promptTemplate.value) {
    notifyError(m.knowledgeGraph_noPromptTemplateLoaded())
    return
  }

  const variants = [...promptTemplate.value.variants]
  const existingIdx = variants.findIndex((v) => v.variant === variant.variant)

  if (existingIdx >= 0) {
    variants[existingIdx] = variant
  } else {
    variants.push(variant)
  }

  const updatedTemplate = { ...promptTemplate.value, variants }
  delete (updatedTemplate as any)._metadata

  const result = await updatePromptTemplate({ id: promptTemplate.value.id, data: updatedTemplate })
  if (result) {
    promptTemplate.value.variants = variants
  } else {
    notifyError(m.knowledgeGraph_failedToUpdatePromptTemplate())
  }

  await queryClient.invalidateQueries({ queryKey: ['promptTemplates'] })

  const prompts = promptItems.value || []
  const updatedFromStore = prompts.find((p: PromptTemplate) => p.system_name === PROMPT_SYSTEM_NAME)
  if (updatedFromStore) {
    promptTemplate.value = updatedFromStore
  }
}

function switchVariant(variantName: string) {
  if (formModifiedSinceLoad.value) {
    pendingVariantSwitch.value = variantName
    showVariantWarning.value = true
  } else {
    doSwitchVariant(variantName)
  }
}

function discardAndSwitchVariant() {
  showVariantWarning.value = false
  if (pendingVariantSwitch.value) {
    doSwitchVariant(pendingVariantSwitch.value)
    pendingVariantSwitch.value = null
  }
}

async function saveAndSwitchVariant() {
  await saveToCurrentVariant()
  showVariantWarning.value = false
  if (pendingVariantSwitch.value) {
    doSwitchVariant(pendingVariantSwitch.value)
    pendingVariantSwitch.value = null
  }
}

function cancelVariantSwitch() {
  showVariantWarning.value = false
  pendingVariantSwitch.value = null
}

function doSwitchVariant(variantName: string) {
  currentVariant.value = variantName
  const variant = findVariant(promptTemplate.value!, variantName)

  if (variant) {
    applyVariantToConfig(variant)
  }

  formModifiedSinceLoad.value = false
  updateUnsavedState()
}

function openPromptVariant() {
  if (!promptTemplate.value?.id) {
    notifyError(m.knowledgeGraph_promptTemplateNotLoaded())
    return
  }
  const route = router.resolve({
    name: 'PromptTemplatesItem',
    params: { id: promptTemplate.value.id },
    query: { variant: currentVariant.value },
  })
  window.open(route.href, '_blank')
}

// --- Dialog Actions ---

const handleToolEnabledChange = (tool: Tool, enabled: boolean) => {
  tool.enabled = enabled
  markGraphChanged()
}

const onToolClick = (_evt: any, tool: Tool) => {
  editingToolIndex.value = tools.value.findIndex((t) => t.id === tool.id)
  editingTool.value = { ...tool }
  showToolDialog.value = true
}

const onSaveTool = (updatedTool: Tool) => {
  if (editingToolIndex.value >= 0) {
    const oldTool = tools.value[editingToolIndex.value]
    tools.value[editingToolIndex.value] = updatedTool

    // Check for prompt config changes
    if (oldTool.additionalOutputInstructions !== updatedTool.additionalOutputInstructions) {
      markAsChanged()
    }

    // Check for graph config changes
    if (
      oldTool.description !== updatedTool.description ||
      oldTool.enabled !== updatedTool.enabled ||
      oldTool.searchControl !== updatedTool.searchControl ||
      oldTool.scoreThreshold !== updatedTool.scoreThreshold ||
      oldTool.limit !== updatedTool.limit ||
      oldTool.hybridWeight !== updatedTool.hybridWeight ||
      oldTool.searchMethod !== updatedTool.searchMethod ||
      oldTool.strategy !== updatedTool.strategy ||
      oldTool.maxIterations !== updatedTool.maxIterations ||
      oldTool.answerMode !== updatedTool.answerMode ||
      oldTool.outputFormat !== updatedTool.outputFormat ||
      oldTool.metadataMergeStrategy !== updatedTool.metadataMergeStrategy
    ) {
      markGraphChanged()
    }
  }

  showToolDialog.value = false
}

const getToolComponent = (toolId?: string) => {
  switch (toolId) {
    case 'findDocumentsByMetadata':
      return FindDocumentsByMetadataDialog
    case 'findDocumentsBySummary':
      return FindDocumentsBySummaryDialog
    case 'findChunksBySimilarity':
      return FindChunksBySimilarityDialog
    case 'exit':
      return ExitToolDialog
    default:
      return ComingSoonToolDialog
  }
}

// --- Examples Actions ---
const saveExample = (example: RetrievalExample) => {
  if (!example.id || example.id === '0') {
    examples.value.push({
      ...example,
      id: uid(),
    })
  } else {
    const idx = examples.value.findIndex((e) => e.id === example.id)
    if (idx !== -1) {
      examples.value[idx] = example
    }
  }
  markGraphChanged()
}

const removeExample = (id: string) => {
  examples.value = examples.value.filter((example) => example.id !== id)
  markGraphChanged()
}

// --- Navigation Guard ---
function handleBeforeUnload(e: BeforeUnloadEvent) {
  if (hasUnsavedChanges.value) {
    e.preventDefault()
    e.returnValue = ''
  }
}

// --- Lifecycle ---
onMounted(() => {
  loadPromptTemplate()
  window.addEventListener('beforeunload', handleBeforeUnload)

  kgPageStore.setSaveCallback(async () => {
    await saveToCurrentVariant()
  })
  kgPageStore.setRevertCallback(() => {
    doSwitchVariant(currentVariant.value)
  })
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload)
  kgPageStore.setRetrievalChanged(false)
  kgPageStore.clearCallbacks()
})

watch(
  () => props.graphId,
  () => {
    loadPromptTemplate()
  }
)

watch(
  () => promptItems.value,
  (newPrompts) => {
    if (newPrompts?.length > 0 && !promptTemplate.value) {
      loadPromptTemplate()
    }
  },
  { immediate: false }
)

watch(
  hasUnsavedChanges,
  (val) => {
    emit('unsaved-change', val)
    kgPageStore.setRetrievalChanged(val)
  },
  { immediate: true }
)

defineExpose({
  async save() {
    await saveToCurrentVariant()
  },
  discard() {
    doSwitchVariant(currentVariant.value)
  },
})
</script>

<style scoped>
:deep(.q-expansion-item__content) {
  border-radius: 0 var(--radius-lg);
}

.retrieval-section :deep(> .col-4) {
  width: 300px;
}

/* Generation Settings Section */
.param-value {
  font-size: 0.875rem;
  font-weight: 600;
  color: var(--q-primary);
  min-width: 40px;
  text-align: right;
}

.param-hint {
  font-size: 0.75rem;
  color: var(--q-secondary-text);
  margin-top: 4px;
  line-height: 1.4;
}
</style>

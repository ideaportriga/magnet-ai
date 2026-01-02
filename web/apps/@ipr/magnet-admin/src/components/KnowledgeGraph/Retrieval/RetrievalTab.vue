<template>
  <div class="q-px-md">
    <!-- Header with Prompt Controls -->
    <div class="row items-center q-mb-md">
      <div class="col">
        <div class="km-heading-7">Retrieval Agent Configuration</div>
        <div class="km-description text-secondary-text">
          Configure the ReAct instructions, tools, generation parameters, and guided examples to tune retrieval agent behavior
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
      <km-section title="Prompt Configuration" sub-title="Customize ReAct prompt sections to adjust agent behavior">
        <div class="column q-gutter-y-sm">
          <kg-expandable-prompt
            v-model="persona"
            title="Agent Identity"
            description="Define the agent's role and capabilities"
            placeholder="You are an advanced ReAct agent..."
            @update:model-value="markAsChanged"
          />
          <kg-expandable-prompt
            v-model="instructions"
            title="ReAct Instructions"
            description="Operational rules and workflows"
            placeholder="## ReAct Instructions..."
            @update:model-value="markAsChanged"
          />
        </div>
      </km-section>

      <!-- Document Filtering Tools -->
      <km-section title="Document Filtering Tools" sub-title="Pre-filter documents before chunk retrieval" class="retrieval-section">
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
            :badge="tool.isStub ? 'Coming Soon' : ''"
            :disabled="!tool.enabled || tool.isStub"
            :show-toggle="true"
            :enabled="tool.enabled"
            :toggle-disabled="tool.isStub"
            @click="onToolClick($event, tool)"
            @update:enabled="handleToolEnabledChange(tool, $event)"
          >
            <template v-if="!tool.isStub" #stats>
              <tool-stat icon="search" :label="getSearchMethodLabel(tool.searchMethod)" />
              <tool-stat icon="tune" :label="`Min score ${((tool.scoreThreshold || 0) * 100).toFixed(0)}%`" />
              <tool-stat icon="format_list_numbered" :label="`Limit ${tool.limit}`" />
            </template>
          </tool-section>
        </div>
      </km-section>

      <!-- Chunk Retrieval Tools -->
      <km-section title="Chunk Retrieval Tools" sub-title="Search for specific information within the knowledge graph">
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
              <tool-stat icon="tune" :label="`Min score ${((tool.scoreThreshold || 0) * 100).toFixed(0)}%`" />
              <tool-stat icon="format_list_numbered" :label="`Limit ${tool.limit}`" />
            </template>
          </tool-section>
        </div>
      </km-section>

      <!-- Loop Termination (Exit Tool) -->
      <km-section title="Loop Termination" sub-title="Configure when the agent should exit the agent's loop and deliver the final answer">
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
            <tool-stat icon="repeat" :label="`Max ${exitTool.maxIterations} iterations`" />
            <tool-stat icon="description" :label="getOutputFormatLabel(exitTool.outputFormat)" />
            <tool-stat icon="output" :label="getAnswerModeLabel(exitTool.answerMode)" />
          </template>
        </tool-section>
      </km-section>

      <!-- Generation Parameters -->
      <km-section title="Generation Settings" sub-title="Configure the language model and sampling parameters for response generation">
        <div class="row q-col-gutter-x-xl">
          <!-- Model Selection -->
          <div class="col-6">
            <div class="row items-center q-gutter-xs q-mb-xs">
              <span class="km-input-label">Language Model</span>
              <q-icon v-if="!model" name="o_info" color="grey-6" size="xs">
                <q-tooltip class="text-body2">Select an LLM to generate responses</q-tooltip>
              </q-icon>
            </div>
            <kg-dropdown-field
              v-model="model"
              :options="availableModels"
              placeholder="Select language model"
              no-options-label="No language models available"
              option-value="value"
              option-label="label"
              :option-meta="formatModelPrice"
              :clearable="true"
              @update:model-value="markAsChanged"
            />

            <!-- Reasoning Effort -->
            <div class="q-mt-md">
              <div class="row items-center q-gutter-xs q-mb-xs">
                <span class="km-input-label text-grey-6">Reasoning Effort</span>
                <q-badge color="orange-1" text-color="orange-9" label="Coming Soon" class="text-weight-medium" />
              </div>
              <kg-dropdown-field model-value="" :options="reasoningEffortOptions" placeholder="Select reasoning effort" :disable="true" />
            </div>
          </div>

          <!-- Sampling Parameters -->
          <div class="col-6 q-pr-md">
            <div class="column q-col-gutter-lg">
              <div class="col-12 col-md-6">
                <div class="row items-center justify-between q-mb-6">
                  <div class="km-input-label">Temperature</div>
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
                  <div class="km-input-label">Top P (Nucleus Sampling)</div>
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
      <km-section title="Guided Examples" sub-title="Capture concrete examples to guide retrieval agent behavior in different scenarios">
        <guided-examples-table :examples="examples" @save="saveExample" @remove="removeExample" />
      </km-section>
    </q-form>

    <!-- Tool Configuration Dialog -->
    <component :is="getToolComponent(editingTool?.id)" v-if="showToolDialog" v-model="showToolDialog" :tool="editingTool" @save="onSaveTool" />

    <!-- Unsaved Changes Variant Switch Warning -->
    <km-popup-confirm
      :visible="showVariantWarning"
      confirm-button-label="Save & Switch"
      confirm-button-label2="Discard & Switch"
      confirm-button-type2="secondary"
      cancel-button-label="Cancel"
      notification-icon="fas fa-triangle-exclamation"
      :loading="saving"
      @confirm="saveAndSwitchVariant"
      @confirm2="discardAndSwitchVariant"
      @cancel="cancelVariantSwitch"
    >
      <div class="row item-center justify-center km-heading-7 q-mb-md">Unsaved Changes</div>
      <div class="row text-center justify-center">You have unsaved changes. Switching variants will discard them. What would you like to do?</div>
    </km-popup-confirm>
  </div>
</template>

<script setup lang="ts">
import { useChroma } from '@shared'
import { uid, useQuasar } from 'quasar'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useStore } from 'vuex'
import { KgDropdownField, KgExpandablePrompt } from '../common'
import GuidedExamplesTable from './GuidedExamplesTable.vue'
import TabControls from './RetrievalTabControls.vue'
import ToolSection from './ToolSection.vue'
import ToolStat from './ToolStat.vue'
import ComingSoonToolDialog from './Tools/ComingSoonToolDialog.vue'
import ExitToolDialog from './Tools/ExitToolDialog.vue'
import FindChunksBySimilarityDialog from './Tools/FindChunksBySimilarityDialog.vue'
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
  (e: 'update-graph', payload: Record<string, any>): void
}>()

const props = defineProps<{
  graphId: string
  graphDetails?: any
}>()

const $q = useQuasar()
const store = useStore()
const router = useRouter()
const { update: updatePromptTemplate, get: refreshPromptTemplates } = useChroma('promptTemplates')
const { items: modelItems, get: getModels } = useChroma('model')

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
    markdown: 'Markdown',
    plain: 'Plain Text',
  }
  return value ? map[value] || value : 'Markdown'
}

const getAnswerModeLabel = (value?: string) => {
  const map: Record<string, string> = {
    answer_only: 'Answer Only',
    sources_only: 'Sources Only',
    answer_with_sources: 'Answer + Sources',
  }
  return value ? map[value] || value : 'Answer + Sources'
}

const getStrategyLabel = (value?: string) => {
  if (value === 'confidence') return 'Confidence-based'
  if (value === 'exhaustive') return 'Exhaustive'
  if (value === 'efficient') return 'Efficient'
  return value || 'Confidence-based'
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
        label: v.display_name || (v.variant === BASE_VARIANT_NAME ? 'Base Variant' : v.variant),
        description: v.description || (v.variant === BASE_VARIANT_NAME ? 'Default configuration' : 'Custom variant'),
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
    const prompts = store.getters.prompts || []
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
          message: `Prompt template "${PROMPT_SYSTEM_NAME}" not found. Using default configuration.`,
        },
      ]
    }
  } catch (error) {
    console.error('Error loading prompt template:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to load prompt template',
    })
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
      console.log(variantResult.errors)
      $q.notify({
        message: 'Failed to generate prompt. Check validation errors.',
        position: 'top',
        color: 'error-text',
        timeout: 3000,
      })
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

    $q.notify({
      type: 'positive',
      message: 'Settings saved successfully',
      textColor: 'black',
      position: 'top',
      timeout: 3000,
    })

    resetChangeTracking()
  } catch (error) {
    console.error('Error saving settings:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to save settings',
    })
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
      $q.notify({
        type: 'negative',
        message: 'Failed to generate prompt. Check validation errors.',
      })
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

    $q.notify({
      type: 'positive',
      message: `Created new variant "${currentVariant.value}"`,
    })

    resetChangeTracking()
  } catch (error) {
    console.error('Error creating variant:', error)
    $q.notify({
      type: 'negative',
      message: 'Failed to create variant',
    })
  } finally {
    saving.value = false
  }
}

async function saveVariant(variant: PromptTemplateVariant, isNew = false) {
  if (!promptTemplate.value) {
    $q.notify({
      message: 'No prompt template loaded. Please load or create a template first.',
      color: 'error-text',
      position: 'top',
      timeout: 3000,
    })
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

  const result = await updatePromptTemplate({ id: promptTemplate.value.id, data: JSON.stringify(updatedTemplate) })
  if (result) {
    promptTemplate.value.variants = variants
  } else {
    $q.notify({
      message: 'Failed to update prompt template',
      color: 'error-text',
      position: 'top',
      timeout: 3000,
    })
  }

  await refreshPromptTemplates()

  const prompts = store.getters.prompts || []
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
    $q.notify({
      type: 'negative',
      message: 'Prompt template not loaded',
    })
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
      oldTool.outputFormat !== updatedTool.outputFormat
    ) {
      markGraphChanged()
    }
  }

  showToolDialog.value = false
}

const getToolComponent = (toolId?: string) => {
  switch (toolId) {
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
  getModels()
  loadPromptTemplate()
  window.addEventListener('beforeunload', handleBeforeUnload)

  store.commit('setKnowledgeGraphSaveCallback', async () => {
    await saveToCurrentVariant()
  })
  store.commit('setKnowledgeGraphRevertCallback', () => {
    doSwitchVariant(currentVariant.value)
  })
})

onBeforeUnmount(() => {
  window.removeEventListener('beforeunload', handleBeforeUnload)
  store.commit('setKnowledgeGraphRetrievalChanged', false)
  store.commit('clearKnowledgeGraphCallbacks')
})

watch(
  () => props.graphId,
  () => {
    loadPromptTemplate()
  }
)

watch(
  () => store.getters.prompts,
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
    store.commit('setKnowledgeGraphRetrievalChanged', val)
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
  border-radius: 0 8px;
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
  color: var(--q-secondary-text, #6b7280);
  margin-top: 4px;
  line-height: 1.4;
}
</style>

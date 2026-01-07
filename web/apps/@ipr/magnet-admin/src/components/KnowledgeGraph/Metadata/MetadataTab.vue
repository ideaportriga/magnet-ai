<template>
  <div class="q-px-md">
    <!-- Header -->
    <div class="row items-center q-mb-md">
      <div class="col">
        <div class="km-heading-7">Metadata Schema</div>
        <div class="km-description text-secondary-text">
          Define, discover, and manage metadata fields across all documents in this knowledge graph
        </div>
      </div>
      <div v-if="hasChanges" class="col-auto">
        <div class="row items-center no-wrap q-gutter-x-sm">
          <q-btn no-caps flat color="grey-7" label="Cancel" class="kg-action-btn" @click="discardChanges" />
          <q-btn
            no-caps
            unelevated
            color="primary"
            label="Save Changes"
            class="kg-action-btn"
            :loading="saving"
            :disable="!hasChanges"
            @click="saveSettings"
          />
        </div>
      </div>
    </div>

    <q-separator class="q-my-md" />

    <div class="column q-gap-32">
      <metadata-fields-table
        :defined-fields="definedFields"
        :discovered-fields="allMetadataValues"
        :available-presets="availablePresets"
        :loading="loadingValues"
        @add-field="openFieldDialog()"
        @add-preset="addPresetField"
        @define-all="defineAllDiscovered"
        @edit-field="openFieldDialog"
        @delete-field="confirmDeleteField"
        @define-field="openFieldDialogFromDiscovered"
      />

      <!-- AI Metadata Extraction -->
      <km-section title="Smart Metadata Extraction" sub-title="Leverage LLM to extract metadata from documents during ingestion">
        <div class="column q-gap-12">
          <div>
            <div class="row q-col-gutter-md">
              <div v-for="opt in extractionApproachOptions" :key="opt.value" class="col-12 col-md-4">
                <div
                  class="kg-extraction-tile"
                  :class="{ 'kg-extraction-tile--selected': extractionApproach === opt.value }"
                  tabindex="0"
                  role="radio"
                  :aria-checked="extractionApproach === opt.value"
                  @click="extractionApproach = opt.value"
                  @keydown.enter.prevent="extractionApproach = opt.value"
                  @keydown.space.prevent="extractionApproach = opt.value"
                >
                  <div class="kg-extraction-tile__header">
                    <div class="kg-extraction-tile__radio" :class="{ 'kg-extraction-tile__radio--checked': extractionApproach === opt.value }">
                      <div v-if="extractionApproach === opt.value" class="kg-extraction-tile__radio-dot" />
                    </div>
                    <span class="kg-extraction-tile__label">{{ opt.label }}</span>
                  </div>
                  <div class="kg-extraction-tile__description">{{ opt.description }}</div>
                </div>
              </div>
            </div>
          </div>

          <kg-field-row label="Extraction Prompt">
            <div class="row items-start q-col-gutter-md">
              <div class="col">
                <kg-dropdown-field
                  v-model="extractionPromptTemplateSystemName"
                  placeholder="Select a prompt template"
                  :options="promptTemplateOptions"
                  :loading="loadingPromptTemplates"
                  :disable="extractionApproach === 'disabled'"
                  option-value="system_name"
                  option-label="name"
                  searchable
                  clearable
                />
                <div class="km-description text-secondary-text q-mt-sm">
                  Pick a template that returns a JSON object with the metadata fields you want to store.
                </div>
              </div>
              <div class="col-auto">
                <q-btn
                  no-caps
                  unelevated
                  color="primary"
                  label="Run Extraction"
                  class="kg-action-btn"
                  :loading="runningExtraction"
                  :disable="!canRunExtraction || runningExtraction"
                  @click="runExtraction"
                />
              </div>
            </div>
          </kg-field-row>

          <div v-if="extractionApproach === 'document'" class="q-pa-md rounded-borders bg-grey-1" style="border: 1px solid rgba(0, 0, 0, 0.06)">
            <div class="km-heading-8 text-weight-medium q-mb-xs">Document segmentation</div>
            <div class="km-description text-secondary-text q-mb-md">
              When a document is larger than the segment size, Magnet will split it into overlapping segments and run extraction per segment.
            </div>

            <div class="row q-col-gutter-lg">
              <div class="col-12 col-md-4">
                <div class="km-input-label q-pb-sm">Segment size (characters)</div>
                <km-input v-model.number="extractionSegmentSize" type="number" min="100" />
              </div>
              <div class="col-12 col-md-8">
                <div class="km-input-label q-pb-sm">Segment overlap (%)</div>
                <div class="row items-center" style="height: 36px">
                  <q-slider
                    v-model="extractionSegmentOverlap"
                    :min="0"
                    :max="0.9"
                    :step="0.02"
                    label
                    :label-value="`${Math.round((extractionSegmentOverlap || 0) * 100)}%`"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>
      </km-section>
    </div>

    <!-- Field Definition Dialog -->
    <metadata-field-dialog
      :show-dialog="showFieldDialog"
      :field="editingField"
      :existing-field-names="definedFieldNames"
      :sources="sources"
      @update:show-dialog="showFieldDialog = $event"
      @cancel="showFieldDialog = false"
      @save="onFieldSave"
    />
  </div>
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import { useQuasar } from 'quasar'
import { computed, onMounted, ref, watch } from 'vue'
import { useStore } from 'vuex'
import { KgDropdownField, KgFieldRow } from '../common'
import { type SourceRow } from '../Sources/models'
import MetadataFieldDialog from './MetadataFieldDialog.vue'
import MetadataFieldsTable from './MetadataFieldsTable.vue'
import { DiscoveredMetadataField, MetadataFieldDefinition, MetadataFieldRow, MetadataOrigin, MetadataValueType, PRESET_FIELDS } from './models'

const props = defineProps<{
  graphId: string
  graphDetails: Record<string, any>
}>()

const emit = defineEmits<{
  (e: 'refresh'): void
  (e: 'unsaved-change', value: boolean): void
}>()

const store = useStore()
const $q = useQuasar()

// Extraction settings
type MetadataExtractionApproach = 'disabled' | 'chunks' | 'document'

const extractionApproach = ref<MetadataExtractionApproach>('disabled')
const extractionPromptTemplateSystemName = ref<string>('')
const extractionSegmentSize = ref<number>(18000)
const extractionSegmentOverlap = ref<number>(0.1)

const extractionApproachOptions: Array<{
  label: string
  value: MetadataExtractionApproach
  description: string
}> = [
  {
    label: 'Disabled',
    value: 'disabled',
    description: 'AI extraction is turned off. Metadata will only come from document properties and sources.',
  },
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

// Prompt templates (admin API)
const promptTemplateOptions = ref<any[]>([])
const loadingPromptTemplates = ref(false)

const loadPromptTemplates = async () => {
  loadingPromptTemplates.value = true
  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
    const response = await fetchData({
      endpoint,
      service: 'prompt_templates',
      method: 'GET',
      credentials: 'include',
    })
    if (response.ok) {
      const data = await response.json()
      promptTemplateOptions.value = Array.isArray(data?.items) ? data.items : []
    } else {
      promptTemplateOptions.value = []
    }
  } catch (error) {
    console.error('Error loading prompt templates:', error)
    promptTemplateOptions.value = []
  } finally {
    loadingPromptTemplates.value = false
  }
}

// Defined fields
const definedFields = ref<MetadataFieldDefinition[]>([])
const showFieldDialog = ref(false)
const editingField = ref<MetadataFieldDefinition | null>(null)

// Sources (for per-source overrides)
const sources = ref<SourceRow[]>([])

// All metadata values
const allMetadataValues = ref<MetadataFieldRow[]>([])
const loadingValues = ref(false)

// State tracking
const saving = ref(false)
const originalState = ref<string>('')

// Manual extraction run state
const runningExtraction = ref(false)

// Field names for select
const definedFieldNames = computed(() => definedFields.value.map((f) => f.name))

// Available presets (not already defined)
const availablePresets = computed(() => {
  const existingNames = new Set(definedFieldNames.value)
  return PRESET_FIELDS.filter((p) => !existingNames.has(p.name!))
})

// Undefined fields (discovered but not in schema)
const undefinedFields = computed(() => {
  return allMetadataValues.value.filter((f) => !f.is_defined)
})

// Check for unsaved changes
const hasChanges = computed(() => {
  const currentState = JSON.stringify({
    extraction: {
      approach: extractionApproach.value,
      prompt_template_system_name: extractionPromptTemplateSystemName.value,
      segment_size: extractionSegmentSize.value,
      segment_overlap: extractionSegmentOverlap.value,
    },
    definedFields: definedFields.value,
  })
  return currentState !== originalState.value
})

// Initialize from graph settings
const initializeFromSettings = () => {
  const settings = props.graphDetails?.settings?.metadata || {}

  const extraction = settings.extraction || {}
  const approachRaw = String(extraction?.approach || '').trim()
  const enabledLegacy = !!extraction?.enabled

  if (approachRaw === 'disabled' || approachRaw === 'chunks' || approachRaw === 'document') {
    extractionApproach.value = approachRaw as MetadataExtractionApproach
  } else {
    // Backward compatibility: old config only had enabled=true/false.
    extractionApproach.value = enabledLegacy ? 'chunks' : 'disabled'
  }

  // Prompt template: prefer new key; fall back to legacy prompt_template if present.
  extractionPromptTemplateSystemName.value = String(extraction?.prompt_template_system_name || extraction?.prompt_template || '').trim()

  const sizeRaw = Number(extraction?.segment_size)
  extractionSegmentSize.value = Number.isFinite(sizeRaw) && sizeRaw > 0 ? sizeRaw : 18000

  const overlapRaw = Number(extraction?.segment_overlap)
  extractionSegmentOverlap.value = Number.isFinite(overlapRaw) ? Math.min(Math.max(overlapRaw, 0), 0.9) : 0.1
  // Strip legacy/unused flags that might still exist in persisted configs
  definedFields.value = (settings.field_definitions || []).map((f: any) => {
    const { is_searchable, is_filterable, ...rest } = f || {}
    return rest as MetadataFieldDefinition
  })

  captureOriginalState()
  syncDefinitionsToValues()
}

const captureOriginalState = () => {
  originalState.value = JSON.stringify({
    extraction: {
      approach: extractionApproach.value,
      prompt_template_system_name: extractionPromptTemplateSystemName.value,
      segment_size: extractionSegmentSize.value,
      segment_overlap: extractionSegmentOverlap.value,
    },
    definedFields: definedFields.value,
  })
}

const canRunExtraction = computed(() => {
  return extractionApproach.value !== 'disabled' && !!String(extractionPromptTemplateSystemName.value || '').trim() && !loadingPromptTemplates.value
})

const runExtraction = async () => {
  if (!canRunExtraction.value) return
  runningExtraction.value = true
  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
    const payload = {
      approach: extractionApproach.value,
      prompt_template_system_name: String(extractionPromptTemplateSystemName.value || '').trim(),
      segment_size: extractionSegmentSize.value,
      segment_overlap: extractionSegmentOverlap.value,
    }
    const res = await fetchData({
      endpoint,
      service: `knowledge_graphs/${props.graphId}/metadata/extract`,
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })

    if (!res.ok) {
      $q.notify({ type: 'negative', message: 'Failed to start extraction', position: 'top' })
      return
    }

    const data: any = await res.json().catch(() => ({}))
    const approach = String(data?.approach || extractionApproach.value)
    const docs = Number(data?.processed_documents || 0)
    const chunks = Number(data?.processed_chunks || 0)
    const errors = Number(data?.errors || 0)
    const message =
      approach === 'chunks'
        ? `Extraction completed: ${docs} documents updated, ${chunks} chunks processed${errors ? ` (${errors} errors)` : ''}.`
        : `Extraction completed: ${docs} documents processed${errors ? ` (${errors} errors)` : ''}.`

    $q.notify({ type: 'positive', message, position: 'top', textColor: 'black', timeout: 2500 })
    await fetchMetadataValues()
  } catch (error) {
    console.error('Error running extraction:', error)
    $q.notify({ type: 'negative', message: 'Error running extraction', position: 'top' })
  } finally {
    runningExtraction.value = false
  }
}

// Fetch aggregated metadata values
const fetchMetadataValues = async () => {
  loadingValues.value = true

  type ApiSourceLink = {
    id: string
    name: string
    type: string
  }

  type ApiDiscoveredMetadataField = {
    id?: string
    name?: string
    inferred_type?: string | null
    origins?: string[] | null
    sample_values?: string[] | null
    value_count?: number | null
    sources?: ApiSourceLink[] | null
  }

  const toDisplayName = (fieldName: string) => {
    const s = String(fieldName || '').trim()
    if (!s) return ''
    return s
      .split(/[_-]+/g)
      .filter(Boolean)
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(' ')
  }

  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
    const response: any = await fetchData({
      endpoint,
      service: `knowledge_graphs/${props.graphId}/metadata/discovered`,
      method: 'GET',
      credentials: 'include',
    })

    if (response?.ok) {
      const data = (await response.json()) as ApiDiscoveredMetadataField[]
      const rows = Array.isArray(data) ? data : []
      allMetadataValues.value = rows
        .filter((f) => !!f?.name)
        .map((f) => {
          const name = String(f.name || '').trim()
          return {
            id: String(f.id || name),
            name,
            display_name: toDisplayName(name),
            description: '',
            value_type: (f.inferred_type || 'string') as MetadataValueType,
            origins: (Array.isArray(f.origins) ? f.origins : []) as MetadataOrigin[],
            sources: Array.isArray(f.sources) ? f.sources : [],
            is_defined: definedFieldNames.value.includes(name),
            sample_values: Array.isArray(f.sample_values) ? f.sample_values : [],
          } as MetadataFieldRow
        })
    } else {
      allMetadataValues.value = []
    }
  } catch (error) {
    console.error('Error fetching metadata values:', error)
    allMetadataValues.value = []
  } finally {
    loadingValues.value = false
    syncDefinitionsToValues()
  }
}

const fetchSources = async () => {
  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
    const response = await fetchData({
      endpoint,
      service: `knowledge_graphs/${props.graphId}/sources`,
      method: 'GET',
      credentials: 'include',
    })
    if (response.ok) {
      sources.value = await response.json()
    } else {
      sources.value = []
    }
  } catch (error) {
    console.error('Error fetching sources:', error)
    sources.value = []
  }
}

// Save settings
const saveSettings = async () => {
  if (!hasChanges.value) return
  saving.value = true
  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
    const fieldDefinitions = definedFields.value.map((f: any) => {
      const { is_searchable, is_filterable, ...rest } = f || {}
      return rest as MetadataFieldDefinition
    })
    const payload = {
      settings: {
        ...(props.graphDetails?.settings || {}),
        metadata: {
          extraction: {
            enabled: extractionApproach.value !== 'disabled',
            approach: extractionApproach.value,
            prompt_template_system_name: extractionPromptTemplateSystemName.value || undefined,
            segment_size: extractionSegmentSize.value,
            segment_overlap: extractionSegmentOverlap.value,
          },
          field_definitions: fieldDefinitions,
        },
      },
    }

    const res = await fetchData({
      endpoint,
      service: `knowledge_graphs/${props.graphId}`,
      method: 'PATCH',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })

    if (!res.ok) {
      $q.notify({ type: 'negative', message: 'Failed to save settings', position: 'top' })
      return
    }

    captureOriginalState()
    emit('refresh')
    $q.notify({ type: 'positive', message: 'Settings saved successfully', position: 'top', textColor: 'black', timeout: 1500 })
  } catch (error) {
    console.error('Error saving metadata settings:', error)
    $q.notify({ type: 'negative', message: 'Error saving settings', position: 'top' })
  } finally {
    saving.value = false
  }
}

const discardChanges = () => {
  initializeFromSettings()
}

// Field dialog
const openFieldDialog = (field?: MetadataFieldDefinition) => {
  editingField.value = field || null
  showFieldDialog.value = true
}

const openFieldDialogFromDiscovered = (discovered: MetadataFieldRow | DiscoveredMetadataField) => {
  editingField.value = {
    id: '',
    name: discovered.name,
    display_name: discovered.name
      .split('_')
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(' '),
    description: '',
    value_type: (discovered as MetadataFieldRow).value_type || 'string',
    is_multiple: false,
    is_required: false,
  }
  showFieldDialog.value = true
}

const onFieldSave = (field: MetadataFieldDefinition) => {
  const idx = definedFields.value.findIndex((f) => f.id === field.id)
  if (idx !== -1) {
    definedFields.value[idx] = field
  } else {
    definedFields.value.push(field)
  }
  showFieldDialog.value = false
  syncDefinitionsToValues()
}

const confirmDeleteField = (field: MetadataFieldDefinition) => {
  $q.dialog({
    title: 'Delete Field Definition',
    message: `Are you sure you want to delete the field "${field.display_name || field.name}"? This won't delete existing metadata values.`,
    cancel: true,
    persistent: true,
    ok: { color: 'negative', label: 'Delete', flat: true },
  }).onOk(() => {
    definedFields.value = definedFields.value.filter((f) => f.id !== field.id)
    syncDefinitionsToValues()
  })
}

const addPresetField = (preset: Partial<MetadataFieldDefinition>) => {
  const field: MetadataFieldDefinition = {
    id: crypto.randomUUID(),
    name: preset.name!,
    display_name: preset.display_name || preset.name!,
    description: preset.description || '',
    value_type: preset.value_type || 'string',
    is_multiple: preset.is_multiple ?? false,
    is_required: preset.is_required ?? false,
    allowed_values: preset.allowed_values ? preset.allowed_values.map((v) => ({ ...v })) : undefined,
    default_value: preset.default_value,
    default_values: preset.default_values ? [...preset.default_values] : undefined,
  }
  definedFields.value.push(field)
  syncDefinitionsToValues()
}

const defineAllDiscovered = () => {
  const toDefine = undefinedFields.value
  if (toDefine.length === 0) return

  toDefine.forEach((field) => {
    const newField: MetadataFieldDefinition = {
      id: crypto.randomUUID(),
      name: field.name,
      display_name: field.name
        .split('_')
        .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
        .join(' '),
      description: '',
      value_type: field.value_type || 'string',
      is_multiple: false,
      is_required: false,
    }
    definedFields.value.push(newField)
  })
  syncDefinitionsToValues()
}

const syncDefinitionsToValues = () => {
  if (!allMetadataValues.value?.length) return
  const defsByName = new Map(definedFields.value.map((f) => [f.name, f]))
  allMetadataValues.value.forEach((row) => {
    const def = defsByName.get(row.name)
    row.is_defined = !!def
    if (def?.display_name) {
      row.display_name = def.display_name
    }
  })
}

// Watch for changes
watch(hasChanges, (val) => {
  emit('unsaved-change', val)
})

watch(showFieldDialog, (open) => {
  if (open) fetchSources()
})

watch(
  () => props.graphDetails,
  () => {
    if (props.graphDetails) {
      initializeFromSettings()
    }
  },
  { immediate: true, deep: true }
)

onMounted(() => {
  fetchMetadataValues()
  fetchSources()
  loadPromptTemplates()
})

// Expose methods for parent
defineExpose({
  save: saveSettings,
  discard: discardChanges,
})
</script>

<style scoped>
/* Extraction Approach Tiles - Clean Radio Style */
.kg-extraction-tile {
  display: flex;
  flex-direction: column;
  padding: 16px 18px;
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 4px;
  cursor: pointer;
  background: #fff;
  transition: all 0.15s ease;
  height: 100%;
  min-height: 100px;
}

.kg-extraction-tile:hover {
  border-color: rgba(0, 0, 0, 0.24);
  background: #fafafa;
}

.kg-extraction-tile:focus-visible {
  outline: 2px solid var(--q-primary);
  outline-offset: 2px;
}

.kg-extraction-tile--selected {
  border-color: var(--q-primary);
  background: rgba(var(--q-primary-rgb, 25, 118, 210), 0.04);
}

.kg-extraction-tile--selected:hover {
  border-color: var(--q-primary);
  background: rgba(var(--q-primary-rgb, 25, 118, 210), 0.06);
}

.kg-extraction-tile__header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 8px;
}

.kg-extraction-tile__radio {
  width: 18px;
  height: 18px;
  border: 2px solid rgba(0, 0, 0, 0.38);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.15s ease;
}

.kg-extraction-tile__radio--checked {
  border-color: var(--q-primary);
}

.kg-extraction-tile__radio-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: var(--q-primary);
}

.kg-extraction-tile__label {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  line-height: 1.3;
}

.kg-extraction-tile--selected .kg-extraction-tile__label {
  color: var(--q-primary);
}

.kg-extraction-tile__description {
  font-size: 13px;
  color: #6b7280;
  line-height: 1.5;
  padding-left: 28px;
}

/* Action buttons */
.kg-action-btn {
  font-size: 13px;
  height: 34px;
  min-height: 34px;
  padding-left: 12px;
  padding-right: 12px;
}
</style>

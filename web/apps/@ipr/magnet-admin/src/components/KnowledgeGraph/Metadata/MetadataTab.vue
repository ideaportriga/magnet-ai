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
      <div class="col-auto">
        <q-btn-dropdown
          no-caps
          color="primary"
          label="Preset"
          dense
          class="preset-selector q-pl-12"
          dropdown-icon="expand_more"
          content-class="preset-dropdown-menu"
          :disable="availablePresets.length === 0"
          @click.stop
        >
          <q-list dense class="preset-dropdown-list">
            <q-item
              v-for="preset in availablePresets"
              :key="preset.name"
              v-close-popup
              clickable
              class="preset-dropdown-item"
              @click="addPresetField(preset)"
            >
              <q-item-section>
                <q-item-label class="preset-label">{{ preset.display_name || preset.name }}</q-item-label>
                <q-item-label v-if="preset.description" caption class="preset-caption">{{ preset.description }}</q-item-label>
              </q-item-section>
            </q-item>
            <q-item v-if="availablePresets.length === 0" disable>
              <q-item-section class="text-grey-6">All presets added</q-item-section>
            </q-item>
          </q-list>
        </q-btn-dropdown>
      </div>
    </div>

    <q-separator class="q-my-md" />

    <div class="column q-gap-32">
      <metadata-fields-table
        :defined-fields="definedFields"
        :discovered-fields="allMetadataValues"
        :extracted-fields="extractedFields"
        :discarded-field-names="discardedFieldNames"
        :sources="sources"
        :loading="loadingValues"
        :can-run-extraction="canRunExtraction"
        :running-extraction="runningExtraction"
        @add-field="openFieldDialog()"
        @add-extraction-field="openSmartExtractionFieldDialog()"
        @edit-extraction-field="openSmartExtractionFieldDialog"
        @delete-extraction-field="confirmDeleteExtractedField"
        @edit-field="openFieldDialog"
        @delete-field="confirmDeleteField"
        @promote-field="openPromoteFieldDialog"
        @discard-field="discardField"
        @restore-field="restoreField"
        @run-extraction="runExtraction"
        @open-extraction-settings="showExtractionDialog = true"
        @quick-create-field="quickCreateField"
        @quick-replace-field="quickReplaceField"
        @quick-create-from-extraction="quickCreateFromExtraction"
        @quick-replace-from-extraction="quickReplaceFromExtraction"
      />
    </div>

    <!-- Field Definition Dialog -->
    <metadata-field-dialog
      :show-dialog="showFieldDialog"
      :field="editingField"
      :existing-field-names="definedFieldNames"
      :discovered-fields="allMetadataValues"
      :sources="sources"
      :extracted-fields="extractedFields"
      @update:show-dialog="showFieldDialog = $event"
      @cancel="showFieldDialog = false"
      @save="onFieldSave"
    />

    <!-- Smart Extraction Field Dialog -->
    <smart-extraction-field-dialog
      :show-dialog="showSmartExtractionFieldDialog"
      :field="editingSmartExtractionField"
      :existing-field-names="extractedFieldNames"
      @update:show-dialog="showSmartExtractionFieldDialog = $event"
      @cancel="showSmartExtractionFieldDialog = false"
      @save="onSmartExtractionFieldSave"
    />

    <!-- Smart Extraction Settings Dialog -->
    <smart-extraction-settings-dialog
      :show-dialog="showExtractionDialog"
      :settings="extractionSettings"
      :prompt-template-options="promptTemplateOptions"
      :loading-prompt-templates="loadingPromptTemplates"
      @update:show-dialog="showExtractionDialog = $event"
      @cancel="showExtractionDialog = false"
      @save="onExtractionSettingsSave"
    />

    <!-- Promote Field Dialog -->
    <promote-field-dialog
      :show-dialog="showPromoteDialog"
      :discovered-field="promotingField"
      :existing-fields="definedFields"
      @update:show-dialog="showPromoteDialog = $event"
      @create-new="onPromoteCreateNew"
      @link-existing="onPromoteLinkExisting"
    />
  </div>
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import { useQuasar } from 'quasar'
import { computed, onMounted, ref, watch } from 'vue'
import { useStore } from 'vuex'
import { type SourceRow } from '../Sources/models'
import MetadataFieldDialog from './MetadataFieldDialog.vue'
import MetadataFieldsTable from './MetadataFieldsTable.vue'
import {
  DiscoveredMetadataField,
  MetadataDiscoveredField,
  MetadataExtractedField,
  MetadataFieldDefinition,
  MetadataFieldSourceValueResolution,
  MetadataFieldValueSourceStep,
  MetadataOrigin,
  MetadataValueType,
  PRESET_FIELDS,
  PresetFieldDefinition,
} from './models'
import PromoteFieldDialog from './PromoteFieldDialog.vue'
import SmartExtractionFieldDialog, { type SmartExtractionFieldDefinition } from './SmartExtractionFieldDialog.vue'
import SmartExtractionSettingsDialog, { type MetadataExtractionApproach, type SmartExtractionSettings } from './SmartExtractionSettingsDialog.vue'

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
const extractionApproach = ref<MetadataExtractionApproach>('document')
const extractionPromptTemplateSystemName = ref<string>('')
const extractionSegmentSize = ref<number>(18000)
const extractionSegmentOverlap = ref<number>(0.1)

// Extraction dialog state
const showExtractionDialog = ref(false)

// Computed extraction settings for dialog
const extractionSettings = computed<SmartExtractionSettings>(() => ({
  approach: extractionApproach.value,
  prompt_template_system_name: extractionPromptTemplateSystemName.value,
  segment_size: extractionSegmentSize.value,
  segment_overlap: extractionSegmentOverlap.value,
}))

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

// Smart extraction field dialog state
const showSmartExtractionFieldDialog = ref(false)
const editingSmartExtractionField = ref<SmartExtractionFieldDefinition | null>(null)

// Smart extraction fields (persisted separately via /metadata/extracted)
const extractedFields = ref<MetadataExtractedField[]>([])

// Promote field dialog state
const showPromoteDialog = ref(false)
const promotingField = ref<MetadataDiscoveredField | null>(null)

// Sources (for per-source overrides)
const sources = ref<SourceRow[]>([])

// All metadata values
const allMetadataValues = ref<MetadataDiscoveredField[]>([])
const loadingValues = ref(false)

// Discarded field names (persisted per knowledge graph)
const discardedFieldNames = ref<string[]>([])

// State tracking
const saving = ref(false)
const originalState = ref<string>('')
const autoSaveEnabled = ref(false)
const baseSettings = ref<Record<string, any>>({})
let autoSaveTimer: number | undefined
let autoSaveAfterInFlight = false
let refreshTimer: number | undefined

// Manual extraction run state
const runningExtraction = ref(false)

// Field names for select
const definedFieldNames = computed(() => definedFields.value.map((f) => f.name))
const extractedFieldNames = computed(() => extractedFields.value.map((f) => f.name))

// Available presets (not already defined in schema or extraction)
const availablePresets = computed(() => {
  const existingSchemaNames = new Set(definedFieldNames.value)
  const existingExtractionNames = new Set(extractedFieldNames.value)
  return PRESET_FIELDS.filter((p) => !existingSchemaNames.has(p.name) && !existingExtractionNames.has(p.name))
})

// Check for unsaved changes
const currentStateJson = computed(() =>
  JSON.stringify({
    extraction: {
      approach: extractionApproach.value,
      prompt_template_system_name: extractionPromptTemplateSystemName.value,
      segment_size: extractionSegmentSize.value,
      segment_overlap: extractionSegmentOverlap.value,
    },
    definedFields: definedFields.value,
    discardedFieldNames: discardedFieldNames.value,
  })
)

const hasChanges = computed(() => currentStateJson.value !== originalState.value)

// Initialize from graph settings
const initializeFromSettings = () => {
  autoSaveEnabled.value = false
  if (autoSaveTimer) window.clearTimeout(autoSaveTimer)
  autoSaveAfterInFlight = false

  // Keep a local copy of the full settings object. The backend treats `settings` as a full replacement.
  // This prevents us from accidentally dropping other settings keys when we persist metadata changes.
  try {
    baseSettings.value = JSON.parse(JSON.stringify(props.graphDetails?.settings || {}))
  } catch {
    baseSettings.value = (props.graphDetails?.settings || {}) as Record<string, any>
  }

  const settings = props.graphDetails?.settings?.metadata || {}

  const extraction = settings.extraction || {}
  const approachRaw = String(extraction?.approach || '').trim()

  // Read approach from settings, default to 'document' if not present or invalid
  if (approachRaw === 'chunks' || approachRaw === 'document') {
    extractionApproach.value = approachRaw as MetadataExtractionApproach
  } else {
    extractionApproach.value = 'document'
  }

  // Prompt template: prefer new key; fall back to legacy prompt_template if present.
  extractionPromptTemplateSystemName.value = String(extraction?.prompt_template_system_name || extraction?.prompt_template || '').trim()

  const sizeRaw = Number(extraction?.segment_size)
  extractionSegmentSize.value = Number.isFinite(sizeRaw) && sizeRaw > 0 ? sizeRaw : 18000

  const overlapRaw = Number(extraction?.segment_overlap)
  extractionSegmentOverlap.value = Number.isFinite(overlapRaw) ? Math.min(Math.max(overlapRaw, 0), 0.9) : 0.1
  // Strip legacy/unused flags that might still exist in persisted configs
  definedFields.value = (settings.field_definitions || []).map((f: any) => {
    const {
      is_searchable,
      is_filterable,
      value_type,
      is_multiple,
      allowed_values,
      default_value,
      default_values,
      llm_extraction_hint,
      source_overrides,
      created_at,
      updated_at,
      ...rest
    } = f || {}
    return rest as MetadataFieldDefinition
  })

  // Load discarded field names
  discardedFieldNames.value = Array.isArray(settings.discarded_field_names) ? settings.discarded_field_names : []

  // Snapshot as "saved" baseline (auto-save will persist changes from here).
  originalState.value = currentStateJson.value
  syncDefinitionsToValues()
  autoSaveEnabled.value = true
  emit('unsaved-change', false)
}

const scheduleRefresh = () => {
  if (refreshTimer) window.clearTimeout(refreshTimer)
  refreshTimer = window.setTimeout(() => emit('refresh'), 300)
}

const scheduleAutoSave = () => {
  if (!autoSaveEnabled.value) return
  if (autoSaveTimer) window.clearTimeout(autoSaveTimer)
  autoSaveTimer = window.setTimeout(() => {
    void saveSettings()
  }, 250)
}

const canRunExtraction = computed(() => {
  return !!String(extractionPromptTemplateSystemName.value || '').trim() && !loadingPromptTemplates.value
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
    origin?: string | null
    sample_values?: string[] | null
    value_count?: number | null
    source?: ApiSourceLink | null
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
          const origin = String(f.origin || '').trim()
          const src = f.source
          const source = src
            ? {
                id: String(src.id || ''),
                name: String(src.name || ''),
                type: String(src.type || ''),
              }
            : null
          return {
            id: String(f.id || name),
            name,
            description: '',
            value_type: (f.inferred_type || 'string') as MetadataValueType,
            origin: (origin || null) as MetadataOrigin | null,
            source,
            is_defined: definedFieldNames.value.includes(name),
            sample_values: Array.isArray(f.sample_values) ? f.sample_values : [],
          } as MetadataDiscoveredField
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

// Fetch configured smart extraction fields
const fetchExtractedFields = async () => {
  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
    const response: any = await fetchData({
      endpoint,
      service: `knowledge_graphs/${props.graphId}/metadata/extracted`,
      method: 'GET',
      credentials: 'include',
    })

    if (response?.ok) {
      const data = await response.json()
      const rows = Array.isArray(data) ? data : []
      extractedFields.value = rows
        .filter((r: any) => !!r?.name)
        .map((r: any) => ({
          id: String(r.id || crypto.randomUUID()),
          name: String(r.name || '').trim(),
          value_type: (String(r.value_type || 'string') as any) || 'string',
          is_multiple: !!r.is_multiple,
          allowed_values: Array.isArray(r.allowed_values) ? r.allowed_values : undefined,
          llm_extraction_hint: r.llm_extraction_hint ? String(r.llm_extraction_hint) : undefined,
          sample_values: Array.isArray(r.sample_values) ? r.sample_values : undefined,
          value_count: Number.isFinite(Number(r.value_count)) ? Number(r.value_count) : undefined,
          created_at: r.created_at ? String(r.created_at) : undefined,
          updated_at: r.updated_at ? String(r.updated_at) : undefined,
        })) as MetadataExtractedField[]
    } else {
      extractedFields.value = []
    }
  } catch (error) {
    console.error('Error fetching extracted metadata fields:', error)
    extractedFields.value = []
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
  const snapshotJson = currentStateJson.value
  if (snapshotJson === originalState.value) return

  if (saving.value) {
    autoSaveAfterInFlight = true
    return
  }

  saving.value = true
  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin

    const snapshot = JSON.parse(snapshotJson) as {
      extraction: {
        approach: MetadataExtractionApproach
        prompt_template_system_name: string
        segment_size: number
        segment_overlap: number
      }
      definedFields: MetadataFieldDefinition[]
      discardedFieldNames: string[]
    }

    const fieldDefinitions = (snapshot.definedFields || []).map((f: any) => {
      const { is_searchable, is_filterable, ...rest } = f || {}
      return rest as MetadataFieldDefinition
    })

    const payload = {
      settings: {
        ...(baseSettings.value || {}),
        metadata: {
          extraction: {
            enabled: !!snapshot.extraction.prompt_template_system_name,
            approach: snapshot.extraction.approach,
            prompt_template_system_name: snapshot.extraction.prompt_template_system_name || undefined,
            segment_size: snapshot.extraction.segment_size,
            segment_overlap: snapshot.extraction.segment_overlap,
          },
          field_definitions: fieldDefinitions,
          discarded_field_names: snapshot.discardedFieldNames,
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

    // Persist baseline as the exact snapshot we sent (user may have changed state while request was in-flight).
    originalState.value = snapshotJson
    baseSettings.value = payload.settings
    // Only refresh the parent graph details once we're caught up; otherwise we'd fetch intermediate state.
    if (currentStateJson.value === snapshotJson) {
      scheduleRefresh()
    }
  } catch (error) {
    console.error('Error saving metadata settings:', error)
    $q.notify({ type: 'negative', message: 'Error saving settings', position: 'top' })
  } finally {
    saving.value = false
    // If state changed while we were saving, immediately schedule another save.
    if (autoSaveAfterInFlight || currentStateJson.value !== originalState.value) {
      autoSaveAfterInFlight = false
      scheduleAutoSave()
    }
  }
}

// Auto-save: persist any changes to schema/discarded/extraction settings.
watch(
  currentStateJson,
  () => {
    if (!autoSaveEnabled.value) return
    scheduleAutoSave()
  },
  { deep: false }
)

// Field dialog
const openFieldDialog = (field?: MetadataFieldDefinition) => {
  editingField.value = field || null
  showFieldDialog.value = true
}

// Smart extraction field dialog
const openSmartExtractionFieldDialog = (field?: MetadataExtractedField) => {
  editingSmartExtractionField.value = (field as any) || null
  showSmartExtractionFieldDialog.value = true
}

const openFieldDialogFromDiscovered = (discovered: MetadataDiscoveredField | DiscoveredMetadataField) => {
  const row = discovered as MetadataDiscoveredField

  const sourceId = String(row?.source?.id || '').trim()
  const origin = row?.origin || null

  const chain: MetadataFieldValueSourceStep[] = []
  if (origin === 'file' || origin === 'source') {
    chain.push({ kind: origin, field_name: row.name })
  } else if (origin === 'llm') {
    chain.push({ kind: 'llm' })
  }

  const source_value_resolution: MetadataFieldSourceValueResolution[] | undefined =
    sourceId && chain.length ? [{ source_id: sourceId, chain }] : undefined

  editingField.value = {
    id: '',
    name: row.name,
    display_name: row.name
      .split('_')
      .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
      .join(' '),
    description: '',
    source_value_resolution,
  }
  showFieldDialog.value = true
}

// Promote field dialog
const openPromoteFieldDialog = (row: MetadataDiscoveredField) => {
  promotingField.value = row
  showPromoteDialog.value = true
}

const onPromoteCreateNew = (row: MetadataDiscoveredField) => {
  openFieldDialogFromDiscovered(row)
}

const onPromoteLinkExisting = (payload: { discovered: MetadataDiscoveredField; targetFieldId: string }) => {
  const { discovered: row, targetFieldId } = payload
  const targetField = definedFields.value.find((f) => f.id === targetFieldId)
  if (!targetField) return

  const sourceId = String(row?.source?.id || '').trim()
  const origin = row?.origin || null

  const newStep: MetadataFieldValueSourceStep = { kind: origin || 'file', field_name: row.name }
  if (origin === 'llm') {
    newStep.kind = 'llm'
    newStep.field_name = row.name
  }

  // Build or update the source_value_resolution
  const existingResolutions = targetField.source_value_resolution || []

  if (sourceId) {
    // Find existing resolution for this source, or create new one
    const existingIdx = existingResolutions.findIndex((r) => r.source_id === sourceId)
    if (existingIdx !== -1) {
      // Add step to beginning of existing chain (highest priority)
      const existing = existingResolutions[existingIdx]
      const chainHasStep = existing.chain.some((s) => s.kind === newStep.kind && s.field_name === newStep.field_name)
      if (!chainHasStep) {
        existing.chain.unshift(newStep)
      }
    } else {
      // Create new resolution for this source
      existingResolutions.push({ source_id: sourceId, chain: [newStep] })
    }
  } else {
    // No source - add to all existing resolutions or create a default one
    if (existingResolutions.length === 0) {
      existingResolutions.push({ source_id: '*', chain: [newStep] })
    } else {
      existingResolutions.forEach((r) => {
        const chainHasStep = r.chain.some((s) => s.kind === newStep.kind && s.field_name === newStep.field_name)
        if (!chainHasStep) {
          r.chain.unshift(newStep)
        }
      })
    }
  }

  targetField.source_value_resolution = existingResolutions

  // Auto-remove from discarded when linking a field
  if (discardedFieldNames.value.includes(row.name)) {
    discardedFieldNames.value = discardedFieldNames.value.filter((n) => n !== row.name)
  }

  syncDefinitionsToValues()
  $q.notify({
    type: 'positive',
    message: `Linked "${row.name}" to "${targetField.display_name || targetField.name}"`,
    position: 'top',
    textColor: 'black',
    timeout: 2000,
  })
}

const onFieldSave = (field: MetadataFieldDefinition) => {
  const idx = definedFields.value.findIndex((f) => f.id === field.id)
  if (idx !== -1) {
    definedFields.value[idx] = field
  } else {
    definedFields.value.push(field)
  }
  // Auto-remove from discarded when defining a field
  if (discardedFieldNames.value.includes(field.name)) {
    discardedFieldNames.value = discardedFieldNames.value.filter((n) => n !== field.name)
  }
  showFieldDialog.value = false
  syncDefinitionsToValues()
}

const onSmartExtractionFieldSave = async (field: SmartExtractionFieldDefinition) => {
  const name = String(field?.name || '').trim()
  if (!name) return

  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
    const payload = {
      name,
      value_type: field.value_type || 'string',
      is_multiple: !!field.is_multiple,
      allowed_values: field.allowed_values?.length ? field.allowed_values : undefined,
      llm_extraction_hint: field.llm_extraction_hint,
    }

    const res = await fetchData({
      endpoint,
      service: `knowledge_graphs/${props.graphId}/metadata/extracted`,
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })

    if (!res.ok) {
      $q.notify({ type: 'negative', message: 'Failed to save extraction field', position: 'top' })
      return
    }

    showSmartExtractionFieldDialog.value = false
    await fetchExtractedFields()
    $q.notify({ type: 'positive', message: 'Extraction field saved', position: 'top', textColor: 'black', timeout: 1500 })
  } catch (error) {
    console.error('Error saving extracted metadata field:', error)
    $q.notify({ type: 'negative', message: 'Error saving extraction field', position: 'top' })
  }
}

const confirmDeleteExtractedField = (field: MetadataExtractedField) => {
  const name = String(field?.name || '').trim()
  if (!name) return
  $q.dialog({
    title: 'Delete Extraction Field',
    message: `Delete the extraction field \"${name}\"?`,
    cancel: true,
    persistent: true,
    ok: { color: 'negative', label: 'Delete', flat: true },
  }).onOk(async () => {
    try {
      const endpoint = store.getters.config.api.aiBridge.urlAdmin
      const res = await fetchData({
        endpoint,
        service: `knowledge_graphs/${props.graphId}/metadata/extracted/${name}`,
        method: 'DELETE',
        credentials: 'include',
      })
      if (!res.ok) {
        $q.notify({ type: 'negative', message: 'Failed to delete extraction field', position: 'top' })
        return
      }
      await fetchExtractedFields()
      $q.notify({ type: 'positive', message: 'Extraction field deleted', position: 'top', textColor: 'black', timeout: 1500 })
    } catch (error) {
      console.error('Error deleting extracted metadata field:', error)
      $q.notify({ type: 'negative', message: 'Error deleting extraction field', position: 'top' })
    }
  })
}

const onExtractionSettingsSave = (settings: SmartExtractionSettings) => {
  extractionApproach.value = settings.approach
  extractionPromptTemplateSystemName.value = settings.prompt_template_system_name
  extractionSegmentSize.value = settings.segment_size
  extractionSegmentOverlap.value = settings.segment_overlap
  showExtractionDialog.value = false
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

const addPresetField = async (preset: PresetFieldDefinition) => {
  // 1. Create the schema field definition
  const field: MetadataFieldDefinition = {
    id: crypto.randomUUID(),
    name: preset.name,
    display_name: preset.display_name || preset.name,
    description: preset.description || '',
  }
  definedFields.value.push(field)
  syncDefinitionsToValues()

  // 2. Also create the smart extraction field
  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
    const payload = {
      name: preset.name,
      value_type: preset.value_type || 'string',
      is_multiple: !!preset.is_multiple,
      allowed_values: preset.allowed_values?.length ? preset.allowed_values : undefined,
      llm_extraction_hint: preset.llm_extraction_hint,
    }

    const res = await fetchData({
      endpoint,
      service: `knowledge_graphs/${props.graphId}/metadata/extracted`,
      method: 'POST',
      credentials: 'include',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    })

    if (!res.ok) {
      console.error('Failed to create extraction field for preset')
    } else {
      await fetchExtractedFields()
      $q.notify({
        type: 'positive',
        message: `Added preset field "${preset.display_name || preset.name}" to schema and smart extraction`,
        position: 'top',
        textColor: 'black',
        timeout: 2000,
      })
    }
  } catch (error) {
    console.error('Error creating extraction field for preset:', error)
  }
}

const syncDefinitionsToValues = () => {
  if (!allMetadataValues.value?.length) return
  const defsByName = new Map(definedFields.value.map((f) => [f.name, f]))
  allMetadataValues.value.forEach((row) => {
    const def = defsByName.get(row.name)
    row.is_defined = !!def
  })
}

// Discard/restore field handlers
const discardField = (name: string) => {
  if (!discardedFieldNames.value.includes(name)) {
    discardedFieldNames.value = [...discardedFieldNames.value, name]
  }
}

const restoreField = (name: string) => {
  discardedFieldNames.value = discardedFieldNames.value.filter((n) => n !== name)
}

// Quick field creation/replacement via drag-and-drop
const toDisplayName = (fieldName: string) => {
  const s = String(fieldName || '').trim()
  if (!s) return ''
  return s
    .split(/[_-]+/g)
    .filter(Boolean)
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ')
}

const buildResolutionChain = (row: MetadataDiscoveredField): MetadataFieldSourceValueResolution[] | undefined => {
  const sourceId = String(row?.source?.id || '').trim()
  const origin = row?.origin || null

  const chain: MetadataFieldValueSourceStep[] = []
  if (origin === 'file' || origin === 'source') {
    chain.push({ kind: origin, field_name: row.name })
  } else if (origin === 'llm') {
    chain.push({ kind: 'llm', field_name: row.name })
  }

  if (sourceId && chain.length) {
    return [{ source_id: sourceId, chain }]
  } else if (chain.length) {
    return [{ source_id: '*', chain }]
  }
  return undefined
}

const quickCreateField = (row: MetadataDiscoveredField) => {
  const field: MetadataFieldDefinition = {
    id: crypto.randomUUID(),
    name: row.name,
    display_name: toDisplayName(row.name),
    description: '',
    source_value_resolution: buildResolutionChain(row),
  }
  definedFields.value.push(field)
  // Auto-remove from discarded
  if (discardedFieldNames.value.includes(row.name)) {
    discardedFieldNames.value = discardedFieldNames.value.filter((n) => n !== row.name)
  }
  syncDefinitionsToValues()
  $q.notify({
    type: 'positive',
    message: `Created schema field "${field.display_name || field.name}"`,
    position: 'top',
    textColor: 'black',
    timeout: 1500,
  })
}

const quickReplaceField = (payload: { discovered: MetadataDiscoveredField; target: MetadataFieldDefinition }) => {
  const { discovered: row, target: targetField } = payload
  const idx = definedFields.value.findIndex((f) => f.id === targetField.id)
  if (idx === -1) return

  const sourceId = String(row?.source?.id || '').trim()
  const origin = row?.origin || null

  // Build the new step for this discovered field
  const newStep: MetadataFieldValueSourceStep = { kind: origin || 'file', field_name: row.name }
  if (origin === 'llm') {
    newStep.kind = 'llm'
    newStep.field_name = row.name
  }

  // Get existing resolutions or start fresh
  const existingResolutions = [...(targetField.source_value_resolution || [])]

  if (sourceId) {
    // Find existing resolution for this source, or create new one
    const existingIdx = existingResolutions.findIndex((r) => r.source_id === sourceId)
    if (existingIdx !== -1) {
      // Add step to beginning of existing chain (highest priority) if not already present
      const existing = existingResolutions[existingIdx]
      const chainHasStep = existing.chain.some((s) => s.kind === newStep.kind && s.field_name === newStep.field_name)
      if (!chainHasStep) {
        existing.chain = [newStep, ...existing.chain]
      }
    } else {
      // Create new resolution for this source
      existingResolutions.push({ source_id: sourceId, chain: [newStep] })
    }
  } else {
    // No source - add to wildcard resolution or create one
    const wildcardIdx = existingResolutions.findIndex((r) => r.source_id === '*')
    if (wildcardIdx !== -1) {
      const existing = existingResolutions[wildcardIdx]
      const chainHasStep = existing.chain.some((s) => s.kind === newStep.kind && s.field_name === newStep.field_name)
      if (!chainHasStep) {
        existing.chain = [newStep, ...existing.chain]
      }
    } else {
      existingResolutions.push({ source_id: '*', chain: [newStep] })
    }
  }

  // Update the field with new resolution (keeping original name, display_name, etc.)
  definedFields.value[idx] = {
    ...targetField,
    source_value_resolution: existingResolutions,
  }

  // Auto-remove from discarded
  if (discardedFieldNames.value.includes(row.name)) {
    discardedFieldNames.value = discardedFieldNames.value.filter((n) => n !== row.name)
  }
  syncDefinitionsToValues()
  $q.notify({
    type: 'positive',
    message: `Linked "${row.name}" to "${targetField.display_name || targetField.name}"`,
    position: 'top',
    textColor: 'black',
    timeout: 1500,
  })
}

// Quick field creation/replacement from extraction field via drag-and-drop
const quickCreateFromExtraction = (extractedField: MetadataExtractedField) => {
  // Create resolution entries for all sources
  const llmStep: MetadataFieldValueSourceStep = { kind: 'llm', field_name: extractedField.name }
  const sourceValueResolution: MetadataFieldSourceValueResolution[] =
    sources.value.length > 0 ? sources.value.map((src) => ({ source_id: src.id, chain: [llmStep] })) : [{ source_id: '*', chain: [llmStep] }]

  const field: MetadataFieldDefinition = {
    id: crypto.randomUUID(),
    name: extractedField.name,
    display_name: toDisplayName(extractedField.name),
    description: extractedField.llm_extraction_hint || '',
    source_value_resolution: sourceValueResolution,
  }
  definedFields.value.push(field)
  syncDefinitionsToValues()
  $q.notify({
    type: 'positive',
    message: `Created schema field "${field.display_name || field.name}" from extraction field`,
    position: 'top',
    textColor: 'black',
    timeout: 1500,
  })
}

const quickReplaceFromExtraction = (payload: { extracted: MetadataExtractedField; target: MetadataFieldDefinition }) => {
  const { extracted: extractedField, target: targetField } = payload
  const idx = definedFields.value.findIndex((f) => f.id === targetField.id)
  if (idx === -1) return

  // Build the new step for this extraction field
  const newStep: MetadataFieldValueSourceStep = { kind: 'llm', field_name: extractedField.name }

  // Get existing resolutions or start fresh
  const existingResolutions = [...(targetField.source_value_resolution || [])]

  // Get all source IDs that already have resolutions
  const existingSourceIds = new Set(existingResolutions.map((r) => r.source_id))

  // Add the LLM step to all existing resolutions
  existingResolutions.forEach((resolution) => {
    const chainHasStep = resolution.chain.some((s) => s.kind === newStep.kind && s.field_name === newStep.field_name)
    if (!chainHasStep) {
      resolution.chain = [newStep, ...resolution.chain]
    }
  })

  // Add resolutions for any sources that don't have one yet
  sources.value.forEach((src) => {
    if (!existingSourceIds.has(src.id)) {
      existingResolutions.push({ source_id: src.id, chain: [newStep] })
    }
  })

  // If no sources exist and no resolutions, add a wildcard
  if (existingResolutions.length === 0) {
    existingResolutions.push({ source_id: '*', chain: [newStep] })
  }

  // Update the field with new resolution (keeping original name, display_name, etc.)
  definedFields.value[idx] = {
    ...targetField,
    source_value_resolution: existingResolutions,
  }

  syncDefinitionsToValues()
  $q.notify({
    type: 'positive',
    message: `Linked extraction field "${extractedField.name}" to "${targetField.display_name || targetField.name}"`,
    position: 'top',
    textColor: 'black',
    timeout: 1500,
  })
}

watch(showFieldDialog, (open) => {
  if (open) fetchSources()
})

watch(
  () => props.graphDetails,
  () => {
    if (props.graphDetails) {
      // Always refresh base settings from props so future PATCH payloads preserve all settings keys.
      try {
        baseSettings.value = JSON.parse(JSON.stringify(props.graphDetails?.settings || {}))
      } catch {
        baseSettings.value = (props.graphDetails?.settings || {}) as Record<string, any>
      }

      // Avoid clobbering local in-progress edits with incoming props updates.
      if (saving.value) return
      if (autoSaveEnabled.value && hasChanges.value) return

      initializeFromSettings()
    }
  },
  { immediate: true, deep: true }
)

onMounted(() => {
  fetchMetadataValues()
  fetchExtractedFields()
  fetchSources()
  loadPromptTemplates()
})

// Expose methods for parent
defineExpose({
  refresh: () => {
    fetchMetadataValues()
    fetchExtractedFields()
    fetchSources()
  },
})
</script>

<style scoped>
/* Preset dropdown */
.preset-selector {
  height: 34px;
  min-height: 34px;
  font-size: 14px;
  font-weight: 500;
}

:deep(.preset-dropdown-menu) {
  border-radius: 8px;
  box-shadow:
    0 4px 20px rgba(0, 0, 0, 0.12),
    0 2px 8px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(0, 0, 0, 0.06);
  overflow: hidden;
  min-width: 280px;
}

:deep(.preset-dropdown-list) {
  padding: 4px 0;
}

:deep(.preset-dropdown-item) {
  padding: 8px 14px !important;
  margin: 4px 6px;
  border-radius: 6px;
}

:deep(.preset-dropdown-item:hover) {
  background-color: #f3f4f6;
}

:deep(.preset-label) {
  font-size: 13px;
  font-weight: 500;
  color: #1f2937;
  line-height: 1.3;
}

:deep(.preset-caption) {
  font-size: 11px;
  color: #9ca3af;
  margin-top: 2px;
  line-height: 1.3;
}
</style>

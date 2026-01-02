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
      <!-- Field Definitions -->
      <km-section title="Field Definitions" sub-title="Schema definitions for metadata fields with types, constraints, and validation rules">
        <!-- Actions for non-empty state -->
        <div v-if="definedFields.length > 0" class="row items-center q-gutter-x-sm q-mb-sm">
          <q-space />
          <q-btn no-caps flat color="primary" icon="add" label="Add Field" class="kg-action-btn" @click.stop="openFieldDialog()" />
          <q-btn-dropdown
            no-caps
            flat
            color="primary"
            icon="playlist_add"
            label="Add Preset"
            class="kg-action-btn"
            dropdown-icon="expand_more"
            content-class="kg-preset-dropdown-menu"
            :disable="availablePresets.length === 0"
            @click.stop
          >
            <q-list dense class="kg-preset-dropdown-list">
              <q-item
                v-for="preset in availablePresets"
                :key="preset.name"
                v-close-popup
                clickable
                class="kg-preset-dropdown-item"
                @click="addPresetField(preset)"
              >
                <q-item-section avatar class="kg-preset-icon-section">
                  <div class="kg-preset-icon-wrapper">
                    <q-icon name="playlist_add" size="16px" />
                  </div>
                </q-item-section>
                <q-item-section>
                  <q-item-label class="kg-preset-label">{{ preset.display_name || preset.name }}</q-item-label>
                  <q-item-label v-if="preset.description" caption class="kg-preset-caption">{{ preset.description }}</q-item-label>
                </q-item-section>
              </q-item>
              <q-item v-if="availablePresets.length === 0" disable>
                <q-item-section class="text-grey-6">All presets already added</q-item-section>
              </q-item>
            </q-list>
          </q-btn-dropdown>
        </div>

        <!-- Empty state with border -->
        <div v-if="definedFields.length === 0" class="metadata-empty-state bordered">
          <q-icon name="category" size="48px" color="grey-4" />
          <div class="text-subtitle1 text-grey-7 q-mt-md">No metadata fields defined</div>
          <div class="text-body2 text-grey-6 q-mb-lg">Define fields to create a structured metadata schema</div>

          <!-- Buttons in empty state -->
          <div class="row items-center justify-center q-gutter-x-md">
            <q-btn no-caps unelevated color="primary" icon="add" label="Add Field" class="kg-action-btn" @click.stop="openFieldDialog()" />
            <span class="text-grey-6 text-body2">or</span>
            <q-btn-dropdown
              no-caps
              unelevated
              color="primary"
              icon="playlist_add"
              label="Add Preset"
              class="kg-action-btn"
              dropdown-icon="expand_more"
              content-class="kg-preset-dropdown-menu"
              :disable="availablePresets.length === 0"
              @click.stop
            >
              <q-list dense class="kg-preset-dropdown-list">
                <q-item
                  v-for="preset in availablePresets"
                  :key="preset.name"
                  v-close-popup
                  clickable
                  class="kg-preset-dropdown-item"
                  @click="addPresetField(preset)"
                >
                  <q-item-section>
                    <q-item-label class="kg-preset-label">{{ preset.display_name || preset.name }}</q-item-label>
                    <q-item-label v-if="preset.description" caption class="kg-preset-caption">{{ preset.description }}</q-item-label>
                  </q-item-section>
                </q-item>
                <q-item v-if="availablePresets.length === 0" disable>
                  <q-item-section class="text-grey-6">All presets already added</q-item-section>
                </q-item>
              </q-list>
            </q-btn-dropdown>
          </div>
        </div>

        <q-table
          v-else
          :rows="definedFields"
          :columns="definedFieldsColumns"
          row-key="id"
          flat
          bordered
          hide-pagination
          :rows-per-page-options="[0]"
          table-header-class="bg-primary-light"
          @row-click="onFieldRowClick"
        >
          <template #body-cell-name="slotProps">
            <q-td :props="slotProps">
              <div class="row items-center no-wrap q-gap-sm">
                <div style="max-width: 360px">
                  <div class="text-body2 text-weight-medium ellipsis">
                    {{ slotProps.row.display_name || slotProps.row.name }}
                    <q-tooltip>{{ slotProps.row.display_name || slotProps.row.name }}</q-tooltip>
                  </div>
                  <div class="text-caption text-grey-6 ellipsis font-mono">
                    {{ slotProps.row.name }}
                    <q-tooltip>{{ slotProps.row.name }}</q-tooltip>
                  </div>
                </div>
              </div>
            </q-td>
          </template>

          <template #body-cell-value_type="slotProps">
            <q-td :props="slotProps">
              <span class="text-caption text-grey-8">{{ getTypeLabel(slotProps.row.value_type) }}</span>
            </q-td>
          </template>

          <template #body-cell-constraints="slotProps">
            <q-td :props="slotProps">
              <div class="row items-center q-gutter-x-sm">
                <template v-if="slotProps.row.allowed_values?.length">
                  <span class="text-caption text-grey-7">{{ slotProps.row.allowed_values.length }} allowed values</span>
                  <q-tooltip>
                    <div class="text-caption">Allowed values:</div>
                    <div v-for="v in slotProps.row.allowed_values.slice(0, 10)" :key="v">• {{ v }}</div>
                    <div v-if="slotProps.row.allowed_values.length > 10">...and {{ slotProps.row.allowed_values.length - 10 }} more</div>
                  </q-tooltip>
                </template>
                <span v-if="slotProps.row.is_required" class="text-caption text-orange-9">Required</span>
                <span v-if="!slotProps.row.allowed_values?.length && !slotProps.row.is_required" class="text-grey-5">—</span>
              </div>
            </q-td>
          </template>

          <template #body-cell-actions="slotProps">
            <q-td :props="slotProps" class="text-right">
              <q-btn dense flat color="dark" icon="more_vert" @click.stop>
                <q-menu class="kg-field-menu" anchor="bottom right" self="top right" auto-close>
                  <q-list dense>
                    <q-item v-ripple="false" clickable @click="openFieldDialog(slotProps.row)">
                      <q-item-section thumbnail>
                        <q-icon name="o_edit" color="primary" size="20px" class="q-ml-sm" />
                      </q-item-section>
                      <q-item-section>Edit</q-item-section>
                    </q-item>
                    <q-separator />
                    <q-item v-ripple="false" clickable @click="confirmDeleteField(slotProps.row)">
                      <q-item-section thumbnail>
                        <q-icon name="o_delete" color="negative" size="20px" class="q-ml-sm" />
                      </q-item-section>
                      <q-item-section>Delete</q-item-section>
                    </q-item>
                  </q-list>
                </q-menu>
              </q-btn>
            </q-td>
          </template>
        </q-table>
      </km-section>

      <!-- AI Metadata Extraction -->
      <km-section title="AI Metadata Extraction" sub-title="Enable automatic metadata extraction using LLMs during document ingestion">
        <kg-toggle-field
          v-model="extractionEnabled"
          title="Enable automatic metadata extraction"
          description="When enabled, Magnet can extract metadata fields during ingestion and enrich documents automatically."
        />
      </km-section>

      <!-- Discovered Fields -->
      <km-section title="Discovered Fields" sub-title="Metadata fields observed across documents from all sources, including AI-extracted values">
        <div class="row items-center q-gutter-md q-mb-sm">
          <q-btn-toggle v-model="valuesView" toggle-color="primary" :options="valuesViewOptions" unelevated no-caps size="sm" />
          <q-space />
          <km-input v-model="valuesSearch" placeholder="Search fields or values..." icon-before="search" clearable style="width: 250px" />
          <q-btn
            v-if="undefinedFields.length > 0"
            no-caps
            flat
            color="primary"
            icon="playlist_add"
            label="Define All"
            class="kg-action-btn"
            @click="defineAllDiscovered"
          />
        </div>

        <q-linear-progress v-if="loadingValues" indeterminate color="primary" />

        <div v-else-if="filteredValueRows.length === 0" class="metadata-empty-state">
          <q-icon :name="valuesSearch ? 'search_off' : 'inventory_2'" size="48px" color="grey-4" />
          <div class="text-subtitle1 text-grey-7 q-mt-md">{{ valuesSearch ? 'No matching fields' : 'No discovered fields' }}</div>
          <div class="text-body2 text-grey-6">
            {{ valuesSearch ? 'Try a different search term' : 'Sync sources to populate metadata' }}
          </div>
        </div>

        <q-table
          v-else
          v-model:pagination="valuesPagination"
          :rows="filteredValueRows"
          :columns="valuesColumns"
          row-key="name"
          flat
          bordered
          table-header-class="bg-primary-light"
          :rows-per-page-options="[10]"
          @row-click="onValueRowClick"
        >
          <template #body-cell-name="slotProps">
            <q-td :props="slotProps">
              <div class="row items-center no-wrap q-gap-sm">
                <div style="max-width: 360px">
                  <div class="text-body2 text-weight-medium ellipsis">
                    {{ slotProps.row.display_name || slotProps.row.name }}
                    <q-tooltip>{{ slotProps.row.display_name || slotProps.row.name }}</q-tooltip>
                  </div>
                  <div class="text-caption text-grey-6 ellipsis font-mono">
                    {{ slotProps.row.name }}
                    <q-tooltip>{{ slotProps.row.name }}</q-tooltip>
                  </div>
                </div>
              </div>
            </q-td>
          </template>

          <template #body-cell-value_type="slotProps">
            <q-td :props="slotProps">
              <span class="text-caption text-grey-8">{{ getTypeLabel(slotProps.row.value_type) }}</span>
            </q-td>
          </template>

          <template #body-cell-origins="slotProps">
            <q-td :props="slotProps">
              <div class="row items-center no-wrap q-gutter-x-sm">
                <q-icon
                  v-for="origin in slotProps.row.origins"
                  :key="origin"
                  :name="getOriginIcon(origin)"
                  :color="getOriginIconColor(origin)"
                  size="18px"
                >
                  <q-tooltip>{{ getOriginLabel(origin) }}</q-tooltip>
                </q-icon>
                <span v-if="!slotProps.row.origins?.length" class="text-grey-5">—</span>
              </div>
            </q-td>
          </template>

          <template #body-cell-sample_values="slotProps">
            <q-td :props="slotProps">
              <div class="row items-center q-gutter-x-xs">
                <span v-for="sample in (slotProps.row.sample_values || []).slice(0, 3)" :key="sample" class="kg-sample-value">
                  {{ truncateValue(sample, 20) }}
                  <q-tooltip v-if="sample.length > 20">{{ sample }}</q-tooltip>
                </span>
                <span v-if="(slotProps.row.sample_values || []).length > 3" class="text-caption text-grey-6">
                  +{{ slotProps.row.sample_values.length - 3 }} more
                </span>
                <span v-if="!(slotProps.row.sample_values || []).length" class="text-grey-5">—</span>
              </div>
            </q-td>
          </template>

          <template #body-cell-is_defined="slotProps">
            <q-td :props="slotProps">
              <div class="row items-center no-wrap q-gutter-x-xs">
                <q-icon
                  :name="slotProps.row.is_defined ? 'check_circle' : 'warning'"
                  :color="slotProps.row.is_defined ? 'positive' : 'orange-7'"
                  size="16px"
                />
                <span class="text-caption" :class="slotProps.row.is_defined ? 'text-grey-7' : 'text-orange-9'">
                  {{ slotProps.row.is_defined ? 'Defined' : 'Needs schema' }}
                </span>
              </div>
            </q-td>
          </template>

          <template #body-cell-actions="slotProps">
            <q-td :props="slotProps" class="text-right">
              <q-btn
                v-if="slotProps.row.is_defined"
                flat
                dense
                round
                icon="o_edit"
                size="sm"
                color="grey-7"
                @click.stop="openFieldDialogForValue(slotProps.row)"
              >
                <q-tooltip>Edit field</q-tooltip>
              </q-btn>
              <q-btn v-else flat dense round icon="o_add" size="sm" color="primary" @click.stop="openFieldDialogFromDiscovered(slotProps.row)">
                <q-tooltip>Define field</q-tooltip>
              </q-btn>
            </q-td>
          </template>
        </q-table>
      </km-section>
    </div>

    <!-- Field Definition Dialog -->
    <metadata-field-dialog
      :show-dialog="showFieldDialog"
      :field="editingField"
      :existing-field-names="definedFieldNames"
      @update:show-dialog="showFieldDialog = $event"
      @cancel="showFieldDialog = false"
      @save="onFieldSave"
    />
  </div>
</template>

<script setup lang="ts">
import { fetchData } from '@shared'
import { QTableColumn, useQuasar } from 'quasar'
import { computed, onMounted, ref, watch } from 'vue'
import { useStore } from 'vuex'
import { KgToggleField } from '../common'
import MetadataFieldDialog from './MetadataFieldDialog.vue'
import {
  DiscoveredMetadataField,
  MetadataFieldDefinition,
  MetadataFieldRow,
  MetadataOrigin,
  MetadataOriginLabels,
  MetadataValueType,
  PRESET_FIELDS,
  ValueTypeOptions,
} from './models'

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
const extractionEnabled = ref(false)

// Defined fields
const definedFields = ref<MetadataFieldDefinition[]>([])
const showFieldDialog = ref(false)
const editingField = ref<MetadataFieldDefinition | null>(null)

// All metadata values
const allMetadataValues = ref<MetadataFieldRow[]>([])
const loadingValues = ref(false)
const valuesSearch = ref('')
const valuesView = ref<'all' | 'llm' | 'undefined'>('all')
const valuesViewOptions = [
  { label: 'All discovered', value: 'all' },
  { label: 'LLM extracted', value: 'llm' },
  { label: 'Needs schema', value: 'undefined' },
]
const valuesPagination = ref({ rowsPerPage: 10, page: 1 })

// State tracking
const saving = ref(false)
const originalState = ref<string>('')

// Field names for select
const definedFieldNames = computed(() => definedFields.value.map((f) => f.name))

// Available presets (not already defined)
const availablePresets = computed(() => {
  const existingNames = new Set(definedFieldNames.value)
  return PRESET_FIELDS.filter((p) => !existingNames.has(p.name!))
})

const filteredValueRows = computed(() => {
  let rows = allMetadataValues.value

  if (valuesView.value === 'undefined') {
    rows = rows.filter((r) => !r.is_defined)
  } else if (valuesView.value === 'llm') {
    rows = rows.filter((r) => (r.origins || []).includes('llm'))
  }

  if (!valuesSearch.value) return rows
  const search = valuesSearch.value.toLowerCase()
  return rows.filter(
    (f) =>
      f.name.toLowerCase().includes(search) ||
      f.display_name?.toLowerCase().includes(search) ||
      (f.sample_values || []).some((v) => v.toLowerCase().includes(search))
  )
})

// Undefined fields (discovered but not in schema)
const undefinedFields = computed(() => {
  return allMetadataValues.value.filter((f) => !f.is_defined)
})

// Check for unsaved changes
const hasChanges = computed(() => {
  const currentState = JSON.stringify({
    extractionEnabled: extractionEnabled.value,
    definedFields: definedFields.value,
  })
  return currentState !== originalState.value
})

// Table columns
const definedFieldsColumns: QTableColumn[] = [
  { name: 'name', label: 'Field', field: 'display_name', align: 'left', sortable: true },
  { name: 'description', label: 'Description', field: 'description', align: 'left', style: 'max-width: 300px', classes: 'text-grey-7 ellipsis' },
  { name: 'value_type', label: 'Type', field: 'value_type', align: 'left', sortable: true },
  { name: 'constraints', label: 'Constraints', field: 'allowed_values', align: 'left' },
  { name: 'actions', label: '', field: 'id', align: 'right' },
]

const valuesColumns: QTableColumn<MetadataFieldRow>[] = [
  { name: 'name', label: 'Field', field: 'name', align: 'left', sortable: true },
  { name: 'value_type', label: 'Type', field: 'value_type', align: 'left', sortable: true },
  { name: 'sample_values', label: 'Samples', field: 'sample_values', align: 'left' },
  { name: 'origins', label: 'Source', field: 'origins', align: 'left' },
  { name: 'is_defined', label: 'Status', field: 'is_defined', align: 'left', sortable: true },
  { name: 'actions', label: '', field: 'name', align: 'right' },
]

// Initialize from graph settings
const initializeFromSettings = () => {
  const settings = props.graphDetails?.settings?.metadata || {}

  extractionEnabled.value = settings.extraction?.enabled ?? false
  definedFields.value = settings.field_definitions || []

  captureOriginalState()
  syncDefinitionsToValues()
}

const captureOriginalState = () => {
  originalState.value = JSON.stringify({
    extractionEnabled: extractionEnabled.value,
    definedFields: definedFields.value,
  })
}

// Fetch aggregated metadata values
const fetchMetadataValues = async () => {
  // Mock sample metadata values for demonstration purposes
  allMetadataValues.value = [
    {
      id: '1',
      name: 'author',
      display_name: 'Author',
      description: 'The creator or contributor of the document.',
      value_type: 'string',
      origins: ['document', 'static'],
      is_searchable: true,
      is_filterable: true,
      is_defined: definedFieldNames.value.includes('author'),
      sample_values: ['Alice Smith', 'Bob Lee', 'Carol Chen'],
    },
    {
      id: '2',
      name: 'publication_date',
      display_name: 'Publication Date',
      description: 'The date the document was published.',
      value_type: 'date',
      origins: ['document'],
      is_searchable: false,
      is_filterable: true,
      is_defined: definedFieldNames.value.includes('publication_date'),
      sample_values: ['2024-01-10', '2023-11-05', '2023-08-21'],
    },
    {
      id: '3',
      name: 'language',
      display_name: 'Language',
      description: 'The language of the content.',
      value_type: 'string',
      origins: ['llm', 'document'],
      is_searchable: true,
      is_filterable: true,
      is_defined: definedFieldNames.value.includes('language'),
      sample_values: ['English', 'Spanish', 'French'],
    },
    {
      id: '4',
      name: 'doc_type',
      display_name: 'Document Type',
      description: 'The classification of the document content.',
      value_type: 'string',
      origins: ['static'],
      is_searchable: true,
      is_filterable: true,
      is_defined: definedFieldNames.value.includes('doc_type'),
      sample_values: ['Manual', 'FAQ', 'Guide'],
    },
  ]
  syncDefinitionsToValues()
}

// Save settings
const saveSettings = async () => {
  if (!hasChanges.value) return
  saving.value = true
  try {
    const endpoint = store.getters.config.api.aiBridge.urlAdmin
    const payload = {
      settings: {
        ...(props.graphDetails?.settings || {}),
        metadata: {
          extraction: {
            enabled: extractionEnabled.value,
          },
          field_definitions: definedFields.value,
        },
      },
    }

    const res = await fetchData({
      endpoint,
      service: `knowledge_graphs//${props.graphId}`,
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

const openFieldDialogForValue = (row: MetadataFieldRow) => {
  const existing = definedFields.value.find((f) => f.name === row.name)
  if (existing) {
    openFieldDialog(existing)
    return
  }
  openFieldDialogFromDiscovered(row)
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
    is_searchable: true,
    is_filterable: true,
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

const onFieldRowClick = (evt: Event, row: MetadataFieldDefinition) => {
  openFieldDialog(row)
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
    is_searchable: preset.is_searchable ?? true,
    is_filterable: preset.is_filterable ?? true,
    is_required: preset.is_required ?? false,
    allowed_values: preset.allowed_values,
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
      is_searchable: true,
      is_filterable: true,
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

// Helper functions
const getTypeLabel = (type: MetadataValueType) => {
  return ValueTypeOptions.find((t) => t.value === type)?.label || type
}

const getOriginLabel = (origin: MetadataOrigin) => MetadataOriginLabels[origin]

const getOriginIcon = (origin: MetadataOrigin) => {
  switch (origin) {
    case 'llm':
      return 'smart_toy'
    case 'document':
      return 'description'
    case 'static':
      return 'tune'
    case 'system':
      return 'settings'
    default:
      return 'help_outline'
  }
}

const getOriginIconColor = (origin: MetadataOrigin) => {
  switch (origin) {
    case 'llm':
      return 'purple-7'
    case 'document':
      return 'teal-7'
    case 'static':
      return 'primary'
    case 'system':
      return 'grey-7'
    default:
      return 'grey-7'
  }
}

const truncateValue = (value: string, maxLength = 30) => {
  return value.length > maxLength ? value.substring(0, maxLength) + '...' : value
}

const onValueRowClick = (_evt: Event, row: MetadataFieldRow) => {
  openFieldDialogForValue(row)
}

// Watch for changes
watch(hasChanges, (val) => {
  emit('unsaved-change', val)
})

watch([valuesSearch, valuesView], () => {
  valuesPagination.value.page = 1
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
})

// Expose methods for parent
defineExpose({
  save: saveSettings,
  discard: discardChanges,
})
</script>

<style scoped>
.metadata-empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 48px 24px;
  text-align: center;
}

.metadata-empty-state.bordered {
  border: 1px solid rgba(0, 0, 0, 0.12);
  border-radius: 4px;
}

.font-mono {
  font-family: 'SF Mono', 'Consolas', 'Monaco', monospace;
}

.kg-sample-value {
  display: inline-block;
  padding: 2px 8px;
  background: #f5f5f5;
  border-radius: 4px;
  font-size: 12px;
  color: #555;
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

:deep(.q-table thead th) {
  font-size: 14px;
  font-weight: 600;
}

/* Row menu styling - match SourcesTab */
:deep(.kg-field-menu .q-focus-helper) {
  opacity: 0 !important;
}

:deep(.kg-field-menu .q-item.q-focusable:hover) {
  background: transparent !important;
}

/* Preset dropdown menu styling (variant selector inspired) */
:deep(.kg-preset-dropdown-menu) {
  border-radius: 8px;
  box-shadow:
    0 4px 20px rgba(0, 0, 0, 0.12),
    0 2px 8px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(0, 0, 0, 0.06);
  overflow: hidden;
  min-width: 320px;
}

:deep(.kg-preset-dropdown-list) {
  padding: 4px 0;
}

:deep(.kg-preset-dropdown-item) {
  padding: 8px 16px !important;
  margin: 6px 6px;
  border-radius: 6px;
}

:deep(.kg-preset-dropdown-item:hover) {
  background-color: #f3f4f6;
}

:deep(.kg-preset-icon-section) {
  min-width: 32px !important;
}

:deep(.kg-preset-icon-wrapper) {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 28px;
  height: 28px;
  border-radius: 6px;
  background-color: #dbeafe;
  color: #2563eb;
  transition: all 0.15s ease;
}

:deep(.kg-preset-dropdown-item:hover .kg-preset-icon-wrapper) {
  background-color: #bfdbfe;
}

:deep(.kg-preset-label) {
  font-size: 13px;
  font-weight: 500;
  color: #1f2937;
  line-height: 1.3;
}

:deep(.kg-preset-caption) {
  font-size: 11px;
  color: #9ca3af;
  margin-top: 2px;
  line-height: 1.3;
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

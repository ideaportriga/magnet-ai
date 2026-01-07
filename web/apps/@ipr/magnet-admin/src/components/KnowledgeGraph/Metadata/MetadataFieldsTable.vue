<template>
  <km-section :title="sectionTitle" :sub-title="sectionSubtitle">
    <!-- Toolbar -->
    <div class="row items-center q-gutter-md q-mb-md">
      <!-- Category Tabs -->
      <div class="category-tabs">
        <button
          v-for="cat in categories"
          :key="cat.value"
          class="category-tab"
          :class="{ 'category-tab--active': selectedCategory === cat.value }"
          @click="selectedCategory = cat.value"
        >
          <q-icon :name="cat.icon" size="18px" />
          <span class="category-tab__label">{{ cat.label }}</span>
          <span class="category-tab__count">{{ cat.count }}</span>
        </button>
      </div>

      <!-- Search -->
      <km-input v-model="search" placeholder="Search fields..." icon-before="search" clearable style="width: 220px" />

      <q-space />

      <!-- Filter Dropdown (only for Discovered) -->
      <q-select
        v-if="selectedCategory === 'discovered'"
        v-model="discoveredFilter"
        :options="discoveredFilterOptions"
        dense
        outlined
        emit-value
        map-options
        options-dense
        style="min-width: 160px"
        class="filter-select"
      />

      <!-- Actions (fixed position on right) -->
      <template v-if="selectedCategory === 'schema'">
        <q-btn no-caps flat color="primary" icon="add" label="Add Field" class="action-btn" @click.stop="emit('add-field')" />
        <q-btn-dropdown
          no-caps
          unelevated
          color="primary"
          label="Add Preset"
          class="action-btn"
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
              @click="emit('add-preset', preset)"
            >
              <q-item-section>
                <q-item-label class="preset-label">{{ preset.display_name || preset.name }}</q-item-label>
                <q-item-label v-if="preset.description" caption class="preset-caption">{{ preset.description }}</q-item-label>
              </q-item-section>
            </q-item>
            <q-item v-if="availablePresets.length === 0" disable>
              <q-item-section class="text-grey-6">All presets already added</q-item-section>
            </q-item>
          </q-list>
        </q-btn-dropdown>
      </template>

      <template v-else>
        <q-btn
          no-caps
          flat
          color="primary"
          icon="playlist_add"
          label="Define All"
          :disable="undefinedInCurrentView === 0"
          class="action-btn"
          @click.stop="emit('define-all')"
        />
      </template>
    </div>

    <q-linear-progress v-if="loading" indeterminate color="primary" class="q-mb-sm" />

    <!-- Empty State -->
    <div v-else-if="showEmptyState" class="text-center q-pa-lg">
      <q-icon :name="emptyStateIcon" size="64px" color="grey-5" />
      <div class="km-heading-7 text-grey-7 q-mt-md">{{ emptyStateTitle }}</div>
      <div class="km-description text-grey-6">{{ emptyStateSubtitle }}</div>
    </div>

    <!-- Schema Fields Table -->
    <q-table
      v-else-if="selectedCategory === 'schema'"
      v-model:pagination="pagination"
      :rows="schemaRows"
      :columns="schemaColumns"
      row-key="name"
      flat
      bordered
      table-header-class="bg-primary-light"
      :rows-per-page-options="[10, 25, 50]"
      @row-click="onSchemaRowClick"
    >
      <template #body-cell-field="slotProps">
        <q-td :props="slotProps">
          <div class="row items-center no-wrap q-gutter-x-sm">
            <div style="max-width: 300px">
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

      <template #body-cell-type="slotProps">
        <q-td :props="slotProps">
          <span class="text-caption text-grey-8">{{ getTypeLabel(slotProps.row.value_type) }}</span>
        </q-td>
      </template>

      <template #body-cell-constraints="slotProps">
        <q-td :props="slotProps">
          <div class="row items-center no-wrap q-gutter-x-sm">
            <span v-if="slotProps.row.is_required" class="text-caption text-orange-9">Required</span>
            <span v-if="slotProps.row.allowed_values?.length" class="text-caption text-grey-7">
              {{ slotProps.row.allowed_values.length }} allowed
              <q-tooltip>
                <div class="text-caption">Allowed values:</div>
                <div v-for="av in slotProps.row.allowed_values.slice(0, 10)" :key="av.value">
                  • {{ av.value }}
                  <span v-if="av.hint" class="text-grey-5">— {{ av.hint }}</span>
                </div>
                <div v-if="slotProps.row.allowed_values.length > 10">...and {{ slotProps.row.allowed_values.length - 10 }} more</div>
              </q-tooltip>
            </span>
            <span v-if="slotProps.row.is_multiple" class="text-caption text-grey-7">Multiple</span>
            <span v-if="!slotProps.row.is_required && !slotProps.row.allowed_values?.length && !slotProps.row.is_multiple" class="text-grey-5">
              —
            </span>
          </div>
        </q-td>
      </template>

      <template #body-cell-extraction="slotProps">
        <q-td :props="slotProps">
          <div v-if="slotProps.row.llm_extraction_hint" class="row items-center no-wrap q-gutter-x-xs text-purple-6">
            <q-icon name="smart_toy" size="16px" />
            <span class="text-caption">{{ slotProps.row.is_required ? 'Mandatory' : 'Optional' }}</span>
            <q-tooltip max-width="320px">
              <div class="text-weight-medium q-mb-xs">AI Extraction Hint:</div>
              <div class="text-caption" style="white-space: pre-wrap">{{ slotProps.row.llm_extraction_hint }}</div>
            </q-tooltip>
          </div>
          <span v-else class="text-caption text-grey-5">Disabled</span>
        </q-td>
      </template>

      <template #body-cell-observed="slotProps">
        <q-td :props="slotProps">
          <template v-if="getDiscoveredForDefinition(slotProps.row)">
            <div class="row items-center no-wrap q-gutter-x-sm">
              <!-- Origins as text labels -->
              <div class="row items-center no-wrap q-gutter-x-xs">
                <template v-for="origin in getDiscoveredForDefinition(slotProps.row)?.origins || []" :key="origin">
                  <span class="origin-label" :class="`origin-label--${origin}`">{{ getOriginLabel(origin) }}</span>
                </template>
              </div>
              <!-- Sample values -->
              <div v-if="getDiscoveredForDefinition(slotProps.row)?.sample_values?.length" class="row items-center no-wrap q-gutter-x-xs">
                <span v-for="sample in getDiscoveredForDefinition(slotProps.row)?.sample_values?.slice(0, 2)" :key="sample" class="sample-chip">
                  {{ truncateValue(sample, 12) }}
                  <q-tooltip v-if="sample.length > 12">{{ sample }}</q-tooltip>
                </span>
                <span v-if="(getDiscoveredForDefinition(slotProps.row)?.sample_values?.length || 0) > 2" class="text-caption text-grey-6">
                  +{{ (getDiscoveredForDefinition(slotProps.row)?.sample_values?.length || 0) - 2 }}
                </span>
              </div>
            </div>
          </template>
          <span v-else class="text-grey-5">—</span>
        </q-td>
      </template>

      <template #body-cell-actions="slotProps">
        <q-td :props="slotProps" class="text-right">
          <q-btn dense flat color="dark" icon="more_vert" @click.stop>
            <q-menu class="field-menu" anchor="bottom right" self="top right" auto-close>
              <q-list dense>
                <q-item v-ripple="false" clickable @click="emit('edit-field', slotProps.row)">
                  <q-item-section thumbnail>
                    <q-icon name="o_edit" color="primary" size="20px" class="q-ml-sm" />
                  </q-item-section>
                  <q-item-section>Edit</q-item-section>
                </q-item>
                <q-separator />
                <q-item v-ripple="false" clickable @click="emit('delete-field', slotProps.row)">
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

    <!-- Discovered Fields Table -->
    <q-table
      v-else
      v-model:pagination="pagination"
      :rows="discoveredRows"
      :columns="discoveredColumns"
      row-key="name"
      flat
      bordered
      table-header-class="bg-primary-light"
      :rows-per-page-options="[10, 25, 50]"
      @row-click="onDiscoveredRowClick"
    >
      <template #body-cell-field="slotProps">
        <q-td :props="slotProps">
          <div class="row items-center no-wrap q-gutter-x-sm">
            <div style="max-width: 300px">
              <div class="row items-center no-wrap q-gutter-x-sm">
                <span class="text-body2 text-weight-medium ellipsis">
                  {{ slotProps.row.display_name || slotProps.row.name }}
                </span>
                <q-icon v-if="slotProps.row.is_defined" name="check_circle" size="14px" color="positive">
                  <q-tooltip>Defined in schema</q-tooltip>
                </q-icon>
              </div>
              <div class="text-caption text-grey-6 ellipsis font-mono">
                {{ slotProps.row.name }}
                <q-tooltip>{{ slotProps.row.name }}</q-tooltip>
              </div>
            </div>
          </div>
        </q-td>
      </template>

      <template #body-cell-type="slotProps">
        <q-td :props="slotProps">
          <span class="text-caption text-grey-8">{{ getTypeLabel(slotProps.row.value_type) }}</span>
        </q-td>
      </template>

      <template #body-cell-origins="slotProps">
        <q-td :props="slotProps">
          <div class="row items-center no-wrap q-gutter-x-sm">
            <template v-if="slotProps.row.origins?.length">
              <template v-for="origin in slotProps.row.origins" :key="origin">
                <span class="origin-chip" :class="`origin-chip--${origin}`">
                  {{ getOriginLabel(origin) }}
                  <template v-if="origin === 'source' && slotProps.row.sources?.length">
                    <span class="text-weight-medium">({{ slotProps.row.sources.length }})</span>
                    <q-tooltip>
                      <div class="text-weight-medium q-mb-xs">Sources:</div>
                      <div v-for="src in slotProps.row.sources.slice(0, 12)" :key="src.id">• {{ src.name }}</div>
                      <div v-if="slotProps.row.sources.length > 12">...and {{ slotProps.row.sources.length - 12 }} more</div>
                    </q-tooltip>
                  </template>
                </span>
              </template>
            </template>
            <span v-else class="text-grey-5">—</span>
          </div>
        </q-td>
      </template>

      <template #body-cell-samples="slotProps">
        <q-td :props="slotProps">
          <div class="row items-center no-wrap q-gutter-x-xs">
            <template v-if="slotProps.row.sample_values?.length">
              <span v-for="sample in slotProps.row.sample_values.slice(0, 3)" :key="sample" class="sample-chip">
                {{ truncateValue(sample, 20) }}
                <q-tooltip v-if="sample.length > 20">{{ sample }}</q-tooltip>
              </span>
              <span v-if="slotProps.row.sample_values.length > 3" class="text-caption text-grey-6">
                +{{ slotProps.row.sample_values.length - 3 }}
              </span>
            </template>
            <span v-else class="text-grey-5">—</span>
          </div>
        </q-td>
      </template>

      <template #body-cell-actions="slotProps">
        <q-td :props="slotProps" class="text-right">
          <template v-if="slotProps.row.is_defined">
            <q-btn dense flat round icon="o_edit" size="sm" color="grey-7" @click.stop="editDefinedField(slotProps.row)">
              <q-tooltip>Edit schema definition</q-tooltip>
            </q-btn>
          </template>
          <template v-else>
            <q-btn flat dense no-caps color="primary" icon="o_add" size="sm" @click.stop="emit('define-field', slotProps.row)">
              <q-tooltip>Define field</q-tooltip>
            </q-btn>
          </template>
        </q-td>
      </template>
    </q-table>
  </km-section>
</template>

<script setup lang="ts">
import type { QTableColumn } from 'quasar'
import { computed, ref, watch } from 'vue'
import { MetadataFieldDefinition, MetadataFieldRow, MetadataOrigin, MetadataOriginLabels, MetadataValueType, ValueTypeOptions } from './models'

type CategoryType = 'schema' | 'discovered'
type DiscoveredFilterType = 'all' | 'undefined' | 'defined' | 'llm' | 'source' | 'document'

const props = defineProps<{
  definedFields: MetadataFieldDefinition[]
  discoveredFields: MetadataFieldRow[]
  availablePresets: Partial<MetadataFieldDefinition>[]
  loading: boolean
}>()

const emit = defineEmits<{
  (e: 'add-field'): void
  (e: 'add-preset', preset: Partial<MetadataFieldDefinition>): void
  (e: 'define-all'): void
  (e: 'edit-field', field: MetadataFieldDefinition): void
  (e: 'delete-field', field: MetadataFieldDefinition): void
  (e: 'define-field', row: MetadataFieldRow): void
}>()

const selectedCategory = ref<CategoryType>('schema')
const discoveredFilter = ref<DiscoveredFilterType>('all')
const search = ref('')
const pagination = ref({ rowsPerPage: 10, page: 1 })

// Maps for quick lookups
const defsByName = computed(() => new Map((props.definedFields || []).map((f) => [f.name, f] as const)))
const discoveredByName = computed(() => new Map((props.discoveredFields || []).map((r) => [r.name, r] as const)))

// Counts
const schemaCount = computed(() => (props.definedFields || []).length)
const discoveredCount = computed(() => (props.discoveredFields || []).length)
const undefinedDiscoveredCount = computed(() => (props.discoveredFields || []).filter((f) => !f.is_defined).length)
const definedDiscoveredCount = computed(() => (props.discoveredFields || []).filter((f) => f.is_defined).length)
const llmDiscoveredCount = computed(() => (props.discoveredFields || []).filter((f) => f.origins?.includes('llm')).length)
const sourceDiscoveredCount = computed(() => (props.discoveredFields || []).filter((f) => f.origins?.includes('source')).length)
const documentDiscoveredCount = computed(() => (props.discoveredFields || []).filter((f) => f.origins?.includes('document')).length)

// Category tabs config
const categories = computed(() => [
  { value: 'schema' as const, label: 'Schema', count: schemaCount.value, icon: 'tune' },
  { value: 'discovered' as const, label: 'Discovered', count: discoveredCount.value, icon: 'explore' },
])

// Discovered filter dropdown options
const discoveredFilterOptions = computed(() => [
  { label: `All (${discoveredCount.value})`, value: 'all' },
  { label: `Needs Schema (${undefinedDiscoveredCount.value})`, value: 'undefined' },
  { label: `Already Defined (${definedDiscoveredCount.value})`, value: 'defined' },
  { label: `LLM Extracted (${llmDiscoveredCount.value})`, value: 'llm' },
  { label: `From Source (${sourceDiscoveredCount.value})`, value: 'source' },
  { label: `From Document (${documentDiscoveredCount.value})`, value: 'document' },
])

// Section title and subtitle based on category
const sectionTitle = computed(() => (selectedCategory.value === 'schema' ? 'Schema Fields' : 'Discovered Fields'))
const sectionSubtitle = computed(() => {
  if (selectedCategory.value === 'schema') {
    return 'User-defined metadata field definitions that structure your knowledge graph'
  }
  return 'Metadata fields automatically detected from documents during ingestion'
})

// Filtered rows for Schema table
const schemaRows = computed(() => {
  let rows = props.definedFields || []
  if (!search.value) return rows

  const s = search.value.toLowerCase()
  return rows.filter(
    (r) => r.name.toLowerCase().includes(s) || (r.display_name || '').toLowerCase().includes(s) || (r.description || '').toLowerCase().includes(s)
  )
})

// Filtered rows for Discovered table
const discoveredRows = computed(() => {
  let rows = props.discoveredFields || []

  // Apply sub-filter
  if (discoveredFilter.value === 'undefined') {
    rows = rows.filter((r) => !r.is_defined)
  } else if (discoveredFilter.value === 'defined') {
    rows = rows.filter((r) => r.is_defined)
  } else if (discoveredFilter.value === 'llm') {
    rows = rows.filter((r) => r.origins?.includes('llm'))
  } else if (discoveredFilter.value === 'source') {
    rows = rows.filter((r) => r.origins?.includes('source'))
  } else if (discoveredFilter.value === 'document') {
    rows = rows.filter((r) => r.origins?.includes('document'))
  }

  if (!search.value) return rows

  const s = search.value.toLowerCase()
  return rows.filter(
    (r) =>
      r.name.toLowerCase().includes(s) ||
      (r.display_name || '').toLowerCase().includes(s) ||
      r.sample_values?.some((v) => v.toLowerCase().includes(s))
  )
})

// Count of undefined fields in current view
const undefinedInCurrentView = computed(() => discoveredRows.value.filter((r) => !r.is_defined).length)

// Empty state logic
const showEmptyState = computed(() => {
  if (props.loading) return false
  if (selectedCategory.value === 'schema') {
    return schemaRows.value.length === 0
  }
  return discoveredRows.value.length === 0
})

const emptyStateIcon = computed(() => {
  if (search.value) return 'search_off'
  if (selectedCategory.value === 'schema') return 'category'
  if (discoveredFilter.value === 'undefined') return 'check_circle'
  if (discoveredFilter.value === 'llm') return 'smart_toy'
  return 'explore'
})

const emptyStateTitle = computed(() => {
  if (search.value) return 'No matching fields'
  if (selectedCategory.value === 'schema') return 'No schema fields defined'
  if (discoveredFilter.value === 'undefined') return 'All fields are defined'
  if (discoveredFilter.value === 'defined') return 'No defined fields found'
  if (discoveredFilter.value === 'llm') return 'No LLM-extracted fields'
  if (discoveredFilter.value === 'source') return 'No source-origin fields'
  if (discoveredFilter.value === 'document') return 'No document-origin fields'
  return 'No discovered fields'
})

const emptyStateSubtitle = computed(() => {
  if (search.value) return 'Try a different search term'
  if (selectedCategory.value === 'schema') return 'Add a field definition to start building your metadata schema'
  if (discoveredFilter.value === 'undefined') return 'All discovered fields have been added to the schema'
  return 'Sync sources to discover metadata fields from your documents'
})

// Schema table columns
const schemaColumns = computed<QTableColumn<MetadataFieldDefinition>[]>(() => [
  { name: 'field', label: 'Field', field: 'name', align: 'left', sortable: true },
  { name: 'type', label: 'Type', field: 'value_type', align: 'left', sortable: true, style: 'width: 100px' },
  { name: 'constraints', label: 'Constraints', field: () => '', align: 'left', style: 'width: 180px' },
  { name: 'extraction', label: 'AI Extraction', field: () => '', align: 'left', style: 'width: 120px' },
  { name: 'observed', label: 'Observed', field: () => '', align: 'left' },
  { name: 'actions', label: '', field: 'name', align: 'right', style: 'width: 60px' },
])

// Discovered table columns
const discoveredColumns = computed<QTableColumn<MetadataFieldRow>[]>(() => [
  { name: 'field', label: 'Field', field: 'name', align: 'left', sortable: true },
  { name: 'type', label: 'Type', field: 'value_type', align: 'left', sortable: true, style: 'width: 100px' },
  { name: 'origins', label: 'Origin', field: () => '', align: 'left', style: 'width: 220px' },
  { name: 'samples', label: 'Sample Values', field: () => '', align: 'left' },
  { name: 'actions', label: '', field: 'name', align: 'right', style: 'width: 80px' },
])

// Helper functions
const getTypeLabel = (type: MetadataValueType) => ValueTypeOptions.find((t) => t.value === type)?.label || type
const getOriginLabel = (origin: MetadataOrigin) => MetadataOriginLabels[origin]

const truncateValue = (value: string, maxLength = 30) => {
  return value.length > maxLength ? value.substring(0, maxLength) + '…' : value
}

const getDiscoveredForDefinition = (def: MetadataFieldDefinition): MetadataFieldRow | undefined => {
  return discoveredByName.value.get(def.name)
}

// Row click handlers
const onSchemaRowClick = (_evt: Event, row: MetadataFieldDefinition) => {
  emit('edit-field', row)
}

const onDiscoveredRowClick = (_evt: Event, row: MetadataFieldRow) => {
  if (row.is_defined) {
    const def = defsByName.value.get(row.name)
    if (def) emit('edit-field', def)
  } else {
    emit('define-field', row)
  }
}

const editDefinedField = (row: MetadataFieldRow) => {
  const def = defsByName.value.get(row.name)
  if (def) emit('edit-field', def)
}

// Reset pagination on filter changes
watch([search, selectedCategory, discoveredFilter], () => {
  pagination.value.page = 1
})
</script>

<style scoped>
.font-mono {
  font-family: 'SF Mono', 'Consolas', 'Monaco', monospace;
}

/* Category Tabs */
.category-tabs {
  display: flex;
  gap: 2px;
  background: #f3f4f6;
  padding: 4px;
  border-radius: 8px;
}

.category-tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.15s ease;
  font-size: 13px;
  font-weight: 500;
  color: #6b7280;
}

.category-tab:hover {
  background: rgba(0, 0, 0, 0.04);
  color: #374151;
}

.category-tab--active {
  background: white;
  color: #1f2937;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.category-tab__count {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 18px;
  padding: 0 6px;
  background: #e5e7eb;
  border-radius: 9px;
  font-size: 11px;
  font-weight: 600;
  color: #6b7280;
}

.category-tab--active .category-tab__count {
  background: var(--q-primary);
  color: white;
}

.action-btn {
  font-size: 13px;
  height: 34px;
  min-height: 34px;
  padding-left: 12px;
  padding-right: 12px;
}

.filter-select {
  font-size: 13px;
}

:deep(.filter-select .q-field__control) {
  height: 34px;
  min-height: 34px;
}

:deep(.filter-select .q-field__native) {
  padding-top: 0;
  padding-bottom: 0;
}

/* Table styles */
:deep(.q-table thead th) {
  font-size: 14px;
  font-weight: 600;
}

:deep(.q-table tbody tr) {
  cursor: pointer;
}

/* Sample chips */
.sample-chip {
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

/* Origin labels (compact text in Schema table) */
.origin-label {
  font-size: 11px;
  font-weight: 500;
  padding: 1px 6px;
  border-radius: 3px;
}

.origin-label--llm {
  background: #f3e8ff;
  color: #7c3aed;
}

.origin-label--document {
  background: #ccfbf1;
  color: #0d9488;
}

.origin-label--system {
  background: #f3f4f6;
  color: #4b5563;
}

.origin-label--source {
  background: #e0e7ff;
  color: #4338ca;
}

/* Origin chips (Discovered table) */
.origin-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 12px;
  font-weight: 500;
}

.origin-chip--llm {
  background: #f3e8ff;
  color: #7c3aed;
}

.origin-chip--document {
  background: #ccfbf1;
  color: #0d9488;
}

.origin-chip--system {
  background: #f3f4f6;
  color: #4b5563;
}

.origin-chip--source {
  background: #e0e7ff;
  color: #4338ca;
}

/* Menu styling */
:deep(.field-menu .q-focus-helper) {
  opacity: 0 !important;
}

:deep(.field-menu .q-item.q-focusable:hover) {
  background: transparent !important;
}

/* Preset dropdown */
:deep(.preset-dropdown-menu) {
  border-radius: 8px;
  box-shadow:
    0 4px 20px rgba(0, 0, 0, 0.12),
    0 2px 8px rgba(0, 0, 0, 0.08);
  border: 1px solid rgba(0, 0, 0, 0.06);
  overflow: hidden;
  min-width: 320px;
}

:deep(.preset-dropdown-list) {
  padding: 4px 0;
}

:deep(.preset-dropdown-item) {
  padding: 8px 16px !important;
  margin: 6px 6px;
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

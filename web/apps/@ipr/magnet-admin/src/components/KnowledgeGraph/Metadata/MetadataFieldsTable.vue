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
      <kg-dropdown-field
        v-if="selectedCategory === 'discovered'"
        v-model="discoveredFilter"
        :options="discoveredFilterOptions"
        dense
        style="min-width: 180px"
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

      <template v-else-if="selectedCategory === 'extracted'">
        <q-btn
          no-caps
          unelevated
          color="primary"
          icon="play_arrow"
          label="Run Extraction"
          :loading="runningExtraction"
          :disable="!canRunExtraction || runningExtraction"
          class="action-btn"
          @click.stop="emit('run-extraction')"
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
      v-model:pagination="schemaPagination"
      :rows="schemaRows"
      :columns="schemaColumns"
      row-key="name"
      flat
      bordered
      dense
      :rows-per-page-options="[5]"
      class="compact-table"
      @row-click="(evt, row) => emit('edit-field', row)"
    >
      <template #body-cell-field="slotProps">
        <q-td :props="slotProps">
          <div class="row items-center no-wrap q-gutter-x-xs">
            <span class="compact-field-name ellipsis" style="max-width: 280px">
              {{ slotProps.row.display_name || slotProps.row.name }}
            </span>
          </div>
        </q-td>
      </template>

      <template #body-cell-type="slotProps">
        <q-td :props="slotProps">
          <span class="compact-type">{{ getTypeLabel(slotProps.row.value_type) }}</span>
        </q-td>
      </template>

      <template #body-cell-constraints="slotProps">
        <q-td :props="slotProps">
          <div class="row items-center no-wrap q-gutter-x-sm">
            <span v-if="slotProps.row.allowed_values?.length" class="compact-constraint">{{ slotProps.row.allowed_values.length }} allowed</span>
            <span v-if="slotProps.row.is_multiple" class="compact-constraint">Multiple</span>
            <span v-if="!slotProps.row.allowed_values?.length && !slotProps.row.is_multiple" class="text-grey-5">—</span>
          </div>
        </q-td>
      </template>

      <template #body-cell-actions="slotProps">
        <q-td :props="slotProps" class="text-right">
          <q-btn dense flat round color="grey-7" icon="more_vert" size="sm" @click.stop>
            <q-menu class="field-menu" anchor="bottom right" self="top right" auto-close>
              <q-list dense>
                <q-item v-ripple="false" clickable @click="emit('edit-field', slotProps.row)">
                  <q-item-section thumbnail>
                    <q-icon name="o_edit" color="primary" size="18px" class="q-ml-sm" />
                  </q-item-section>
                  <q-item-section>Edit</q-item-section>
                </q-item>
                <q-separator />
                <q-item v-ripple="false" clickable @click="emit('delete-field', slotProps.row)">
                  <q-item-section thumbnail>
                    <q-icon name="o_delete" color="negative" size="18px" class="q-ml-sm" />
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
      v-else-if="selectedCategory === 'discovered'"
      v-model:pagination="discoveredPagination"
      :rows="discoveredRows"
      :columns="discoveredColumns"
      row-key="id"
      flat
      bordered
      dense
      :rows-per-page-options="[5]"
      class="compact-table"
    >
      <template #body-cell-field="slotProps">
        <q-td :props="slotProps">
          <div class="row items-center no-wrap q-gutter-x-xs">
            <span class="compact-field-name ellipsis" style="max-width: 280px">
              {{ slotProps.row.display_name || slotProps.row.name }}
            </span>
            <q-icon v-if="slotProps.row.is_defined" name="check_circle" size="12px" color="positive" />
          </div>
        </q-td>
      </template>

      <template #body-cell-type="slotProps">
        <q-td :props="slotProps">
          <span class="compact-type">{{ getTypeLabel(slotProps.row.value_type) }}</span>
        </q-td>
      </template>

      <template #body-cell-origin="slotProps">
        <q-td :props="slotProps">
          <template v-if="slotProps.row.origin">
            <span class="origin-chip" :class="`origin-chip--${slotProps.row.origin}`">
              {{ getOriginLabel(slotProps.row.origin) }}
            </span>
          </template>
          <span v-else class="text-grey-5">—</span>
        </q-td>
      </template>

      <template #body-cell-source="slotProps">
        <q-td :props="slotProps">
          <template v-if="slotProps.row.source">
            <div class="row items-center no-wrap q-gutter-x-xs">
              <q-img
                v-if="getSourceVisual(slotProps.row.source.type).image"
                :src="getSourceVisual(slotProps.row.source.type).image"
                width="14px"
                height="14px"
                no-spinner
                no-transition
              />
              <q-icon v-else :name="getSourceVisual(slotProps.row.source.type).icon" size="14px" color="grey-6" />
              <span class="compact-source-name ellipsis" style="max-width: 180px">
                {{ slotProps.row.source.name }}
              </span>
            </div>
          </template>
          <span v-else class="text-grey-5">—</span>
        </q-td>
      </template>

      <template #body-cell-samples="slotProps">
        <q-td :props="slotProps">
          <div class="row items-center no-wrap q-gutter-x-xs">
            <template v-if="slotProps.row.sample_values?.length">
              <span v-for="sample in slotProps.row.sample_values.slice(0, 2)" :key="sample" class="sample-chip-sm">
                {{ truncateValue(sample, 16) }}
              </span>
              <span v-if="slotProps.row.sample_values.length > 2" class="sample-more">+{{ slotProps.row.sample_values.length - 2 }}</span>
            </template>
            <span v-else class="text-grey-5">—</span>
          </div>
        </q-td>
      </template>

      <template #body-cell-actions="slotProps">
        <q-td :props="slotProps" class="text-right">
          <q-btn dense flat round color="grey-7" icon="more_vert" size="sm" @click.stop>
            <q-menu class="field-menu" anchor="bottom right" self="top right" auto-close>
              <q-list dense>
                <template v-if="slotProps.row.is_defined">
                  <q-item v-ripple="false" clickable @click="editDefinedField(slotProps.row)">
                    <q-item-section thumbnail>
                      <q-icon name="o_edit" color="primary" size="18px" class="q-ml-sm" />
                    </q-item-section>
                    <q-item-section>Edit</q-item-section>
                  </q-item>
                </template>
                <template v-else>
                  <q-item v-ripple="false" clickable @click="emit('define-field', slotProps.row)">
                    <q-item-section thumbnail>
                      <q-icon name="o_add" color="primary" size="18px" class="q-ml-sm" />
                    </q-item-section>
                    <q-item-section>Define Field</q-item-section>
                  </q-item>
                </template>
              </q-list>
            </q-menu>
          </q-btn>
        </q-td>
      </template>
    </q-table>

    <!-- Extracted Fields Table -->
    <q-table
      v-else-if="selectedCategory === 'extracted'"
      v-model:pagination="extractedPagination"
      :rows="extractedRows"
      :columns="extractedColumns"
      row-key="id"
      flat
      bordered
      dense
      :rows-per-page-options="[5]"
      class="compact-table"
    >
      <template #body-cell-field="slotProps">
        <q-td :props="slotProps">
          <div class="row items-center no-wrap q-gutter-x-xs">
            <span class="compact-field-name ellipsis" style="max-width: 280px">
              {{ slotProps.row.display_name || slotProps.row.name }}
            </span>
          </div>
        </q-td>
      </template>

      <template #body-cell-type="slotProps">
        <q-td :props="slotProps">
          <span class="compact-type">{{ getTypeLabel(slotProps.row.value_type) }}</span>
        </q-td>
      </template>

      <template #body-cell-source="slotProps">
        <q-td :props="slotProps">
          <template v-if="slotProps.row.source">
            <div class="row items-center no-wrap q-gutter-x-xs">
              <q-img
                v-if="getSourceVisual(slotProps.row.source.type).image"
                :src="getSourceVisual(slotProps.row.source.type).image"
                width="14px"
                height="14px"
                no-spinner
                no-transition
              />
              <q-icon v-else :name="getSourceVisual(slotProps.row.source.type).icon" size="14px" color="grey-6" />
              <span class="compact-source-name ellipsis" style="max-width: 180px">
                {{ slotProps.row.source.name }}
              </span>
            </div>
          </template>
          <span v-else class="text-grey-5">—</span>
        </q-td>
      </template>

      <template #body-cell-samples="slotProps">
        <q-td :props="slotProps">
          <div class="row items-center no-wrap q-gutter-x-xs">
            <template v-if="slotProps.row.sample_values?.length">
              <span v-for="sample in slotProps.row.sample_values.slice(0, 2)" :key="sample" class="sample-chip-sm">
                {{ truncateValue(sample, 16) }}
              </span>
              <span v-if="slotProps.row.sample_values.length > 2" class="sample-more">+{{ slotProps.row.sample_values.length - 2 }}</span>
            </template>
            <span v-else class="text-grey-5">—</span>
          </div>
        </q-td>
      </template>

      <template #body-cell-actions="slotProps">
        <q-td :props="slotProps" class="text-right">
          <q-btn dense flat round color="grey-7" icon="more_vert" size="sm" @click.stop>
            <q-menu class="field-menu" anchor="bottom right" self="top right" auto-close>
              <q-list dense>
                <template v-if="slotProps.row.is_defined">
                  <q-item v-ripple="false" clickable @click="editDefinedField(slotProps.row)">
                    <q-item-section thumbnail>
                      <q-icon name="o_edit" color="primary" size="18px" class="q-ml-sm" />
                    </q-item-section>
                    <q-item-section>Edit</q-item-section>
                  </q-item>
                </template>
                <template v-else>
                  <q-item v-ripple="false" clickable @click="emit('define-field', slotProps.row)">
                    <q-item-section thumbnail>
                      <q-icon name="o_add" color="primary" size="18px" class="q-ml-sm" />
                    </q-item-section>
                    <q-item-section>Define Field</q-item-section>
                  </q-item>
                </template>
              </q-list>
            </q-menu>
          </q-btn>
        </q-td>
      </template>
    </q-table>
  </km-section>
</template>

<script setup lang="ts">
import confluenceImage from '@/assets/brands/atlassian-confluence.png'
import fluidTopicsImage from '@/assets/brands/fluid-topics.png'
import sharepointImage from '@/assets/brands/sharepoint.svg'
import type { QTableColumn } from 'quasar'
import { computed, ref, watch } from 'vue'
import { KgDropdownField } from '../common'
import { MetadataFieldDefinition, MetadataFieldRow, MetadataOrigin, MetadataOriginLabels, MetadataValueType, ValueTypeOptions } from './models'

// Source type visuals (image or icon)
const sourceTypeVisuals: Record<string, { image?: string; icon?: string }> = {
  upload: { icon: 'upload' },
  sharepoint: { image: sharepointImage },
  fluid_topics: { image: fluidTopicsImage },
  confluence: { image: confluenceImage },
}

const getSourceVisual = (type: string) => {
  return sourceTypeVisuals[type] || { icon: 'description' }
}

type CategoryType = 'schema' | 'discovered' | 'extracted'
type DiscoveredFilterType = 'all' | 'undefined'

const props = defineProps<{
  definedFields: MetadataFieldDefinition[]
  discoveredFields: MetadataFieldRow[]
  availablePresets: Partial<MetadataFieldDefinition>[]
  loading: boolean
  canRunExtraction?: boolean
  runningExtraction?: boolean
}>()

const emit = defineEmits<{
  (e: 'add-field'): void
  (e: 'add-preset', preset: Partial<MetadataFieldDefinition>): void
  (e: 'edit-field', field: MetadataFieldDefinition): void
  (e: 'delete-field', field: MetadataFieldDefinition): void
  (e: 'define-field', row: MetadataFieldRow): void
  (e: 'run-extraction'): void
}>()

const selectedCategory = ref<CategoryType>('schema')
const discoveredFilter = ref<DiscoveredFilterType>('undefined')
const search = ref('')
const schemaPagination = ref({ rowsPerPage: 5, page: 1 })
const discoveredPagination = ref({ rowsPerPage: 5, page: 1 })
const extractedPagination = ref({ rowsPerPage: 5, page: 1 })

// Maps for quick lookups
const defsByName = computed(() => new Map((props.definedFields || []).map((f) => [f.name, f] as const)))

// Counts
const schemaCount = computed(() => (props.definedFields || []).length)
const discoveredCount = computed(() => (props.discoveredFields || []).filter((f) => f.origin !== 'llm').length)
const extractedCount = computed(() => (props.discoveredFields || []).filter((f) => f.origin === 'llm').length)
const undefinedDiscoveredCount = computed(() => (props.discoveredFields || []).filter((f) => !f.is_defined && f.origin !== 'llm').length)

// Category tabs config
const categories = computed(() => [
  { value: 'schema' as const, label: 'Schema', count: schemaCount.value, icon: 'tune' },
  { value: 'discovered' as const, label: 'Discovered', count: discoveredCount.value, icon: 'explore' },
  { value: 'extracted' as const, label: 'Extracted', count: extractedCount.value, icon: 'smart_toy' },
])

// Discovered filter dropdown options
const discoveredFilterOptions = computed(() => [
  { label: `Needs Schema (${undefinedDiscoveredCount.value})`, value: 'undefined' },
  { label: `All (${discoveredCount.value})`, value: 'all' },
])

// Section title and subtitle based on category
const sectionTitle = computed(() => {
  if (selectedCategory.value === 'schema') return 'Schema Fields'
  if (selectedCategory.value === 'extracted') return 'Extracted Fields'
  return 'Discovered Fields'
})
const sectionSubtitle = computed(() => {
  if (selectedCategory.value === 'schema') {
    return 'User-defined metadata field definitions that structure your knowledge graph'
  }
  if (selectedCategory.value === 'extracted') {
    return 'Metadata fields extracted by AI/LLM from document content'
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

// Filtered rows for Discovered table (excludes LLM-extracted)
const discoveredRows = computed(() => {
  // Exclude LLM-origin fields from discovered - those go to "extracted" tab
  let rows = (props.discoveredFields || []).filter((r) => r.origin !== 'llm')

  // Apply sub-filter
  if (discoveredFilter.value === 'undefined') {
    rows = rows.filter((r) => !r.is_defined)
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

// Filtered rows for Extracted table (LLM-origin only)
const extractedRows = computed(() => {
  let rows = (props.discoveredFields || []).filter((r) => r.origin === 'llm')

  if (!search.value) return rows

  const s = search.value.toLowerCase()
  return rows.filter(
    (r) =>
      r.name.toLowerCase().includes(s) ||
      (r.display_name || '').toLowerCase().includes(s) ||
      r.sample_values?.some((v) => v.toLowerCase().includes(s))
  )
})

// Empty state logic
const showEmptyState = computed(() => {
  if (props.loading) return false
  if (selectedCategory.value === 'schema') {
    return schemaRows.value.length === 0
  }
  if (selectedCategory.value === 'extracted') {
    return extractedRows.value.length === 0
  }
  return discoveredRows.value.length === 0
})

const emptyStateIcon = computed(() => {
  if (search.value) return 'search_off'
  if (selectedCategory.value === 'schema') return 'category'
  if (selectedCategory.value === 'extracted') return 'smart_toy'
  if (discoveredFilter.value === 'undefined') return 'check_circle'
  return 'explore'
})

const emptyStateTitle = computed(() => {
  if (search.value) return 'No matching fields'
  if (selectedCategory.value === 'schema') return 'No schema fields defined'
  if (selectedCategory.value === 'extracted') return 'No extracted fields'
  if (discoveredFilter.value === 'undefined') return 'All fields are defined'
  return 'No discovered fields'
})

const emptyStateSubtitle = computed(() => {
  if (search.value) return 'Try a different search term'
  if (selectedCategory.value === 'schema') return 'Add a field definition to start building your metadata schema'
  if (selectedCategory.value === 'extracted') return 'Run extraction to detect metadata fields using AI'
  if (discoveredFilter.value === 'undefined') return 'All discovered fields have been added to the schema'
  return 'Sync sources to discover metadata fields from your documents'
})

// Schema table columns
const schemaColumns = computed<QTableColumn<MetadataFieldDefinition>[]>(() => [
  { name: 'field', label: 'Field', field: 'name', align: 'left', sortable: true },
  { name: 'type', label: 'Type', field: 'value_type', align: 'left', sortable: true, style: 'width: 100px' },
  { name: 'constraints', label: 'Constraints', field: () => '', align: 'left', style: 'width: 180px' },
  { name: 'actions', label: '', field: 'name', align: 'right', style: 'width: 60px' },
])

// Discovered table columns
const discoveredColumns = computed<QTableColumn<MetadataFieldRow>[]>(() => [
  { name: 'field', label: 'Field', field: 'name', align: 'left', sortable: true },
  { name: 'type', label: 'Type', field: 'value_type', align: 'left', sortable: true, style: 'width: 100px' },
  { name: 'source', label: 'Source', field: () => '', align: 'left', style: 'width: 260px' },
  { name: 'origin', label: 'Origin', field: () => '', align: 'left', style: 'width: 220px' },
  { name: 'samples', label: 'Sample Values', field: () => '', align: 'left' },
  { name: 'actions', label: '', field: 'name', align: 'right', style: 'width: 80px' },
])

// Extracted table columns
const extractedColumns = computed<QTableColumn<MetadataFieldRow>[]>(() => [
  { name: 'field', label: 'Field', field: 'name', align: 'left', sortable: true },
  { name: 'type', label: 'Type', field: 'value_type', align: 'left', sortable: true, style: 'width: 100px' },
  { name: 'source', label: 'Source', field: () => '', align: 'left', style: 'width: 260px' },
  { name: 'samples', label: 'Sample Values', field: () => '', align: 'left' },
  { name: 'actions', label: '', field: 'name', align: 'right', style: 'width: 80px' },
])

// Helper functions
const getTypeLabel = (type: MetadataValueType) => ValueTypeOptions.find((t) => t.value === type)?.label || type
const getOriginLabel = (origin: MetadataOrigin) => MetadataOriginLabels[origin]

const truncateValue = (value: string, maxLength = 30) => {
  return value.length > maxLength ? value.substring(0, maxLength) + '…' : value
}

const editDefinedField = (row: MetadataFieldRow) => {
  const def = defsByName.value.get(row.name)
  if (def) emit('edit-field', def)
}

// Reset pagination on filter changes
watch([search, selectedCategory, discoveredFilter], () => {
  schemaPagination.value.page = 1
  discoveredPagination.value.page = 1
  extractedPagination.value.page = 1
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
  border-radius: 4px;
}

.category-tab {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: transparent;
  border: none;
  border-radius: 4px;
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

/* Table styles - compact and light */
:deep(.q-table thead th) {
  font-size: 12px;
  font-weight: 500;
  color: #6b7280;
  padding: 8px 12px;
}

:deep(.q-table tbody td) {
  font-size: 12px;
  padding: 6px 12px;
}

:deep(.q-table tbody tr) {
  cursor: default;
}

:deep(.compact-table tbody tr) {
  cursor: pointer;
}

:deep(.q-table--bordered) {
  border-color: #e5e7eb;
}

:deep(.q-table tbody tr:hover) {
  background: #fafafa;
}

/* Compact table styles (shared by all tables) */
:deep(.compact-table thead th) {
  padding: 6px 12px;
  font-size: 13px;
  background: #f9fafb !important;
}

:deep(.compact-table tbody td) {
  padding: 8px 12px;
}

.compact-field-name {
  font-size: 12px;
  font-weight: 500;
  color: #374151;
}

.compact-type {
  font-size: 11px;
  color: #6b7280;
}

.compact-constraint {
  font-size: 11px;
  color: #6b7280;
}

.compact-source-name {
  font-size: 12px;
  color: #4b5563;
}

/* Sample chips - compact */
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

.sample-chip-sm {
  display: inline-block;
  padding: 2px 8px;
  background: #f3f4f6;
  border-radius: 4px;
  font-size: 11px;
  color: #4b5563;
  max-width: 100px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sample-more {
  font-size: 11px;
  color: #6b7280;
}

/* Origin chips (Discovered table) */
.origin-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 2px 8px;
  border-radius: 4px;
  font-size: 11px;
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

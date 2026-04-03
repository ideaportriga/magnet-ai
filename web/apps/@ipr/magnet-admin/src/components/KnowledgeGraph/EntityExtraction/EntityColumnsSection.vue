<template>
  <kg-dialog-section
    title="Columns"
    description="Define the columns (attributes) for this entity. Mark one column as the identifier to serve as a unique key."
    icon="o_view_column"
    icon-color="teal"
  >
    <div class="entity-columns-list">
      <div v-if="columns.length === 0" class="entity-columns-empty">
        <q-icon name="o_view_column" size="28px" color="grey-4" />
        <div class="text-grey-6 text-caption q-mt-xs">No columns defined yet</div>
        <q-btn no-caps unelevated color="teal-8" icon="add" label="Add Column" class="entity-add-col-btn q-mt-sm" @click="addColumn" />
      </div>

      <div v-for="(col, idx) in columns" :key="col.id" class="entity-column-card" :class="{ 'entity-column-card--identifier': col.is_identifier }">
        <div class="entity-column-header" @click="toggleColumnExpand(col.id)">
          <div class="entity-column-header__left">
            <q-icon
              :name="expandedColumns.has(col.id) ? 'expand_less' : 'expand_more'"
              size="20px"
              color="grey-6"
              class="entity-column-toggle-icon"
            />
            <span class="entity-column-name" :class="{ 'text-grey-5': !col.name }">{{ col.name || 'Unnamed' }}</span>
            <q-badge v-if="col.is_identifier" color="amber-8" text-color="white" class="entity-column-id-badge">ID</q-badge>
            <q-badge v-if="col.is_required" color="blue-7" text-color="white" class="entity-column-id-badge">REQ</q-badge>
          </div>
          <div class="entity-column-header__right">
            <q-btn flat dense round icon="delete_outline" size="sm" color="red-5" class="entity-col-action-btn" @click.stop="removeColumn(idx)" />
          </div>
        </div>

        <div v-if="expandedColumns.has(col.id)" class="entity-column-body">
          <div class="entity-column-grid">
            <kg-field-row :cols="1" label="Column name">
              <km-input
                :model-value="col.name"
                outlined
                dense
                placeholder="e.g. product_id"
                class="entity-col-control entity-col-field-name"
                @update:model-value="updateColumnName(idx, $event)"
              />
            </kg-field-row>

            <kg-field-row :cols="1" label="Type">
              <kg-dropdown-field
                :model-value="col.type"
                :options="columnTypeOptions"
                placeholder="Select type"
                option-value="value"
                option-label="label"
                dense
                class="entity-col-control"
                @update:model-value="updateColumnType(idx, $event)"
              />
            </kg-field-row>

            <kg-field-row :cols="1" label="Identifier" class="entity-col-field--identifier">
              <div
                class="entity-col-identifier-toggle"
                :class="{ 'entity-col-identifier-toggle--active': col.is_identifier }"
                role="button"
                tabindex="0"
                :aria-pressed="col.is_identifier"
                @click="setIdentifier(idx, !col.is_identifier)"
                @keydown.enter.prevent="setIdentifier(idx, !col.is_identifier)"
                @keydown.space.prevent="setIdentifier(idx, !col.is_identifier)"
              >
                <span class="entity-col-identifier-toggle__label">
                  {{ col.is_identifier ? 'Primary identifier' : 'Mark as identifier' }}
                </span>
                <q-toggle
                  :model-value="col.is_identifier"
                  dense
                  size="sm"
                  color="amber-8"
                  keep-color
                  @update:model-value="setIdentifier(idx, $event)"
                  @click.stop
                />
              </div>
            </kg-field-row>

            <kg-field-row :cols="1" label="Required" class="entity-col-field--required">
              <div
                class="entity-col-identifier-toggle entity-col-required-toggle"
                :class="{ 'entity-col-required-toggle--active': col.is_required, 'entity-col-required-toggle--locked': col.is_identifier }"
                :role="col.is_identifier ? undefined : 'button'"
                :tabindex="col.is_identifier ? -1 : 0"
                :aria-pressed="col.is_required"
                @click="!col.is_identifier && updateColumn(idx, { is_required: !col.is_required })"
                @keydown.enter.prevent="!col.is_identifier && updateColumn(idx, { is_required: !col.is_required })"
                @keydown.space.prevent="!col.is_identifier && updateColumn(idx, { is_required: !col.is_required })"
              >
                <span class="entity-col-identifier-toggle__label">
                  {{ col.is_required ? 'Required field' : 'Mark as required' }}
                </span>
                <q-toggle
                  :model-value="col.is_required"
                  :disable="col.is_identifier"
                  dense
                  size="sm"
                  @update:model-value="!col.is_identifier && updateColumn(idx, { is_required: $event })"
                  @click.stop
                />
              </div>
            </kg-field-row>

            <kg-field-row :cols="1" label="Description" class="entity-col-field--description">
              <km-input
                :model-value="col.description"
                outlined
                dense
                type="textarea"
                autogrow
                placeholder="Explain what this column captures and how it should be used"
                :input-style="{ minHeight: '84px', maxHeight: '160px' }"
                @update:model-value="updateColumnDescription(idx, $event)"
              />
            </kg-field-row>
          </div>
        </div>
      </div>

      <button v-if="columns.length > 0" class="entity-add-col-btn-dashed" @click="addColumn">
        <q-icon name="add" size="16px" />
        <span>Add Column</span>
      </button>
    </div>
  </kg-dialog-section>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { m } from '@/paraglide/messages'
import { KgDialogSection, KgDropdownField, KgFieldRow } from '../common'
import { ColumnTypeOptions, createEmptyColumn, type EntityColumn, type EntityColumnType } from './models'

interface Props {
  columns: EntityColumn[]
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'update:columns': [columns: EntityColumn[]]
}>()

const columnTypeOptions = ColumnTypeOptions
const expandedColumns = ref<Set<string>>(new Set())

watch(
  () => props.columns.map((column) => column.id),
  (columnIds, previousColumnIds) => {
    const idsChanged =
      !previousColumnIds ||
      columnIds.length !== previousColumnIds.length ||
      columnIds.some((columnId, index) => columnId !== previousColumnIds[index])

    if (!idsChanged) {
      return
    }

    const columnIdSet = new Set(columnIds)
    const nextExpandedColumns = new Set([...expandedColumns.value].filter((columnId) => columnIdSet.has(columnId)))

    if (nextExpandedColumns.size === 0 && columnIds.length > 0) {
      nextExpandedColumns.add(columnIds[0])
    }

    expandedColumns.value = nextExpandedColumns
  },
  { immediate: true }
)

function emitColumns(columns: EntityColumn[]) {
  emit('update:columns', columns)
}

function toggleColumnExpand(columnId: string) {
  const nextExpandedColumns = new Set(expandedColumns.value)
  if (nextExpandedColumns.has(columnId)) nextExpandedColumns.delete(columnId)
  else nextExpandedColumns.add(columnId)
  expandedColumns.value = nextExpandedColumns
}

function addColumn() {
  const column = createEmptyColumn()
  expandedColumns.value = new Set([...expandedColumns.value, column.id])
  emitColumns([...props.columns, column])
}

function removeColumn(idx: number) {
  const removedColumnId = props.columns[idx]?.id
  if (!removedColumnId) {
    return
  }

  const nextExpandedColumns = new Set(expandedColumns.value)
  nextExpandedColumns.delete(removedColumnId)
  expandedColumns.value = nextExpandedColumns

  emitColumns(props.columns.filter((_, index) => index !== idx))
}

function updateColumn(idx: number, patch: Partial<EntityColumn>) {
  emitColumns(props.columns.map((column, index) => (index === idx ? { ...column, ...patch } : column)))
}

function updateColumnName(idx: number, value: string) {
  updateColumn(idx, { name: value })
}

function updateColumnType(idx: number, value: string | string[] | undefined) {
  const typed = Array.isArray(value) ? value[0] : value
  if (typed != null && typed !== '') {
    updateColumn(idx, { type: typed as EntityColumnType })
  }
}

function updateColumnDescription(idx: number, value: string) {
  updateColumn(idx, { description: value })
}

function setIdentifier(idx: number, value: boolean) {
  emitColumns(
    props.columns.map((column, index) => {
      if (value) {
        // The column being set as identifier is also forced required
        return { ...column, is_identifier: index === idx, ...(index === idx ? { is_required: true } : {}) }
      }

      if (index === idx) {
        return { ...column, is_identifier: false }
      }

      return column
    })
  )
}
</script>

<style scoped>
.entity-add-col-btn {
  font-size: var(--km-font-size-caption);
  font-weight: 600;
  border-radius: var(--radius-md);
}

.entity-add-col-btn-dashed {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  width: 100%;
  padding: 9px 0;
  font-size: var(--km-font-size-caption);
  font-weight: 600;
  color: var(--q-primary);
  background: transparent;
  border: 1.5px dashed var(--q-border);
  border-radius: var(--radius-lg);
  cursor: pointer;
  transition:
    border-color 0.15s ease,
    background 0.15s ease,
    color 0.15s ease;
}

.entity-add-col-btn-dashed:hover {
  border-color: var(--q-primary);
  background: var(--q-primary-bg);
  color: var(--q-primary-text);
}

.entity-columns-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.entity-columns-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 24px 16px;
}

.entity-column-card {
  background: var(--q-white);
  border: 1px solid var(--q-border);
  border-radius: var(--radius-lg);
  overflow: hidden;
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.entity-column-card:hover {
  border-color: var(--q-border-2);
}

.entity-column-card--identifier {
  border-color: #f0c040;
  box-shadow: inset 2px 0 0 0 #f0c040;
}

.entity-column-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 12px;
  cursor: pointer;
  user-select: none;
  background: var(--q-background);
  border-bottom: 1px solid transparent;
  transition: background 0.15s ease;
}

.entity-column-header:hover {
  background: var(--q-light);
}

.entity-column-card:has(.entity-column-body) .entity-column-header {
  border-bottom-color: var(--q-border);
}

.entity-column-header__left {
  display: flex;
  align-items: center;
  gap: 8px;
  min-width: 0;
  overflow: hidden;
}

.entity-column-header__right {
  display: flex;
  align-items: center;
  gap: 2px;
  flex-shrink: 0;
}

.entity-column-toggle-icon {
  flex-shrink: 0;
  transition: transform 0.15s ease;
}

.entity-column-name {
  font-size: var(--km-font-size-label);
  font-weight: 600;
  color: var(--q-black);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.entity-column-id-badge {
  font-size: 9px;
  font-weight: 700;
  padding: 2px 5px;
  border-radius: var(--radius-xs);
  letter-spacing: 0.5px;
}

.entity-col-action-btn {
  opacity: 0;
  transition:
    opacity 0.15s ease,
    color 0.15s ease;
}

.entity-column-header:hover .entity-col-action-btn {
  opacity: 1;
}

.entity-col-action-btn:hover {
  color: var(--q-error) !important;
}

.entity-column-body {
  padding: 14px 14px 12px;
  background: var(--q-white);
}

.entity-column-grid {
  display: grid;
  grid-template-columns: minmax(0, 1.6fr) minmax(160px, 0.9fr) minmax(180px, 0.85fr) minmax(180px, 0.85fr);
  gap: 12px;
  align-items: start;
}

.entity-col-field--description {
  grid-column: 1 / -1;
}

.entity-col-control :deep(.q-field__control) {
  height: 40px !important;
  min-height: 40px !important;
  max-height: 40px !important;
}

.entity-col-control :deep(.q-field__native),
.entity-col-control :deep(.q-field__input),
.entity-col-control :deep(.q-field__marginal) {
  min-height: 40px !important;
}

.entity-col-identifier-toggle {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  min-height: 40px;
  height: 40px;
  padding: 0 12px;
  cursor: pointer;
  border: 1px solid var(--q-border);
  border-radius: var(--radius-sm);
  background: var(--q-white);
  transition:
    border-color 0.15s ease,
    background 0.15s ease,
    box-shadow 0.15s ease;
}

.entity-col-identifier-toggle:hover {
  border-color: #c9a54b;
  background: #fffaf0;
}

.entity-col-identifier-toggle:focus-visible {
  outline: none;
  box-shadow: 0 0 0 3px rgba(240, 192, 64, 0.16);
}

.entity-col-identifier-toggle--active {
  border-color: #f0c040;
  background: #fff8e1;
  box-shadow: inset 0 0 0 1px rgba(240, 192, 64, 0.12);
}

.entity-col-required-toggle--locked {
  cursor: default;
  opacity: 0.75;
}

.entity-col-identifier-toggle__label {
  min-width: 0;
  font-size: var(--km-font-size-label);
  font-weight: 600;
  color: var(--q-black);
}

@media (max-width: 1100px) {
  .entity-column-grid {
    grid-template-columns: minmax(0, 1fr) minmax(180px, 220px);
  }

  .entity-col-field--identifier,
  .entity-col-field--required {
    grid-column: 1 / -1;
  }
}

@media (max-width: 720px) {
  .entity-column-grid {
    grid-template-columns: 1fr;
  }
}
</style>

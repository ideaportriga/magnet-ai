<template>
  <!--
    §E.2.4 — migrated from q-table to km-data-table.
    Two modes:
      • Entity-types list: local pagination via useLocalDataTable.
      • Entity-records: server-side pagination — useVueTable wired up
        with manualPagination + external state driven by parent props.
  -->
  <div v-if="!selectedEntityType" class="km-table-scroll">
    <km-data-table
      :table="typesTable"
      row-key="entity"
      hide-pagination
      @row-click="onEntityTypeClick"
    >
      <template #cell-menu="{ row }">
        <q-btn dense flat color="dark" icon="more_vert" :disable="deletingEntityTypes.has(row.entity)" @click.stop>
          <q-menu anchor="bottom right" self="top right" auto-close>
            <q-list dense>
              <q-item clickable @click="emit('delete-entity-type', row)">
                <q-item-section thumbnail>
                  <q-icon name="delete" color="negative" size="20px" class="q-ml-sm" />
                </q-item-section>
                <q-item-section>{{ m.dataExplorer_deleteAllEntities() }}</q-item-section>
              </q-item>
            </q-list>
          </q-menu>
        </q-btn>
      </template>
    </km-data-table>
  </div>

  <div v-else class="km-table-scroll">
    <km-data-table :table="recordsTable" row-key="id">
      <template #cell-menu="{ row }">
        <q-btn dense flat color="dark" icon="more_vert" :disable="deletingEntityRecordIds.has(row.id)" @click.stop>
          <q-menu anchor="bottom right" self="top right" auto-close>
            <q-list dense>
              <q-item clickable @click="emit('delete-entity-record', row)">
                <q-item-section thumbnail>
                  <q-icon name="delete" color="negative" size="20px" class="q-ml-sm" />
                </q-item-section>
                <q-item-section>{{ m.common_delete() }}</q-item-section>
              </q-item>
            </q-list>
          </q-menu>
        </q-btn>
      </template>
    </km-data-table>
  </div>
</template>

<script setup lang="ts">
import { m } from '@/paraglide/messages'
import { computed, ref, watch } from 'vue'
import type { ColumnDef, PaginationState, Updater } from '@tanstack/vue-table'
import { useVueTable, getCoreRowModel } from '@tanstack/vue-table'
import { useLocalDataTable } from '@/composables/useLocalDataTable'
import { getEntityDefinitionsFromSettings } from '../EntityExtraction/models'
import type { EntityRecord, EntityTypeSummary } from './models'

type EntityRecordsPagination = {
  page: number
  rowsPerPage: number
  rowsNumber?: number
}

type EntityRecordsRequest = Record<string, unknown> & {
  pagination: EntityRecordsPagination
}

const props = defineProps<{
  graphDetails: Record<string, unknown>
  entityTypes: EntityTypeSummary[]
  selectedEntityType: string | null
  entityRecords: EntityRecord[]
  entityRecordsPagination: EntityRecordsPagination
  deletingEntityTypes: Set<string>
  deletingEntityRecordIds: Set<string>
}>()

const emit = defineEmits<{
  'select-entity-type': [row: EntityTypeSummary]
  'request-entity-records': [request: EntityRecordsRequest]
  'delete-entity-type': [row: EntityTypeSummary]
  'delete-entity-record': [row: EntityRecord]
  'update:entityRecordsPagination': [pagination: EntityRecordsPagination]
}>()

function applyUpdater<T>(updater: Updater<T>, current: T): T {
  return typeof updater === 'function' ? (updater as (old: T) => T)(current) : updater
}

function formatEntityCellValue(value: unknown) {
  if (value == null) return '—'
  if (Array.isArray(value)) return value.map((item) => formatEntityCellValue(item)).join(', ')
  if (typeof value === 'object') {
    try {
      return JSON.stringify(value)
    } catch {
      return String(value)
    }
  }
  if (typeof value === 'boolean') return value ? m.common_trueValue() : m.common_falseValue()
  return String(value)
}

// ── Entity types table (local pagination) ───────────────────────────
const entityTypesColumns: ColumnDef<EntityTypeSummary, unknown>[] = [
  {
    id: 'entity',
    accessorKey: 'entity',
    header: m.knowledgeGraph_entityLabel(),
    enableSorting: true,
    meta: { align: 'left' },
  },
  {
    id: 'count',
    accessorKey: 'count',
    header: m.common_records(),
    enableSorting: true,
    meta: { align: 'left' },
  },
  {
    id: 'menu',
    header: '',
    enableSorting: false,
    meta: { align: 'right', width: '50px' },
  },
]

const entityTypesRef = computed(() => props.entityTypes)
const { table: typesTable } = useLocalDataTable<EntityTypeSummary>(
  entityTypesRef,
  entityTypesColumns,
  { defaultPageSize: 100 },
)

function onEntityTypeClick(row: EntityTypeSummary) {
  emit('select-entity-type', row)
}

// ── Entity records table (server-side pagination) ───────────────────
// Columns are dynamic — identifier first, then one column per entity
// definition column, then a menu column. They are recomputed whenever
// graphDetails / selectedEntityType / entityRecords change.
const entityRecordsColumns = computed<ColumnDef<EntityRecord, unknown>[]>(() => {
  const entityDefinitions = getEntityDefinitionsFromSettings(
    props.graphDetails?.settings as Record<string, unknown> | undefined,
  )
  const definition = entityDefinitions.find((item) => item.name === props.selectedEntityType)
  const identifierColumn = definition?.columns.find((column) => column.is_identifier)
  const identifierLabel = identifierColumn?.name || 'Identifier'

  const cols: ColumnDef<EntityRecord, unknown>[] = [
    {
      id: 'record_identifier',
      accessorKey: 'record_identifier',
      header: identifierLabel,
      enableSorting: true,
      cell: ({ getValue }) => {
        const v = getValue()
        return v == null ? '—' : formatEntityCellValue(v)
      },
      meta: { align: 'left' },
    },
  ]

  const columnNames: string[] = []
  if (definition) {
    for (const column of definition.columns) {
      if (column.is_identifier) continue
      columnNames.push(column.name)
    }
  } else {
    const allKeys = new Set<string>()
    for (const record of props.entityRecords) {
      if (!record.column_values) continue
      for (const key of Object.keys(record.column_values)) allKeys.add(key)
    }
    for (const key of allKeys) columnNames.push(key)
  }

  for (const name of columnNames) {
    cols.push({
      id: `col_${name}`,
      accessorFn: (row: EntityRecord) => row.column_values?.[name] ?? null,
      header: name,
      enableSorting: false,
      cell: ({ getValue }) => {
        const v = getValue()
        return v == null ? '—' : formatEntityCellValue(v)
      },
      meta: { align: 'left' },
    })
  }

  cols.push({
    id: 'menu',
    header: '',
    enableSorting: false,
    meta: { align: 'right', width: '50px' },
  })

  return cols
})

// External pagination — TanStack's PaginationState is 0-based, parent's
// `entityRecordsPagination` is 1-based. Convert on the edges.
const pagination = ref<PaginationState>({
  pageIndex: Math.max(0, (props.entityRecordsPagination?.page ?? 1) - 1),
  pageSize: props.entityRecordsPagination?.rowsPerPage ?? 10,
})

watch(
  () => props.entityRecordsPagination,
  (next) => {
    if (!next) return
    const idx = Math.max(0, (next.page ?? 1) - 1)
    if (pagination.value.pageIndex !== idx || pagination.value.pageSize !== (next.rowsPerPage ?? 10)) {
      pagination.value = { pageIndex: idx, pageSize: next.rowsPerPage ?? 10 }
    }
  },
  { deep: true },
)

const recordsTable = useVueTable<EntityRecord>({
  get data() { return props.entityRecords },
  get columns() { return entityRecordsColumns.value },
  getCoreRowModel: getCoreRowModel(),
  manualPagination: true,
  manualSorting: true,
  manualFiltering: true,
  get pageCount() {
    const total = props.entityRecordsPagination?.rowsNumber ?? 0
    const size = pagination.value.pageSize || 1
    return Math.max(1, Math.ceil(total / size))
  },
  get rowCount() {
    return props.entityRecordsPagination?.rowsNumber ?? props.entityRecords.length
  },
  state: {
    get pagination() { return pagination.value },
  },
  onPaginationChange: (updater) => {
    const next = applyUpdater(updater, pagination.value)
    if (next.pageIndex === pagination.value.pageIndex && next.pageSize === pagination.value.pageSize) {
      return
    }
    pagination.value = next
    const outgoing: EntityRecordsPagination = {
      page: next.pageIndex + 1,
      rowsPerPage: next.pageSize,
      rowsNumber: props.entityRecordsPagination?.rowsNumber,
    }
    emit('update:entityRecordsPagination', outgoing)
    emit('request-entity-records', { pagination: outgoing })
  },
})
</script>

<style scoped>
:deep(.sticky-col) {
  position: sticky;
  right: 0;
  z-index: 1;
  background: var(--q-white);
}
:deep(tr:hover .sticky-col) {
  background: var(--q-white);
}
:deep(thead th:last-child) {
  position: sticky;
  right: 0;
  z-index: 2;
  background: inherit;
}
</style>

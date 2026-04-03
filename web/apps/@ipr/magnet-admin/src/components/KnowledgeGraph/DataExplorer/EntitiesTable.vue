<template>
  <div v-if="!selectedEntityType">
    <q-table
      flat
      table-header-class="bg-primary-light"
      :rows="entityTypes"
      :columns="entityTypesColumns"
      row-key="entity"
      :rows-per-page-options="[10]"
      @row-click="handleEntityTypeClick"
    >
      <template #body-cell-menu="slotScope">
        <q-td :props="slotScope" class="sticky-col">
          <q-btn dense flat color="dark" icon="more_vert" :disable="deletingEntityTypes.has(slotScope.row.entity)" @click.stop>
            <q-menu anchor="bottom right" self="top right" auto-close>
              <q-list dense>
                <q-item clickable @click="emit('delete-entity-type', slotScope.row)">
                  <q-item-section thumbnail>
                    <q-icon name="delete" color="negative" size="20px" class="q-ml-sm" />
                  </q-item-section>
                  <q-item-section>Delete All Records</q-item-section>
                </q-item>
              </q-list>
            </q-menu>
          </q-btn>
        </q-td>
      </template>
    </q-table>
  </div>

  <div v-else>
    <q-table
      v-model:pagination="paginationModel"
      flat
      table-header-class="bg-primary-light"
      :rows="entityRecords"
      :columns="entityRecordsColumns"
      row-key="id"
      :rows-per-page-options="[10]"
      @request="handleEntityRecordsRequest"
    >
      <template #body-cell="slotScope">
        <q-td :props="slotScope">
          <span v-if="slotScope.value == null" class="text-grey-5">—</span>
          <span v-else>
            {{ slotScope.col.format ? slotScope.col.format(slotScope.value, slotScope.row) : formatEntityCellValue(slotScope.value) }}
          </span>
        </q-td>
      </template>
      <template #header-cell-record_identifier="slotScope">
        <q-th :props="slotScope">
          <span>
            {{ slotScope.col.label }}
            <q-icon name="o_key" size="14px" color="amber-8" class="q-ml-6" />
          </span>
        </q-th>
      </template>
      <template #body-cell-menu="slotScope">
        <q-td :props="slotScope" class="sticky-col">
          <q-btn dense flat color="dark" icon="more_vert" :disable="deletingEntityRecordIds.has(slotScope.row.id)" @click.stop>
            <q-menu anchor="bottom right" self="top right" auto-close>
              <q-list dense>
                <q-item clickable @click="emit('delete-entity-record', slotScope.row)">
                  <q-item-section thumbnail>
                    <q-icon name="delete" color="negative" size="20px" class="q-ml-sm" />
                  </q-item-section>
                  <q-item-section>Delete</q-item-section>
                </q-item>
              </q-list>
            </q-menu>
          </q-btn>
        </q-td>
      </template>
    </q-table>
  </div>
</template>

<script setup lang="ts">
import type { QTableColumn } from 'quasar'
import { m } from '@/paraglide/messages'
import { computed } from 'vue'
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

const entityTypesColumns: QTableColumn<EntityTypeSummary>[] = [
  {
    name: 'entity',
    label: 'Entity',
    field: 'entity',
    align: 'left',
    sortable: true,
  },
  {
    name: 'count',
    label: 'Records',
    field: 'count',
    align: 'left',
    sortable: true,
  },
  {
    name: 'menu',
    label: '',
    field: 'entity',
    style: 'width: 50px',
    headerStyle: 'width: 50px',
  },
]

const entityRecordsColumns = computed<QTableColumn<EntityRecord>[]>(() => {
  const entityDefinitions = getEntityDefinitionsFromSettings(props.graphDetails?.settings as Record<string, unknown> | undefined)
  const definition = entityDefinitions.find((item) => item.name === props.selectedEntityType)
  const identifierColumn = definition?.columns.find((column) => column.is_identifier)
  const identifierLabel = identifierColumn?.name || 'Identifier'

  const columns: QTableColumn<EntityRecord>[] = [
    {
      name: 'record_identifier',
      label: identifierLabel,
      field: 'record_identifier',
      align: 'left',
      sortable: true,
    },
  ]

  if (definition) {
    for (const column of definition.columns) {
      if (column.is_identifier) {
        continue
      }

      columns.push({
        name: `col_${column.name}`,
        label: column.name,
        field: (row: EntityRecord) => row.column_values?.[column.name] ?? null,
        align: 'left',
        format: formatEntityCellValue,
      })
    }
  } else {
    const allKeys = new Set<string>()
    for (const record of props.entityRecords) {
      if (!record.column_values) {
        continue
      }

      for (const key of Object.keys(record.column_values)) {
        allKeys.add(key)
      }
    }

    for (const key of allKeys) {
      columns.push({
        name: `col_${key}`,
        label: key,
        field: (row: EntityRecord) => row.column_values?.[key] ?? null,
        align: 'left',
        format: formatEntityCellValue,
      })
    }
  }

  columns.push({
    name: 'menu',
    label: '',
    field: 'id',
    style: 'width: 50px',
    headerStyle: 'width: 50px',
  })

  return columns
})

const paginationModel = computed({
  get: () => props.entityRecordsPagination,
  set: (pagination: EntityRecordsPagination) => {
    emit('update:entityRecordsPagination', pagination)
  },
})

function formatEntityCellValue(value: unknown) {
  if (value == null) {
    return '—'
  }

  if (Array.isArray(value)) {
    return value.map((item) => formatEntityCellValue(item)).join(', ')
  }

  if (typeof value === 'object') {
    try {
      return JSON.stringify(value)
    } catch {
      return String(value)
    }
  }

  if (typeof value === 'boolean') {
    return value ? 'True' : 'False'
  }

  return String(value)
}

const handleEntityTypeClick = (_event: Event, row: EntityTypeSummary) => {
  emit('select-entity-type', row)
}

const handleEntityRecordsRequest = (request: EntityRecordsRequest) => {
  emit('request-entity-records', request)
}
</script>

<style scoped>
:deep(.q-table thead th) {
  font-size: var(--km-body-sm-size, 14px);
  font-weight: 600;
}

:deep(.q-table tbody td) {
  height: 40px;
  padding: 2px 16px;
}

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

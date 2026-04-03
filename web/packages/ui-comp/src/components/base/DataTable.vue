<template>
  <div class="km-data-table column no-wrap" :class="{ 'km-data-table--fill-height': fillHeight }">
    <!-- Table -->
    <div class="km-data-table__body col overflow-auto">
      <table class="km-data-table__table full-width">
        <thead class="km-data-table__header">
          <tr v-for="headerGroup in table.getHeaderGroups()" :key="headerGroup.id">
            <th
              v-for="header in headerGroup.headers"
              :key="header.id"
              class="km-data-table__th bg-primary-light q-px-md"
              :class="[`text-${header.column.columnDef.meta?.align ?? 'left'}`]"
              :style="header.column.columnDef.meta?.width ? { width: header.column.columnDef.meta.width } : {}"
              @click="header.column.getCanSort() ? header.column.toggleSorting() : undefined"
            >
              <div class="row inline items-center no-wrap" :class="{ 'cursor-pointer': header.column.getCanSort() }">
                <div class="km-title">
                  <FlexRender v-if="!header.isPlaceholder" :render="header.column.columnDef.header" :props="header.getContext()" />
                </div>
                <q-icon
                  v-if="header.column.getIsSorted()"
                  :name="header.column.getIsSorted() === 'desc' ? 'arrow_downward' : 'arrow_upward'"
                  size="14px"
                  class="q-ml-xs"
                />
              </div>
            </th>
          </tr>
        </thead>

        <tbody>
          <!-- Loading overlay -->
          <tr v-if="loading && rows.length === 0">
            <td :colspan="table.getAllColumns().length" class="text-center q-py-xl">
              <q-spinner size="40px" color="primary" />
            </td>
          </tr>

          <!-- Empty state -->
          <tr v-else-if="rows.length === 0">
            <td :colspan="table.getAllColumns().length" class="text-center q-py-xl">
              <slot name="empty-state">
                <div class="text-grey-6 km-description">{{ noRecordsLabel }}</div>
              </slot>
            </td>
          </tr>

          <!-- Data rows -->
          <tr
            v-for="row in rows"
            :key="row.id"
            class="km-data-table__row cursor-pointer"
            :class="{ 'bg-control-hover-bg': activeRowId && getRowKey(row) === activeRowId }"
            @click="emit('row-click', row.original)"
          >
            <td
              v-for="cell in row.getVisibleCells()"
              :key="cell.id"
              class="km-data-table__td q-px-md td-hoverable"
              :class="[`text-${cell.column.columnDef.meta?.align ?? 'left'}`, cell.column.columnDef.meta?.class]"
            >
              <slot :name="`cell-${cell.column.id}`" :cell="cell" :row="row.original" :value="cell.getValue()">
                <!-- Column with custom component (like km-table's type: 'component') -->
                <component
                  :is="resolveComponent(cell.column.columnDef.meta.component, cell, row)"
                  v-if="cell.column.columnDef.meta?.component"
                  :row="row.original"
                  v-bind="cell.column.columnDef.meta?.componentProps?.(row.original) ?? {}"
                />
                <!-- Default: FlexRender -->
                <FlexRender v-else :render="cell.column.columnDef.cell" :props="cell.getContext()" />
              </slot>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- Subtle refetch indicator (thin bar at top of table) -->
    <q-linear-progress v-if="fetching && rows.length > 0" indeterminate color="primary" class="km-data-table__fetching-bar" />

    <!-- Pagination footer -->
    <div v-if="showPagination" class="km-data-table__footer row items-center q-px-md q-py-sm text-grey ba-border">
      <div class="km-description">
        {{ totalLabel }}
      </div>

      <q-space />

      <div class="row items-center q-gap-8">
        <span class="km-description">{{ rowsPerPageLabel }}</span>
        <q-select
          v-model="pageSize"
          :options="pageSizeOptions"
          dense
          borderless
          emit-value
          map-options
          class="km-data-table__page-size"
        />
      </div>

      <div class="row items-center q-ml-md q-gap-4">
        <q-btn
          flat
          dense
          round
          icon="first_page"
          size="sm"
          :disable="!table.getCanPreviousPage()"
          @click="table.firstPage()"
        />
        <q-btn
          flat
          dense
          round
          icon="chevron_left"
          size="sm"
          :disable="!table.getCanPreviousPage()"
          @click="table.previousPage()"
        />
        <span class="km-description">
          {{ table.getState().pagination.pageIndex + 1 }} / {{ table.getPageCount() || 1 }}
        </span>
        <q-btn
          flat
          dense
          round
          icon="chevron_right"
          size="sm"
          :disable="!table.getCanNextPage()"
          @click="table.nextPage()"
        />
        <q-btn
          flat
          dense
          round
          icon="last_page"
          size="sm"
          :disable="!table.getCanNextPage()"
          @click="table.lastPage()"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts" generic="T">
import { computed, type Component } from 'vue'
import { FlexRender, type Table, type Row, type Cell } from '@tanstack/vue-table'

interface ColumnMeta {
  align?: 'left' | 'center' | 'right'
  class?: string
  width?: string
  /** Custom Vue component to render in cell (like km-table's type: 'component') */
  component?: Component | ((context: { row: T; cell: Cell<T, unknown> }) => Component)
  /** Extra props to pass to the component */
  componentProps?: (row: T) => Record<string, unknown>
}

/**
 * Resolve component — supports both static component and factory function
 */
function resolveComponent(comp: any, cell: Cell<T, unknown>, row: Row<T>): Component {
  if (typeof comp === 'function' && !comp.__vccOpts && !comp.setup && !comp.render) {
    return comp({ row: row.original, cell })
  }
  return comp
}

const props = withDefaults(defineProps<{
  table: Table<T>
  loading?: boolean
  /** Subtle indicator for background refetches (thin progress bar) */
  fetching?: boolean
  fillHeight?: boolean
  dense?: boolean
  activeRowId?: string | number
  rowKey?: string
  hidePagination?: boolean
  pageSizeOptions?: number[]
  noRecordsLabel?: string
  rowsPerPageLabel?: string
}>(), {
  loading: false,
  fetching: false,
  fillHeight: false,
  dense: false,
  hidePagination: false,
  pageSizeOptions: () => [10, 20, 50, 100],
})

const emit = defineEmits<{
  'row-click': [row: T]
}>()

const noRecordsLabel = computed(() => props.noRecordsLabel ?? 'No records found')
const rowsPerPageLabel = computed(() => props.rowsPerPageLabel ?? 'Rows per page:')

const rows = computed(() => props.table.getRowModel().rows)

const showPagination = computed(() => !props.hidePagination && props.table.getPageCount() > 0)

const pageSize = computed({
  get: () => props.table.getState().pagination.pageSize,
  set: (val: number) => props.table.setPageSize(val),
})

const totalLabel = computed(() => {
  const total = props.table.getRowCount()
  return `${total} record${total !== 1 ? 's' : ''}`
})

function getRowKey(row: Row<T>): string | number {
  if (props.rowKey) {
    return (row.original as Record<string, unknown>)[props.rowKey] as string | number
  }
  return row.id
}
</script>

<style scoped>
.km-data-table {
  position: relative;
  min-width: 0;
  width: 100%;
  overflow: hidden;
}
.km-data-table--fill-height {
  height: 100%;
  min-height: 0;
}

.km-data-table__table {
  border-collapse: collapse;
  table-layout: auto;
}
.km-data-table__th {
  position: sticky;
  top: 0;
  z-index: 1;
  user-select: none;
  white-space: nowrap;
  height: 48px;
  border-bottom: 1px solid rgba(0, 0, 0, 0.12);
}
.km-data-table__row {
  transition: background-color 0.15s ease;
}
.km-data-table__row:hover {
  background-color: var(--q-control-hover-bg, rgba(0, 0, 0, 0.03));
}
.km-data-table__td {
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 300px;
  height: 48px;
  font-size: var(--km-font-size-body, 13px);
  border-bottom: 1px solid rgba(0, 0, 0, 0.06);
}
.km-data-table__fetching-bar {
  position: absolute;
  top: 48px;
  left: 0;
  right: 0;
  z-index: 2;
  height: 2px !important;
  opacity: 0.6;
}
.km-data-table__footer {
  flex-shrink: 0;
}
.km-data-table__page-size {
  width: 60px;
}
.selection-checkbox .q-checkbox__bg {
  border-color: var(--q-primary) !important;
}
</style>

<script setup lang="ts" generic="T">
/**
 * `<km-data-table>` — drop-in for the legacy DataTable that was already
 * built on top of TanStack Vue Table.
 *
 * Behavioural parity with the legacy:
 *   - sticky header row, click + keyboard sort triggers
 *   - aria-sort exposed for screen readers
 *   - per-column meta: `align`, `class`, `width`, `component`, `componentProps`
 *   - row click emit, custom cell slot named `cell-<columnId>`
 *   - empty-state slot, `loading` initial spinner, `fetching` thin top bar
 *   - pagination footer with page-size select + first/prev/next/last
 *
 * What changed: every Quasar primitive (`q-icon`, `q-spinner`, `q-select`,
 * `q-btn`, `q-linear-progress`, `q-space`) is replaced by `@ds` equivalents;
 * spacing/colour utility classes now use `--ds-*` tokens.
 */

import { computed, type Component } from 'vue'
import { FlexRender, type Cell, type Row, type Table } from '@tanstack/vue-table'
import KmBtn from './KmBtn.vue'
import KmGlyph from './KmGlyph.vue'
import KmLoader from './KmLoader.vue'
import KmSelect from './KmSelect.vue'
import DsProgress from '../primitives/Progress/DsProgress.vue'

interface ColumnMeta<TRow> {
  align?: 'left' | 'center' | 'right'
  class?: string
  width?: string
  component?: Component | ((context: { row: TRow; cell: Cell<TRow, unknown> }) => Component)
  componentProps?: (row: TRow) => Record<string, unknown>
}

const props = withDefaults(
  defineProps<{
    table: Table<T>
    loading?: boolean
    fetching?: boolean
    fillHeight?: boolean
    dense?: boolean
    activeRowId?: string | number
    rowKey?: string
    hidePagination?: boolean
    pageSizeOptions?: number[]
    noRecordsLabel?: string
    rowsPerPageLabel?: string
    rowClass?:
      | string
      | string[]
      | Record<string, boolean>
      | ((row: T) => string | string[] | Record<string, boolean>)
  }>(),
  {
    loading: false,
    fetching: false,
    fillHeight: false,
    dense: false,
    hidePagination: false,
    pageSizeOptions: () => [10, 20, 50, 100],
  },
)

const emit = defineEmits<{
  'row-click': [row: T]
}>()

const noRecordsLabel = computed(() => props.noRecordsLabel ?? 'No records found')
const rowsPerPageLabel = computed(() => props.rowsPerPageLabel ?? 'Rows per page:')

const rows = computed(() => props.table.getRowModel().rows)
const showPagination = computed(() => !props.hidePagination && props.table.getPageCount() > 0)

const pageSize = computed({
  get: () => props.table.getState().pagination.pageSize,
  set: (val) => props.table.setPageSize(Number(val)),
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

function resolveRowClass(row: T) {
  const rc = props.rowClass
  if (!rc) return undefined
  return typeof rc === 'function' ? rc(row) : rc
}

function headerAriaSort(header: { column: { getCanSort: () => boolean; getIsSorted: () => false | 'asc' | 'desc' } }) {
  if (!header.column.getCanSort()) return undefined
  const sorted = header.column.getIsSorted()
  if (sorted === 'asc') return 'ascending'
  if (sorted === 'desc') return 'descending'
  return 'none'
}

function getMeta(meta: unknown): ColumnMeta<T> {
  return (meta ?? {}) as ColumnMeta<T>
}

function resolveComponent(comp: unknown, cell: Cell<T, unknown>, row: Row<T>): Component {
  if (typeof comp === 'function') {
    const fn = comp as (ctx: { row: T; cell: Cell<T, unknown> }) => Component
    return fn({ row: row.original, cell })
  }
  return comp as Component
}

const pageSizeOptionItems = computed(() =>
  props.pageSizeOptions.map((n) => ({ label: String(n), value: n })),
)
</script>

<template>
  <div class="km-data-table" :class="{ 'km-data-table--fill-height': fillHeight }" data-test="km-data-table">
    <div class="km-data-table__body">
      <table class="km-data-table__table">
        <thead class="km-data-table__header">
          <tr v-for="headerGroup in table.getHeaderGroups()" :key="headerGroup.id">
            <th
              v-for="header in headerGroup.headers"
              :key="header.id"
              class="km-data-table__th"
              :class="[`km-data-table__th--${getMeta(header.column.columnDef.meta).align ?? 'left'}`]"
              :style="getMeta(header.column.columnDef.meta).width ? { width: getMeta(header.column.columnDef.meta).width } : {}"
              :aria-sort="headerAriaSort(header)"
              :role="header.column.getCanSort() ? 'button' : undefined"
              :tabindex="header.column.getCanSort() ? 0 : -1"
              @click="header.column.getCanSort() ? header.column.toggleSorting() : undefined"
              @keydown.enter.prevent="header.column.getCanSort() ? header.column.toggleSorting() : undefined"
              @keydown.space.prevent="header.column.getCanSort() ? header.column.toggleSorting() : undefined"
            >
              <span class="km-data-table__th-inner" :class="{ 'km-data-table__th-inner--sortable': header.column.getCanSort() }">
                <slot
                  v-if="!header.isPlaceholder"
                  :name="`header-${header.column.id}`"
                  :header="header"
                  :column="header.column"
                >
                  <FlexRender
                    :render="header.column.columnDef.header"
                    :props="header.getContext()"
                  />
                </slot>
                <KmGlyph
                  v-if="header.column.getIsSorted()"
                  :name="header.column.getIsSorted() === 'desc' ? 'arrow_downward' : 'arrow_upward'"
                  size="14px"
                />
              </span>
            </th>
          </tr>
        </thead>

        <tbody>
          <tr v-if="loading && rows.length === 0">
            <td :colspan="table.getAllColumns().length" class="km-data-table__placeholder">
              <KmLoader size="40px" />
            </td>
          </tr>

          <tr v-else-if="rows.length === 0">
            <td :colspan="table.getAllColumns().length" class="km-data-table__placeholder">
              <slot name="empty-state">
                <p class="km-data-table__empty-text">{{ noRecordsLabel }}</p>
              </slot>
            </td>
          </tr>

          <tr
            v-for="row in rows"
            :key="row.id"
            class="km-data-table__row"
            :class="[
              { 'km-data-table__row--active': activeRowId && getRowKey(row) === activeRowId },
              resolveRowClass(row.original),
            ]"
            data-test="table-row"
            @click="emit('row-click', row.original)"
          >
            <td
              v-for="cell in row.getVisibleCells()"
              :key="cell.id"
              class="km-data-table__td"
              :class="[
                `km-data-table__td--${getMeta(cell.column.columnDef.meta).align ?? 'left'}`,
                getMeta(cell.column.columnDef.meta).class,
              ]"
            >
              <slot
                :name="`cell-${cell.column.id}`"
                :cell="cell"
                :row="row.original"
                :value="cell.getValue()"
              >
                <component
                  :is="resolveComponent(getMeta(cell.column.columnDef.meta).component, cell, row)"
                  v-if="getMeta(cell.column.columnDef.meta).component"
                  :row="row.original"
                  v-bind="getMeta(cell.column.columnDef.meta).componentProps?.(row.original) ?? {}"
                />
                <FlexRender
                  v-else
                  :render="cell.column.columnDef.cell"
                  :props="cell.getContext()"
                />
              </slot>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <DsProgress
      v-if="fetching && rows.length > 0"
      :value="null"
      tone="primary"
      size="sm"
      class="km-data-table__fetching-bar"
    />

    <div v-if="showPagination" class="km-data-table__footer cluster" data-align="center">
      <span class="km-data-table__total">{{ totalLabel }}</span>

      <span class="ms-auto cluster gap-sm" data-align="center">
        <span class="km-data-table__caption">{{ rowsPerPageLabel }}</span>
        <KmSelect
          v-model="pageSize"
          :options="pageSizeOptionItems"
          option-label="label"
          option-value="value"
          emit-value
          class="km-data-table__page-size"
        />
      </span>

      <span class="cluster gap-2xs" data-align="center">
        <KmBtn
          flat
          icon="first-page"
          icon-size="20px"
          :disable="!table.getCanPreviousPage()"
          @click="table.firstPage()"
        />
        <KmBtn
          flat
          icon="chevron_left"
          icon-size="20px"
          :disable="!table.getCanPreviousPage()"
          @click="table.previousPage()"
        />
        <span class="km-data-table__caption">
          {{ table.getState().pagination.pageIndex + 1 }} / {{ table.getPageCount() || 1 }}
        </span>
        <KmBtn
          flat
          icon="chevron_right"
          icon-size="20px"
          :disable="!table.getCanNextPage()"
          @click="table.nextPage()"
        />
        <KmBtn
          flat
          icon="last-page"
          icon-size="20px"
          :disable="!table.getCanNextPage()"
          @click="table.lastPage()"
        />
      </span>
    </div>
  </div>
</template>

<style>
.km-data-table {
  position: relative;
  display: flex;
  flex-flow: column nowrap;
  inline-size: 100%;
  min-inline-size: 0;
  overflow: hidden;
}
.km-data-table--fill-height { block-size: 100%; min-block-size: 0; }

.km-data-table__body {
  flex: 1 1 auto;
  min-inline-size: 0;
  overflow: auto;
  overscroll-behavior: contain;
}

.km-data-table__table {
  inline-size: 100%;
  border-collapse: collapse;
  table-layout: auto;
}

.km-data-table__th {
  position: sticky;
  inset-block-start: 0;
  z-index: var(--ds-z-raised);
  background: var(--ds-color-primary-light);
  padding: 0 var(--ds-space-md);
  block-size: 36px;
  user-select: none;
  white-space: nowrap;
  border-block-end: 1px solid var(--ds-color-border);
  font-size: var(--ds-font-size-caption);
  font-weight: var(--ds-font-weight-semibold);
  color: var(--ds-color-secondary-text);
}
.km-data-table__th--left   { text-align: start; }
.km-data-table__th--center { text-align: center; }
.km-data-table__th--right  { text-align: end; }

.km-data-table__th-inner {
  display: inline-flex;
  align-items: center;
  gap: var(--ds-space-2xs);
}
.km-data-table__th-inner--sortable { cursor: pointer; }

.km-data-table__placeholder {
  text-align: center;
  padding: var(--ds-space-2xl) 0;
}
.km-data-table__empty-text {
  color: var(--ds-color-text-grey);
  font-size: var(--ds-font-size-caption);
  margin: 0;
}

.km-data-table__row {
  transition: background var(--ds-duration-fast) var(--ds-ease-out);
  cursor: pointer;
}
.km-data-table__row:hover { background: var(--ds-color-control-hover-bg); }
.km-data-table__row--active { background: var(--ds-color-control-hover-bg); }

.km-data-table__td {
  padding: 0 var(--ds-space-md);
  block-size: 40px;
  font-size: var(--ds-font-size-body);
  border-block-end: 1px solid var(--ds-color-border-subtle);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-inline-size: 300px;
}
.km-data-table__td--left   { text-align: start; }
.km-data-table__td--center { text-align: center; }
.km-data-table__td--right  { text-align: end; }

/* Opt-in wrapping for cells whose content shouldn't be ellipsised (e.g. a
 * cluster of chips). The row grows to fit the wrapped content. */
.km-data-table__td--wrap {
  white-space: normal;
  block-size: auto;
  max-inline-size: none;
  overflow: visible;
  text-overflow: clip;
  padding-block: var(--ds-space-xs);
}

.km-data-table__fetching-bar {
  position: absolute;
  inset-block-start: 36px;
  inset-inline: 0;
  z-index: var(--ds-z-raised);
  block-size: 2px;
  opacity: 0.6;
}

.km-data-table__footer {
  flex-shrink: 0;
  padding: var(--ds-space-sm) var(--ds-space-md);
  border-block-start: 1px solid var(--ds-color-border);
  color: var(--ds-color-text-grey);
}
.km-data-table__total { font-size: var(--ds-font-size-caption); }
.km-data-table__caption { font-size: var(--ds-font-size-caption); }
.km-data-table__page-size { inline-size: 80px; }
</style>

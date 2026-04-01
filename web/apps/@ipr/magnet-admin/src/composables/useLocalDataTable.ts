import {
  useVueTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  type ColumnDef,
  type PaginationState,
  type SortingState,
  type RowSelectionState,
  type VisibilityState,
  type Updater,
} from '@tanstack/vue-table'
import { computed, ref, type MaybeRef, unref } from 'vue'

export interface UseLocalDataTableOptions {
  defaultPageSize?: number
  defaultSort?: SortingState
  defaultColumnVisibility?: VisibilityState
  enableRowSelection?: boolean
}

function applyUpdater<T>(updater: Updater<T>, current: T): T {
  return typeof updater === 'function' ? (updater as (old: T) => T)(current) : updater
}

/**
 * Table composable for local/store-backed data (not fetched from entity API).
 * Provides client-side pagination, sorting, filtering — same UX as useDataTable.
 *
 * Usage:
 * ```ts
 * const { table, globalFilter } = useLocalDataTable(storeItems, columns)
 * ```
 */
export function useLocalDataTable<T>(
  data: MaybeRef<T[]>,
  columns: ColumnDef<T, unknown>[],
  options?: UseLocalDataTableOptions,
) {
  const {
    defaultPageSize = 20,
    defaultSort = [],
    defaultColumnVisibility = {},
    enableRowSelection = false,
  } = options ?? {}

  const pagination = ref<PaginationState>({ pageIndex: 0, pageSize: defaultPageSize })
  const sorting = ref<SortingState>(defaultSort)
  const rowSelection = ref<RowSelectionState>({})
  const columnVisibility = ref<VisibilityState>(defaultColumnVisibility)
  const globalFilter = ref('')

  const rows = computed(() => unref(data))

  const table = useVueTable<T>({
    get data() { return rows.value },
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    getFilteredRowModel: getFilteredRowModel(),
    getPaginationRowModel: getPaginationRowModel(),
    enableRowSelection,
    globalFilterFn: 'includesString',
    state: {
      get pagination() { return pagination.value },
      get sorting() { return sorting.value },
      get rowSelection() { return rowSelection.value },
      get columnVisibility() { return columnVisibility.value },
      get globalFilter() { return globalFilter.value },
    },
    onPaginationChange: (updater) => { pagination.value = applyUpdater(updater, pagination.value) },
    onSortingChange: (updater) => { sorting.value = applyUpdater(updater, sorting.value) },
    onRowSelectionChange: (updater) => { rowSelection.value = applyUpdater(updater, rowSelection.value) },
    onColumnVisibilityChange: (updater) => { columnVisibility.value = applyUpdater(updater, columnVisibility.value) },
    onGlobalFilterChange: (updater) => { globalFilter.value = applyUpdater(updater, globalFilter.value) },
  })

  const selectedRows = computed(() =>
    table.getSelectedRowModel().rows.map((r) => r.original),
  )

  function clearSelection() {
    rowSelection.value = {}
  }

  return {
    table,
    rows,
    globalFilter,
    pagination,
    sorting,
    rowSelection,
    columnVisibility,
    selectedRows,
    clearSelection,
  }
}

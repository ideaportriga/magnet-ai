import {
  useVueTable,
  getCoreRowModel,
  getSortedRowModel,
  getFilteredRowModel,
  getPaginationRowModel,
  type ColumnDef,
  type PaginationState,
  type SortingState,
  type ColumnFiltersState,
  type RowSelectionState,
  type VisibilityState,
  type Updater,
} from '@tanstack/vue-table'
import { computed, ref, watch, type MaybeRef, unref } from 'vue'
import type { BaseEntity } from '@/types'
import { useEntityQueries } from '@/queries/entities'

type EntityKeyName = keyof ReturnType<typeof useEntityQueries>

export interface UseDataTableOptions {
  defaultPageSize?: number
  defaultSort?: SortingState
  defaultColumnVisibility?: VisibilityState
  manualPagination?: boolean
  manualSorting?: boolean
  manualFiltering?: boolean
  /** Extra static filters to include in every request */
  extraParams?: MaybeRef<Record<string, unknown>>
  /** Client-side filter applied to API results before they reach the table */
  dataFilter?: (items: T[]) => T[]
  /** Debounce delay in ms for server-side search (default: 300) */
  searchDebounce?: number
}

function applyUpdater<T>(updater: Updater<T>, current: T): T {
  return typeof updater === 'function' ? (updater as (old: T) => T)(current) : updater
}

export function useDataTable<T extends BaseEntity>(
  entityKey: EntityKeyName,
  columns: ColumnDef<T, unknown>[],
  options?: UseDataTableOptions,
) {
  const queries = useEntityQueries()
  const entityQ = queries[entityKey] as ReturnType<typeof queries[typeof entityKey]>

  const {
    defaultPageSize = 20,
    defaultSort = [],
    defaultColumnVisibility = {},
    manualPagination = true,
    manualSorting = true,
    manualFiltering = true,
    extraParams,
    dataFilter,
    searchDebounce = 300,
  } = options ?? {}

  // Table state
  const pagination = ref<PaginationState>({ pageIndex: 0, pageSize: defaultPageSize })
  const sorting = ref<SortingState>(defaultSort)
  const columnFilters = ref<ColumnFiltersState>([])
  const rowSelection = ref<RowSelectionState>({})
  const columnVisibility = ref<VisibilityState>(defaultColumnVisibility)
  const globalFilter = ref('')

  // Debounced search value for server-side queries
  const debouncedSearch = ref('')
  let searchTimer: ReturnType<typeof setTimeout> | null = null

  watch(globalFilter, (val) => {
    if (!manualFiltering) return // client-side filtering — no need to debounce
    if (searchTimer) clearTimeout(searchTimer)
    searchTimer = setTimeout(() => {
      debouncedSearch.value = val
    }, searchDebounce)
  })

  // Convert table state → API query params
  const queryParams = computed(() => {
    const params: Record<string, unknown> = {
      ...(unref(extraParams) ?? {}),
    }

    if (manualPagination) {
      params.currentPage = pagination.value.pageIndex + 1
      params.pageSize = pagination.value.pageSize
    }

    if (manualSorting && sorting.value.length > 0) {
      params.orderBy = sorting.value[0].id
      params.sortOrder = sorting.value[0].desc ? 'desc' : 'asc'
    }

    // Column filters → flat params
    for (const filter of columnFilters.value) {
      if (filter.value !== undefined && filter.value !== null && filter.value !== '') {
        params[filter.id] = filter.value
      }
    }

    // Server-side search — only when manualFiltering is true
    if (manualFiltering && debouncedSearch.value) {
      params.search = debouncedSearch.value
    }

    return params
  })

  // TanStack Query — auto-refetches when queryParams change
  const { data, isLoading, isError, error, refetch } = entityQ.useList(queryParams) as ReturnType<typeof entityQ.useList>

  const rawRows = computed<T[]>(() => ((data.value as { items?: T[] })?.items ?? []) as T[])
  const rows = computed<T[]>(() => dataFilter ? dataFilter(rawRows.value) : rawRows.value)
  const totalRows = computed(() => (data.value as { total?: number })?.total ?? rows.value.length)
  const pageCount = computed(() =>
    manualPagination ? Math.ceil(totalRows.value / pagination.value.pageSize) : undefined,
  )

  // TanStack Table instance
  // When manualFiltering: false, TanStack's getFilteredRowModel() handles
  // client-side search via globalFilter state — no need for pre-filtering.
  const table = useVueTable<T>({
    get data() {
      return rows.value
    },
    columns,
    getCoreRowModel: getCoreRowModel(),
    // Client-side models — only active when manual* is false
    ...(!manualSorting ? { getSortedRowModel: getSortedRowModel() } : {}),
    ...(!manualFiltering ? { getFilteredRowModel: getFilteredRowModel() } : {}),
    ...(!manualPagination ? { getPaginationRowModel: getPaginationRowModel() } : {}),

    // Server-side mode flags
    manualPagination,
    manualSorting,
    manualFiltering,

    get pageCount() {
      return pageCount.value
    },
    get rowCount() {
      return totalRows.value
    },

    state: {
      get pagination() { return pagination.value },
      get sorting() { return sorting.value },
      get columnFilters() { return columnFilters.value },
      get rowSelection() { return rowSelection.value },
      get columnVisibility() { return columnVisibility.value },
      get globalFilter() { return globalFilter.value },
    },

    onPaginationChange: (updater) => { pagination.value = applyUpdater(updater, pagination.value) },
    onSortingChange: (updater) => { sorting.value = applyUpdater(updater, sorting.value) },
    onColumnFiltersChange: (updater) => { columnFilters.value = applyUpdater(updater, columnFilters.value) },
    onRowSelectionChange: (updater) => { rowSelection.value = applyUpdater(updater, rowSelection.value) },
    onColumnVisibilityChange: (updater) => { columnVisibility.value = applyUpdater(updater, columnVisibility.value) },
    onGlobalFilterChange: (updater) => { globalFilter.value = applyUpdater(updater, globalFilter.value) },
  })

  return {
    table,
    rows,
    totalRows,
    isLoading,
    isError,
    error,
    refetch,
    // Direct state access for external control
    pagination,
    sorting,
    columnFilters,
    rowSelection,
    columnVisibility,
    globalFilter,
  }
}

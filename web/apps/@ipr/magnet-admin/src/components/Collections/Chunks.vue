<template lang="pug">
.column.full-height.full-width.no-wrap
  //- Toolbar
  .row.q-mb-12.items-center
    .col-auto
      km-input(
        :placeholder='m.collections_searchChunks()',
        iconBefore='search',
        :model-value='searchText',
        @input='onSearchInput',
        @keydown.enter='applySearch',
        clearable
      )
    .col
    .col-auto
      km-btn(:label='m.collections_deleteAllChunks()', :loading='deleteLoading', @click='showDeleteConfirm = true', flat, icon='fas fa-trash', iconSize='14px')

  //- Table
  .col(style='min-height: 0')
    km-data-table(
      :table='table',
      :loading='isLoading',
      fillHeight,
      rowKey='id',
      :activeRowId='selectedRow?.id',
      @row-click='onRowClick'
    )
      template(#empty-state)
        .column.flex-center.q-py-xl
          km-icon(name='empty-collection', width='200', height='200')
          .km-title.q-py-16.text-label {{ m.collectionItems_nothingInSourceYet() }}

  //- Delete confirmation
  km-popup-confirm(
    :visible='showDeleteConfirm',
    notificationIcon='fas fa-triangle-exclamation',
    :confirmButtonLabel='m.collections_yesDeleteAll()',
    :cancelButtonLabel='m.common_cancel()',
    @confirm='confirmDelete',
    @cancel='showDeleteConfirm = false'
  )
    .row.item-center.justify-center.km-heading-7.q-mb-md {{ m.collections_deleteChunksConfirmation() }}
    .row.text-center.justify-center {{ m.collections_deleteAllChunksConfirm() }}
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { m } from '@/paraglide/messages'
import { useRoute } from 'vue-router'
import { useQuery, useQueryClient, keepPreviousData } from '@tanstack/vue-query'
import {
  useVueTable,
  getCoreRowModel,
  type ColumnDef,
  type PaginationState,
  type SortingState,
  type Updater,
} from '@tanstack/vue-table'
import { getApiClient } from '@/api'
import { formatDateTime } from '@shared/utils/dateTime'
import type { Document } from '@/types'

const props = defineProps<{ selectedRow?: Document | null }>()
const emit = defineEmits<{ selectRow: [row: Document | null] }>()

const route = useRoute()
const queryClient = useQueryClient()
const showDeleteConfirm = ref(false)
const deleteLoading = ref(false)
const searchText = ref('')
const appliedSearch = ref('')

const collectionId = computed(() => route.params.id as string)

// Pagination & sorting state
const pagination = ref<PaginationState>({ pageIndex: 0, pageSize: 20 })
const sorting = ref<SortingState>([])

// Query params → POST body for server-side pagination
const queryParams = computed(() => ({
  collectionId: collectionId.value,
  limit: pagination.value.pageSize,
  offset: pagination.value.pageIndex * pagination.value.pageSize,
  sort: sorting.value[0]?.id ?? 'created_at',
  order: sorting.value[0]?.desc ? -1 : 1,
  search: appliedSearch.value || undefined,
}))

// TanStack Query — server-side paginated fetch
const { data, isLoading } = useQuery({
  queryKey: computed(() => ['documents', 'list', queryParams.value]),
  queryFn: async () => {
    const { collectionId: cid, ...body } = queryParams.value
    const client = getApiClient()
    return client.post<{ items: Document[]; total: number }>(
      `collections/${cid}/documents/paginate/offset`,
      body,
    )
  },
  enabled: computed(() => !!collectionId.value),
  placeholderData: keepPreviousData,
})

const rows = computed(() => data.value?.items ?? [])
const totalRows = computed(() => data.value?.total ?? 0)
const pageCount = computed(() => Math.ceil(totalRows.value / pagination.value.pageSize))

// Columns
const columns: ColumnDef<Document, unknown>[] = [
  {
    id: 'title',
    header: m.common_title(),
    accessorFn: (row) => row.metadata?.title ?? '-',
    meta: { width: '40%' },
  },
  {
    id: 'type',
    header: m.common_type(),
    accessorFn: (row) => row.metadata?.type ?? '-',
    meta: { width: '15%' },
  },
  {
    id: 'created_at',
    header: m.common_created(),
    accessorFn: (row) => row.metadata?.createdTime ?? row.created_at ?? '',
    cell: (info) => formatDate(info.getValue() as string),
    meta: { width: '20%' },
  },
  {
    id: 'updated_at',
    header: m.common_modifiedShort(),
    accessorFn: (row) => row.metadata?.modifiedTime ?? row.updated_at ?? '',
    cell: (info) => formatDate(info.getValue() as string),
    meta: { width: '20%' },
  },
]

function applyUpdater<T>(updater: Updater<T>, current: T): T {
  return typeof updater === 'function' ? (updater as (old: T) => T)(current) : updater
}

// TanStack Table — manual (server-side) pagination & sorting
const table = useVueTable({
  get data() { return rows.value },
  columns,
  getCoreRowModel: getCoreRowModel(),
  manualPagination: true,
  manualSorting: true,
  get pageCount() { return pageCount.value },
  get rowCount() { return totalRows.value },
  state: {
    get pagination() { return pagination.value },
    get sorting() { return sorting.value },
  },
  onPaginationChange: (updater) => { pagination.value = applyUpdater(updater, pagination.value) },
  onSortingChange: (updater) => { sorting.value = applyUpdater(updater, sorting.value) },
})

const formatDate = (val?: string) => (val ? formatDateTime(val) : '-')

function onRowClick(row: Document) {
  emit('selectRow', row)
}

let searchDebounce: ReturnType<typeof setTimeout> | null = null

function onSearchInput(value: string) {
  searchText.value = value
  if (searchDebounce) clearTimeout(searchDebounce)
  searchDebounce = setTimeout(() => applySearch(), 400)
}

function applySearch() {
  appliedSearch.value = searchText.value
  pagination.value = { ...pagination.value, pageIndex: 0 }
}

async function confirmDelete() {
  showDeleteConfirm.value = false
  deleteLoading.value = true
  try {
    const client = getApiClient()
    await client.delete(`collections/${collectionId.value}/documents/all`)
  } finally {
    deleteLoading.value = false
  }
  await queryClient.invalidateQueries({ queryKey: ['documents'] })
  await queryClient.invalidateQueries({ queryKey: ['collections'] })
}
</script>

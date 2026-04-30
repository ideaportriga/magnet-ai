<template>
  <div class="cluster mb-md">
    <div class="flex-none center-flex-y">
      <km-input data-test="search-input" :placeholder="m.common_search()" icon-before="search" :model-value="globalFilter" clearable @input="globalFilter = $event" />
    </div>
    <div class="km-space" />
    <div class="flex-none center-flex-y">
      <km-btn class="mr-md" data-test="new-btn" :label="m.common_new()" @click="showNewDialog = true" />
    </div>
  </div>
  <div class="flex-1" style="min-block-size: 0">
    <km-data-table :table="table" fill-height row-key="system_name" @row-click="openDetails" />
  </div>
  <knowledge-providers-new-provider :show-new-dialog="showNewDialog" @cancel="showNewDialog = false" />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useDataTable } from '@/composables/useDataTable'
import { nameDescriptionColumn, chipCopyColumn, dateColumn, textColumn } from '@/utils/columnHelpers'
import { m } from '@/paraglide/messages'
import type { Provider } from '@/types'

const router = useRouter()
const showNewDialog = ref(false)

const columns = [
  nameDescriptionColumn<Provider>(m.common_name()),
  chipCopyColumn<Provider>(m.common_systemName()),
  textColumn<Provider>('type' as keyof Provider, m.common_type()),
  dateColumn<Provider>('created_at', m.common_created()),
  dateColumn<Provider>('updated_at', m.common_lastUpdated()),
]

const { table, isLoading, isFetching, globalFilter } = useDataTable<Provider>('provider', columns, {
  defaultSort: [{ id: 'updated_at', desc: true }],
  manualPagination: false,
  manualSorting: false,
  manualFiltering: false,
  dataFilter: (items) => items.filter((p) => (p as Record<string, unknown>).category === 'knowledge'),
})

const openDetails = async (row: Provider) => {
  await router.push(`/knowledge-providers/${row.id}`)
}
</script>

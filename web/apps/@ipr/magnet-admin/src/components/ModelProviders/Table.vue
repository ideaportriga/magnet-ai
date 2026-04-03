<template lang="pug">
.row.q-mb-12
  .col-auto.center-flex-y
    km-input(:placeholder='m.common_search()', iconBefore='search', :modelValue='globalFilter', @input='globalFilter = $event', clearable)
  q-space
  .col-auto.center-flex-y
    km-btn.q-mr-12(:label='m.common_new()', @click='showNewDialog = true')
.col(style='min-height: 0')
  km-data-table(
    :table='table',
    :loading='isLoading', :fetching='isFetching',
    fill-height,
    row-key='system_name',
    @row-click='openDetails'
  )
model-providers-new-provider(:showNewDialog='showNewDialog', @cancel='showNewDialog = false')
</template>
<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useDataTable } from '@/composables/useDataTable'
import { textColumn, chipCopyColumn, dateColumn } from '@/utils/columnHelpers'
import { formatProviderType } from '@/config/model_providers/providerTypes'
import { m } from '@/paraglide/messages'
import type { Provider } from '@/types'

const router = useRouter()
const showNewDialog = ref(false)

const EXCLUDED_PROVIDER_TYPES = ['teams_note_taker']

const columns = [
  textColumn<Provider>('name', m.common_name()),
  chipCopyColumn<Provider>(m.common_systemName()),
  textColumn<Provider>('type', 'API Type', { format: (val) => formatProviderType(val as string) }),
  dateColumn<Provider>('created_at', m.common_created()),
  dateColumn<Provider>('updated_at', m.common_lastUpdated()),
]

const { table, isLoading, isFetching, globalFilter } = useDataTable<Provider>('provider', columns, {
  defaultSort: [{ id: 'updated_at', desc: true }],
  manualPagination: false,
  manualSorting: false,
  manualFiltering: false,
  dataFilter: (items) =>
    items.filter(
      (p) => (p.category === 'llm' || !p.category) && !EXCLUDED_PROVIDER_TYPES.includes(p.type as string),
    ),
})

const openDetails = async (row: Provider) => {
  await router.push(`/model-providers/${row.id}`)
}
</script>

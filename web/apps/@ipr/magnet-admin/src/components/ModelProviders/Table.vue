<template lang="pug">
.row.q-mb-12
  .col-auto.center-flex-y
    km-input(placeholder='Search', iconBefore='search', :modelValue='globalFilter', @input='globalFilter = $event', clearable)
  q-space
  .col-auto.center-flex-y
    km-btn.q-mr-12(label='New', @click='showNewDialog = true')
.col(style='min-height: 0')
  km-data-table(
    :table='table',
    :loading='isLoading',
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
import type { Provider } from '@/types'

const router = useRouter()
const showNewDialog = ref(false)

const EXCLUDED_PROVIDER_TYPES = ['teams_note_taker']

const columns = [
  textColumn<Provider>('name', 'Name'),
  chipCopyColumn<Provider>('System name'),
  textColumn<Provider>('type', 'API Type', { format: (val) => formatProviderType(val as string) }),
  dateColumn<Provider>('created_at', 'Created'),
  dateColumn<Provider>('updated_at', 'Last Updated'),
]

const { table, isLoading, globalFilter } = useDataTable<Provider>('provider', columns, {
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

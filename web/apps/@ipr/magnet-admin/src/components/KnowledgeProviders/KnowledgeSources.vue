<template lang="pug">
.column.full-height(style='min-height: 0')
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
      row-key='id',
      @row-click='openDetails'
    )
collections-create-new(
  v-if='showNewDialog',
  :showNewDialog='showNewDialog',
  @cancel='showNewDialog = false',
  :providerSystemName='providerSystemName'
)
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useDataTable } from '@/composables/useDataTable'
import { nameDescriptionColumn, chipCopyColumn, dateColumn, textColumn } from '@/utils/columnHelpers'
import { useEntityDetail } from '@/composables/useEntityDetail'
import { m } from '@/paraglide/messages'
import type { Collection } from '@/types'

const router = useRouter()
const { draft } = useEntityDetail('provider')
const showNewDialog = ref(false)

const providerSystemName = computed(() => draft.value?.system_name as string | undefined)

const columns = [
  nameDescriptionColumn<Collection>(m.common_name()),
  textColumn<Collection>('source_type' as keyof Collection, 'Source', {
    format: (val) => {
      if (val && typeof val === 'object') return (val as Record<string, unknown>)?.source_type as string ?? '-'
      return val ? String(val) : '-'
    },
  }),
  chipCopyColumn<Collection>(m.common_systemName()),
  dateColumn<Collection>('created_at', m.common_created()),
]

const { table, rows, isLoading, isFetching, globalFilter } = useDataTable<Collection>('collections', columns, {
  defaultSort: [{ id: 'created_at', desc: true }],
  manualPagination: false,
  manualSorting: false,
  manualFiltering: false,
  dataFilter: (items) => {
    const psn = providerSystemName.value
    if (!psn) return []
    return items.filter((item) => (item as Record<string, unknown>).provider_system_name === psn)
  },
})

const openDetails = async (row: Collection) => {
  await router.push(`/knowledge-sources/${row.id}`)
}
</script>

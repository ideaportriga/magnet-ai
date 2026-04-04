<template lang="pug">
.column.no-wrap.full-height
  .collection-container.q-mx-auto.full-width.column.full-height.q-px-md.q-pt-16
    .col.ba-border.border-radius-12.bg-white.q-pa-16.column(style='min-height: 0')
      .row.q-mb-12
        .col-auto.center-flex-y
          km-filter-bar(v-model:config='filterConfig', v-model:filterObject='filterObject', outputFormat='sql', persistent, persistentKey='traces-filter')
        q-space
        .col-auto.center-flex-y
          km-btn.q-mr-12(
            icon='refresh',
            :label='m.common_refreshList()',
            @click='refetch',
            iconColor='icon',
            hoverColor='primary',
            labelClass='km-title',
            flat,
            iconSize='16px',
            hoverBg='primary-bg'
          )
      .col(style='min-height: 0')
        km-data-table(
          :table='table',
          :loading='isLoading', :fetching='isFetching',
          fill-height,
          dense,
          row-key='id',
          @row-click='openDetails'
        )
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { m } from '@/paraglide/messages'
import { useRouter } from 'vue-router'
import { useDataTable } from '@/composables/useDataTable'
import { textColumn, dateColumn, componentColumn } from '@/utils/columnHelpers'
import StatusField from '@/config/observability/traces/components/StatusField.vue'
import { traceFilters } from '@/config/observability/traces'
import { getApiClient } from '@/api'
import type { ObservabilityTrace } from '@/types'

const router = useRouter()
const filterObject = ref<Record<string, unknown>>({})
const filterConfig = ref(traceFilters())

const columns = [
  textColumn<ObservabilityTrace>('type', m.common_type()),
  textColumn<ObservabilityTrace>('name', m.common_name()),
  componentColumn<ObservabilityTrace>('status', m.common_status(), StatusField, { accessorKey: 'status', sortable: true }),
  dateColumn<ObservabilityTrace>('start_time', m.common_startTime()),
  textColumn<ObservabilityTrace>('latency', m.common_duration(), {
    align: 'right',
    format: (val) => {
      if (!val) return '-'
      const ms = Number(val)
      return ms >= 1000 ? `${Math.round(ms / 1000)}s` : `${Math.round(ms)}ms`
    },
  }),
]

const { table, isLoading, isFetching, refetch } = useDataTable<ObservabilityTrace>('observability_traces', columns, {
  defaultSort: [{ id: 'start_time', desc: true }],
  defaultPageSize: 15,
  manualPagination: true,
  manualSorting: true,
  manualFiltering: true,
  extraParams: filterObject,
})

watch(filterObject, () => refetch(), { deep: true })

onMounted(async () => {
  try {
    const client = getApiClient()
    const graphs = await client.get<Array<{ name?: string }>>('knowledge_graphs')
    const graphNames = [...new Set((graphs ?? []).map((g) => g.name).filter(Boolean))] as string[]
    filterConfig.value = traceFilters(graphNames)
  } catch {
    // ignore — filter will work without KG names
  }
})

const openDetails = async (row: ObservabilityTrace) => {
  await router.push(`/observability-traces/${row.id}`)
}
</script>

<style lang="stylus">
.km-input:not(.q-field--readonly) .q-field__control::before {
  background: #fff !important;
}
</style>

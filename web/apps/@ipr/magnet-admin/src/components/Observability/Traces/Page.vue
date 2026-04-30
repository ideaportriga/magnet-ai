<template>
  <km-list-page>
    <template #toolbar>
      <div class="flex-none center-flex-y">
        <km-filter-bar v-model:config="filterConfig" v-model:filter-object="filterObject" output-format="sql" persistent persistent-key="traces-filter" />
      </div>
      <div class="km-space" />
      <div class="flex-none center-flex-y">
        <km-btn class="mr-md" icon="refresh" :label="m.common_refreshList()" interaction-tone="brand" label-class="km-title" flat icon-size="16px" @click="refetch" />
      </div>
    </template>
    <km-data-table :table="table" :loading="isLoading" :fetching="isFetching" fill-height dense row-key="id" @row-click="openDetails" />
  </km-list-page>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { m } from '@/paraglide/messages'
import { useRouter } from 'vue-router'
import { useDataTable } from '@/composables/useDataTable'
import { useDebouncedWatch } from '@/composables/useDebouncedWatch'
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

// §C.3 — debounce to collapse multi-field filter edits into one refetch.
useDebouncedWatch(filterObject, () => refetch(), 250)

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


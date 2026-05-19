<template>
  <layouts-details-layout no-header :content-container-style="{ maxWidth: &quot;1200px&quot;, margin: &quot;0 auto&quot; }">
    <template #content>
      <div class="stack full-width overflow-auto" data-gap="0">
        <div class="cluster">
          <km-filter-bar v-model:config="filterConfig" v-model:filter-object="filterObject" />
          <div class="km-space" />
          <km-btn class="mr-md" icon="refresh" :label="m.common_refreshList()" interaction-tone="brand" label-class="km-title" flat icon-size="16px" @click="refetch" />
          <km-btn v-if="canCreate" data-test="new-btn" :label="m.common_new()" @click="showNewDialog = true" />
        </div>
        <div class="flex-1 pt-lg" style="min-block-size: 0">
          <km-data-table :table="table" :loading="isLoading" :fetching="isFetching" fill-height dense row-key="id" @row-click="openDetails" />
        </div>
      </div>
    </template>
    <template #drawer>
      <jobs-drawer :show-drawer="showDrawer" :job="selectedJob" @cancel="showDrawer = false" />
    </template>
  </layouts-details-layout>
  <jobs-create-new :show-new-dialog="showNewDialog" @cancel="showNewDialog = false" />
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useRoute } from 'vue-router'
import { useDataTable } from '@/composables/useDataTable'
import { useDebouncedWatch } from '@/composables/useDebouncedWatch'
import { textColumn, dateColumn, componentColumn } from '@/utils/columnHelpers'
import { m } from '@/paraglide/messages'
import { usePermissions } from '@shared'
import type { Job } from '@/types'

const route = useRoute()
const { can } = usePermissions()
const canCreate = computed(() => can('write:jobs'))
const showDrawer = ref(false)
const selectedJob = ref<Job | null>(null)
const showNewDialog = ref(false)
const filterObject = ref<Record<string, unknown>>({})

const filterConfig = ref({
  'definition.job_type': {
    label: 'Job type',
    key: 'definition.job_type',
    options: [
      { label: 'One time immmidiate', value: 'one_time_immediate' },
      { label: 'Recurring', value: 'recurring' },
    ],
    multiple: true,
  },
  status: {
    label: 'Status',
    key: 'status',
    options: [
      { label: 'Processing', value: 'Processing' },
      { label: 'Error', value: 'Error' },
      { label: 'Waiting', value: 'Waiting' },
      { label: 'Canceled', value: 'Canceled' },
    ],
    multiple: true,
  },
  type: {
    label: 'Type',
    key: 'type',
    options: [
      { label: 'Sync knowledge source', value: 'sync_collection' },
      { label: 'Custom', value: 'custom' },
    ],
  },
  created_at: {
    label: 'Created',
    key: 'created_at',
    type: 'timePeriod',
    default: 'P1D',
  },
  'definition.interval': {
    label: 'Interval',
    key: 'definition.interval',
    options: [
      { label: 'Hourly', value: 'hourly' },
      { label: 'Daily', value: 'daily' },
      { label: 'Weekly', value: 'weekly' },
    ],
    multiple: true,
  },
})

// Handle job_id query parameter
if (route.query.job_id) {
  const routeJobId = route.query.job_id as string
  const newConfig = { ...filterConfig.value } as Record<string, unknown>
  for (const key in newConfig) {
    newConfig[key] = { ...(newConfig[key] as Record<string, unknown>) }
    delete (newConfig[key] as Record<string, unknown>).default
  }
  ;(newConfig as Record<string, unknown>).id = {
    label: 'ID',
    key: 'id',
    options: [{ label: routeJobId, value: routeJobId }],
    default: routeJobId,
  }
  filterConfig.value = newConfig as typeof filterConfig.value
  filterObject.value = { id: routeJobId }
}

const columns = [
  textColumn<Job>('name', m.common_name()),
  textColumn<Job>('status', m.common_status()),
  textColumn<Job>('job_type', m.common_type()),
  dateColumn<Job>('last_run', 'Last run'),
  dateColumn<Job>('next_run', 'Next run'),
  textColumn<Job>('job_interval', 'Interval'),
  dateColumn<Job>('created_at', m.common_created()),
]

const { table, isLoading, isFetching, refetch } = useDataTable<Job>('jobs', columns, {
  defaultSort: [{ id: 'created_at', desc: true }],
  manualPagination: true,
  manualSorting: true,
  manualFiltering: true,
  extraParams: filterObject,
})

// §C.3 — debounce filter-driven refetch; multi-field edits used to fire
// 5+ requests per user action via `watch(..., { deep: true })`.
useDebouncedWatch(filterObject, () => refetch(), 250)

const openDetails = (row: Job) => {
  selectedJob.value = row
  showDrawer.value = true
}
</script>

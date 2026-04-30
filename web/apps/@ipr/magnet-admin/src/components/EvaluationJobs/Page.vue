<template>
  <km-list-page>
    <template #toolbar>
      <div class="flex-none center-flex-y">
        <km-input data-test="search-input" :placeholder="m.common_search()" icon-before="search" :model-value="globalFilter" clearable @input="globalFilter = $event" />
      </div>
      <div v-if="groupBy !== 'flat'" class="flex-none center-flex-y ml-md">
        <div class="text-secondary-text mr-sm">{{ m.evaluation_groupBy() }}</div>
        <km-select v-model="groupBy" :options="groups" height="30px" map-options emit-value option-value="value" option-label="label" />
      </div>
      <div class="flex-none center-flex-y ml-md">
        <template v-if="filterObject?.tool || filterObject?.job">
          <div class="text-secondary-text mr-sm">{{ filterObject?.tool ? m.evaluation_toolLabel() : m.evaluation_jobLabel() }}</div>
          <km-chip tone="brand" class="my-0" square size="12px">
            <div class="cluster fit">
              <div class="flex-1 text-center">{{ filterObject?.tool ? filterObject?.tool : filterObject?.job }}</div>
              <div class="flex-none ml-xs">
                <km-glyph class="my-auto cursor-pointer" name="close" @click.stop.prevent="removeFilter" />
              </div>
            </div>
          </km-chip>
        </template>
      </div>
      <div class="km-space" />
      <div class="flex-none center-flex-y">
        <km-btn v-if="groupBy == 'flat'" class="mr-md" icon="download" :label="m.common_report()" interaction-tone="brand" label-class="km-title" flat icon-size="16px" :disable="selected.length < 2" :tooltip="selected.length < 2 ? m.evaluation_selectAtLeastRecords({ count: 2 }) : ''" @click="getEvaluationReport" />
      </div>
      <div class="flex-none center-flex-y">
        <km-btn v-if="groupBy == 'flat'" class="mr-md" icon="compare" :label="m.common_compare()" interaction-tone="brand" label-class="km-title" flat icon-size="16px" :disable="selected.length < 2" :tooltip="selected.length < 2 ? m.evaluation_selectAtLeastRecords({ count: 2 }) : ''" @click="compare(false)" />
      </div>
      <div class="flex-none center-flex-y">
        <km-btn v-if="groupBy == 'flat'" class="mr-md" icon="delete" :label="m.common_delete()" interaction-tone="brand" label-class="km-title" flat icon-size="16px" :disable="selected.length < 1" :tooltip="selected.length < 1 ? m.evaluation_selectAtLeastRecords({ count: 1 }) : ''" @click="showDeleteDialog = true" />
      </div>
      <div class="flex-none center-flex-y">
        <km-btn class="mr-md" icon="refresh" :label="m.common_refreshList()" interaction-tone="brand" label-class="km-title" flat icon-size="16px" @click="refetch" />
      </div>
      <div class="flex-none center-flex-y">
        <km-btn v-if="!filterObject?.row" class="mr-md" data-test="new-btn" :label="m.common_new()" @click="showNewDialog = true" />
      </div>
    </template>
    <km-separator class="my-sm" />
    <div v-if="filterObject?.row" class="cluster mb-sm" data-align="start">
      <div class="flex-none">
        <div class="stack">
          <div v-if="filterObject?.job">
            <div class="cluster" data-gap="md" data-wrap="no" data-align="baseline">
              <div class="flex-none">
                <div class="km-field text-secondary-text">{{ m.evaluation_jobStart() }}</div>
              </div>
              <div class="flex-none">
                <div class="km-heading-3 mr-sm">{{ filterObjectStartData }}</div>
              </div>
            </div>
          </div>
          <div>
            <div class="cluster" data-gap="md" data-wrap="no" data-align="baseline">
              <div class="flex-none">
                <div class="km-field text-secondary-text">{{ m.evaluation_evaluatedTool() }}</div>
              </div>
              <div class="flex-none">
                <div class="km-heading-3 mr-sm">{{ filterObject?.row?.tool?.name }}</div>
              </div>
            </div>
          </div>
          <div v-if="filterObject?.job">
            <div class="cluster" data-gap="md" data-wrap="no" data-align="baseline">
              <div class="flex-none">
                <div class="km-field text-secondary-text">{{ m.evaluation_testSet() }}</div>
              </div>
              <div class="flex-none">
                <div class="km-heading-3 mr-sm">{{ filterObject?.row?.test_sets?.[0] }}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
      <div class="flex-1 ml-md">
        <km-chip class="km-small-chip" tone="neutral" :label="filterObject.row?.type === 'prompt_eval' ? m.entity_promptTemplate() : m.entity_ragTool()" />
      </div>
    </div>
    <km-separator v-if="filterObject?.row" class="my-sm" />
    <km-data-table :table="currentTable" :loading="isLoading" :fetching="isFetching" :fill-height="!filterObject?.row" row-key="id" @row-click="selectRecord" />
    <template #overlays>
      <evaluation-jobs-create-new v-if="showNewDialog" :show-new-dialog="showNewDialog" @cancel="showNewDialog = false" />
      <km-popup-confirm :visible="showDeleteDialog" :confirm-button-label="m.common_delete()" :cancel-button-label="m.common_cancel()" notification-icon="warning" @confirm="deleteSelected" @cancel="showDeleteDialog = false">
        <div class="cluster km-heading-7" data-justify="center">{{ m.evaluation_deleteTitle() }}</div>
        <div class="cluster text-center" data-justify="center">{{ m.evaluation_deleteSelectedConfirm({ count: selected?.length ?? 0 }) }}</div>
      </km-popup-confirm>
      <km-popup-confirm :visible="showRerunDialog" :confirm-button-label="m.common_run()" :cancel-button-label="m.common_cancel()" notification-icon="warning" @confirm="rerunSelected" @cancel="showRerunDialog = false">
        <div class="cluster km-heading-7" data-justify="center">{{ m.evaluation_rerunTitle() }}</div>
        <div class="cluster text-center" data-justify="center">{{ m.evaluation_rerunSelectedConfirm({ count: selected?.length ?? 0 }) }}</div>
      </km-popup-confirm>
    </template>
  </km-list-page>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useVueTable, getCoreRowModel, type ColumnDef } from '@tanstack/vue-table'
import { useDataTable } from '@/composables/useDataTable'
import { useSafeMutation } from '@/composables/useSafeMutation'
import { componentColumn } from '@/utils/columnHelpers'
import { useEntityQueries } from '@/queries/entities'
import { m } from '@/paraglide/messages'
import type { EvaluationJob } from '@/types'
import _ from 'lodash'
import { useEvaluationStore } from '@/stores/evaluationStore'
import Status from '@/config/evaluation_jobs/component/Status.vue'
import VariantName from '@/config/evaluation_jobs/component/VariantName.vue'
import Score from '@/config/evaluation_jobs/component/Score.vue'
import Latency from '@/config/evaluation_jobs/component/Latency.vue'
import Cost from '@/config/evaluation_jobs/component/Cost.vue'
import Report from '@/config/evaluation_jobs/component/Report.vue'

const router = useRouter()
const route = useRoute()
const showNewDialog = ref(false)
const showDeleteDialog = ref(false)
const showRerunDialog = ref(false)
const selected = ref<EvaluationJob[]>([])

const groupBy = ref<string>(route.query?.job_id ? 'flat' : 'job')
const groups = [
  { label: m.evaluation_groupJob(), value: 'job' },
  { label: m.evaluation_groupTool(), value: 'tool' },
]

interface FilterObject {
  tool: string
  job: string
  row?: Record<string, unknown> | null
}

const filterObject = ref<FilterObject>({
  tool: '',
  job: '',
  row: null,
})

const queries = useEntityQueries()
const { evaluation_jobs: evalJobsQ } = queries
// §B.8 — wrap remove/create so bulk delete/rerun can't silently abort
// halfway through on a failure (user would have to reload to see
// which items actually got processed).
const removeEvalJob = useSafeMutation(evalJobsQ.useRemove())
const createEvalJob = useSafeMutation(evalJobsQ.useCreate())
const { data: modelListData } = queries.model.useList()
const modelItems = computed(() => modelListData.value?.items ?? [])

// Flat columns for individual evaluation jobs
const flatColumns: ColumnDef<EvaluationJob, unknown>[] = [
  componentColumn<EvaluationJob>('varian_name', m.evaluation_variantDetails(), VariantName, {
    accessorKey: 'tool',
    sortable: true,
    sortFn: (a, b) => {
      const aName = a.tool?.variant_name || ''
      const bName = b.tool?.variant_name || ''
      return aName.localeCompare(bName)
    },
  }),
  {
    id: 'modelLabel',
    accessorFn: (row: EvaluationJob) => {
      const activeVariantModel = row.tool?.variant_object?.system_name_for_model as string | undefined
      const modelLabel = (modelItems.value || []).find(
        (option: Record<string, unknown>) => option.system_name === activeVariantModel,
      )?.display_name
      return modelLabel || ''
    },
    header: m.common_model(),
    enableSorting: true,
    cell: ({ getValue }) => {
      const val = getValue()
      return val || '-'
    },
    meta: { align: 'left' },
  } as ColumnDef<EvaluationJob, unknown>,
  componentColumn<EvaluationJob>('status', m.common_status(), Status, {
    accessorKey: 'status',
    sortable: true,
  }),
  componentColumn<EvaluationJob>('score', m.evaluation_avgScore(), Score, {
    accessorKey: 'average_score',
    sortable: true,
    sortFn: (a, b) => (a.average_score || 0) - (b.average_score || 0),
  }),
  componentColumn<EvaluationJob>('average_latency', m.evaluation_avgLatencyMs(), Latency, {
    accessorKey: 'average_latency',
    sortable: true,
    sortFn: (a, b) => (a.average_latency || 0) - (b.average_latency || 0),
  }),
  componentColumn<EvaluationJob>('avg_cost', m.evaluation_avgCostUsd(), Cost, {
    accessorKey: 'average_cost',
    sortable: true,
    sortFn: (a, b) => (a.average_cost || 0) - (b.average_cost || 0),
  }),
  componentColumn<EvaluationJob>('report', m.common_report(), Report, {
    align: 'center',
  }),
]

// Use useDataTable to fetch data
const { table: flatTable, rows: allRows, isLoading, isFetching, globalFilter, refetch } = useDataTable<EvaluationJob>(
  'evaluation_jobs',
  flatColumns,
)

// Grouped data computation
interface GroupedRow extends EvaluationJob {
  groupId: string
  groupKey: string
  tools: unknown[]
  test_sets: string[]
  max_score_tool: EvaluationJob | undefined
  records: EvaluationJob[]
}

function groupRecordsByKey(data: EvaluationJob[], key: string): GroupedRow[] {
  return _.chain(data)
    .groupBy(key)
    .map((records, groupKeyId) => {
      return {
        groupId: groupKeyId,
        groupKey: key,
        average_cached_tokens: _.mean(records.map((record: Record<string, unknown>) => record.average_cached_tokens as number)),
        average_completion_tokens: _.mean(records.map((record: Record<string, unknown>) => record.average_completion_tokens as number)),
        average_latency: _.mean(records.map((record) => record.average_latency || 0)),
        average_prompt_tokens: _.mean(records.map((record: Record<string, unknown>) => record.average_prompt_tokens as number)),
        average_score: _.mean(
          records.map((record) => record.average_score || 0).filter((score) => score > 0),
        ),
        records_count: _.sum(records.map((record: Record<string, unknown>) => record.records_count as number)),
        results_with_score: _.sum(records.map((record: Record<string, unknown>) => record.results_with_score as number)),
        started_at: _.min(records.map((record: Record<string, unknown>) => new Date(record.started_at as string).toISOString())),
        type: records[0]?.type,
        tool: records[0]?.tool,
        tools: _.uniqBy(
          records.map((record) => record.tool),
          'variant_name',
        ),
        test_sets: _.uniq(_.flatten(records.map((record: Record<string, unknown>) => record.test_sets as string[]))),
        max_score_tool: _.maxBy(records, 'average_score'),
        records,
      } as unknown as GroupedRow
    })
    .value()
}

const groupedByJobRows = computed(() => groupRecordsByKey(allRows.value, 'job_id'))
const groupedByToolRows = computed(() => groupRecordsByKey(allRows.value, 'tool.system_name'))

// Grouped columns - simplified for grouped view
const groupedColumns: ColumnDef<EvaluationJob, unknown>[] = [
  componentColumn<EvaluationJob>('varian_name', m.evaluation_variantDetails(), VariantName, {
    accessorKey: 'tool',
    sortable: true,
  }),
  componentColumn<EvaluationJob>('status', m.common_status(), Status, {
    accessorKey: 'status',
    sortable: true,
  }),
  componentColumn<EvaluationJob>('score', m.evaluation_avgScore(), Score, {
    accessorKey: 'average_score',
    sortable: true,
  }),
  componentColumn<EvaluationJob>('average_latency', m.evaluation_avgLatencyMs(), Latency, {
    accessorKey: 'average_latency',
    sortable: true,
  }),
  componentColumn<EvaluationJob>('avg_cost', m.evaluation_avgCostUsd(), Cost, {
    accessorKey: 'average_cost',
    sortable: true,
  }),
  componentColumn<EvaluationJob>('report', m.common_report(), Report, {
    align: 'center',
  }),
]

// Computed rows based on current group mode + filter
const currentRows = computed<EvaluationJob[]>(() => {
  let records: EvaluationJob[]
  if (groupBy.value === 'job') {
    records = groupedByJobRows.value as unknown as EvaluationJob[]
  } else if (groupBy.value === 'tool') {
    records = groupedByToolRows.value as unknown as EvaluationJob[]
  } else {
    records = allRows.value
  }

  return records.filter((record: Record<string, unknown>) => {
    if (filterObject.value.tool) {
      return (record.tool as Record<string, unknown>)?.system_name === filterObject.value.tool
    }
    if (filterObject.value.job) {
      return record.job_id === filterObject.value.job
    }
    return true
  })
})

// Create a separate table for grouped views
const groupedTable = useVueTable<EvaluationJob>({
  get data() {
    return currentRows.value
  },
  columns: groupedColumns,
  getCoreRowModel: getCoreRowModel(),
  manualPagination: false,
  manualSorting: false,
  manualFiltering: false,
})

// Switch between flat and grouped tables
const currentTable = computed(() => {
  if (groupBy.value === 'flat') return flatTable
  return groupedTable
})

// Computed display values
const filterObjectStartData = computed(() => {
  const data = filterObject.value?.row?.started_at as string
  if (!data) return ''
  const date = new Date(data)
  const day = String(date.getDate()).padStart(2, '0')
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const year = date.getFullYear()
  const hours = String(date.getHours()).padStart(2, '0')
  const minutes = String(date.getMinutes()).padStart(2, '0')
  return `${day}.${month}.${year} ${hours}:${minutes}`
})

// Handle route query for initial filter
if (route.query?.job_id) {
  filterObject.value = {
    job: (route.query.job_id as string) || '',
    tool: '',
    row: null,
  }
}

// Methods
async function getEvaluationReport() {
  const ids = selected.value.map((obj) => obj._id)
  const evalStore = useEvaluationStore()
  await evalStore.generateEvaluationReport({ ids })
}

function compare(all = false) {
  const ids = all
    ? currentRows.value.map((obj) => obj._id)
    : selected.value.map((obj) => obj._id)
  router.push({
    name: 'EvaluationCompare',
    query: { ids: (ids as string[]).join(',') },
  })
}

function removeFilter() {
  if (filterObject.value.tool) {
    groupBy.value = 'tool'
  }
  if (filterObject.value.job) {
    groupBy.value = 'job'
  }
  filterObject.value = {
    tool: '',
    job: '',
    row: null,
  }
}

function selectRecord(row: EvaluationJob) {
  const rowAny = row as unknown as GroupedRow
  if (groupBy.value === 'flat') {
    openDetails(row)
    return
  }
  if (groupBy.value === 'job') {
    groupBy.value = 'flat'
    filterObject.value.job = rowAny.groupId
    filterObject.value.row = rowAny as unknown as Record<string, unknown>
  }
  if (groupBy.value === 'tool') {
    groupBy.value = 'flat'
    filterObject.value.tool = (rowAny.tool as Record<string, unknown>)?.system_name as string
    filterObject.value.row = rowAny as unknown as Record<string, unknown>
  }
}

async function openDetails(row: EvaluationJob) {
  await router.push(`/evaluation-jobs/${row._id}`)
}

async function deleteSelected() {
  // Parallel removes — useSafeMutation ensures one failure doesn't
  // reject the whole Promise.all and stop later cleanups.
  await Promise.all(
    selected.value.map((obj) => removeEvalJob.run(obj._id!)),
  )
  selected.value = []
  showDeleteDialog.value = false
}

async function rerunSelected() {
  for (const obj of selected.value) {
    const evalObj = obj as Record<string, unknown>
    const evalSet = evalObj?.evaluation_set as Record<string, unknown> | undefined
    const evalTools = evalObj?.evaluated_tools as Record<string, unknown>[] | undefined
    if (!evalSet?.system_name || !(evalTools?.length)) continue

    const evaluation_set = evalSet.system_name as string
    const resultItems = evalObj?.result_items as Record<string, unknown>[] | undefined
    const iteration_count = Math.max(...(resultItems || []).map((item) => item.iteration as number)) || 1
    const evaluation_target_tools = evalTools.map((tool) => tool?.system_name as string)

    await createEvalJob.run({
      evaluation_set,
      iteration_count,
      evaluation_target_tools,
    } as unknown as Partial<EvaluationJob>)
  }

  selected.value = []
  showRerunDialog.value = false
  refetch()
}
</script>


<template lang="pug">
.column.no-wrap.full-height
  .collection-container.q-mx-auto.full-width.column.full-height.q-px-md.q-pt-16
    .col.ba-border.border-radius-12.bg-white.q-pa-16.column(style='min-height: 0')
      .row.q-mb-12
        .col-auto.center-flex-y
          km-input(:placeholder='m.common_search()', iconBefore='search', :modelValue='globalFilter', @input='globalFilter = $event', clearable)
        .col-auto.center-flex-y.q-ml-md(v-if='groupBy !== "flat"')
          .text-secondary-text.q-mr-sm Group by:
          km-select(
            :options='groups',
            v-model='groupBy',
            bg-color='background',
            height='30px',
            map-options,
            emit-value,
            option-value='value',
            option-label='label'
          )
        .col-auto.center-flex-y.q-ml-md
          template(v-if='filterObject?.tool || filterObject?.job')
            .text-secondary-text.q-mr-sm {{ filterObject?.tool ? 'Tool:' : 'Job:' }}
            q-chip.q-my-none(text-color='primary', color='primary-light', square, size='12px')
              .row.fit.items-center
                .col.text-center {{ filterObject?.tool ? filterObject?.tool : filterObject?.job }}
                .col-auto.q-ml-xs
                  q-icon.q-my-auto.cursor-pointer(name='fa fa-times', @click.stop.prevent='removeFilter')
        q-space
        .col-auto.center-flex-y
          km-btn.q-mr-12(
            v-if='groupBy == "flat"',
            icon='fas fa-download',
            label='Report',
            @click='getEvaluationReport',
            iconColor='icon',
            hoverColor='primary',
            labelClass='km-title',
            flat,
            iconSize='16px',
            hoverBg='primary-bg',
            :disable='selected.length < 2',
            :tooltip='selected.length < 2 ? "Select at least 2 records" : ""'
          )
        .col-auto.center-flex-y
          km-btn.q-mr-12(
            v-if='groupBy == "flat"',
            icon='compare',
            label='Compare',
            @click='compare(false)',
            iconColor='icon',
            hoverColor='primary',
            labelClass='km-title',
            flat,
            iconSize='16px',
            hoverBg='primary-bg',
            :disable='selected.length < 2',
            :tooltip='selected.length < 2 ? "Select at least 2 records" : ""'
          )
        .col-auto.center-flex-y
          km-btn.q-mr-12(
            v-if='groupBy == "flat"',
            icon='delete',
            label='Delete',
            @click='showDeleteDialog = true',
            iconColor='icon',
            hoverColor='primary',
            labelClass='km-title',
            flat,
            iconSize='16px',
            hoverBg='primary-bg',
            :disable='selected.length < 1',
            :tooltip='selected.length < 1 ? "Select at least 1 records" : ""'
          )
        .col-auto.center-flex-y
          km-btn.q-mr-12(
            icon='refresh',
            label='Refresh list',
            @click='refetch',
            iconColor='icon',
            hoverColor='primary',
            labelClass='km-title',
            flat,
            iconSize='16px',
            hoverBg='primary-bg'
          )
        .col-auto.center-flex-y
          km-btn.q-mr-12(v-if='!filterObject?.row', :label='m.common_new()', @click='showNewDialog = true')
      q-separator.q-my-sm
      .row.q-mb-sm.items-center(v-if='filterObject?.row')
        .col-auto
          .column
            .col(v-if='filterObject?.job')
              .row.q-gap-12.no-wrap.items-baseline
                .col-auto
                  .km-field.text-secondary-text Job start:
                .col-auto
                  .km-heading-3.q-mr-sm {{ filterObjectStartData }}
            .col
              .row.q-gap-12.no-wrap.items-baseline
                .col-auto
                  .km-field.text-secondary-text Evaluated tool:
                .col-auto
                  .km-heading-3.q-mr-sm {{ filterObject?.row?.tool?.name }}
            .col(v-if='filterObject?.job')
              .row.q-gap-12.no-wrap.items-baseline
                .col-auto
                  .km-field.text-secondary-text Test set:
                .col-auto
                  .km-heading-3.q-mr-sm {{ filterObject?.row?.test_sets?.[0] }}
        .col.q-ml-md
          q-chip.km-small-chip(
            color='in-progress',
            text-color='text-gray',
            :label='filterObject.row?.type === "prompt_eval" ? "Prompt Template" : "RAG"'
          )
      q-separator.q-my-sm(v-if='filterObject?.row')
      .col(style='min-height: 0')
        km-data-table(
          :table='currentTable',
          :loading='isLoading', :fetching='isFetching',
          :fill-height='!filterObject?.row',
          row-key='id',
          @row-click='selectRecord'
        )
    evaluation-jobs-create-new(:showNewDialog='showNewDialog', @cancel='showNewDialog = false', v-if='showNewDialog')
km-popup-confirm(
  :visible='showDeleteDialog',
  confirmButtonLabel='Delete',
  cancelButtonLabel='Cancel',
  notificationIcon='fas fa-triangle-exclamation',
  @confirm='deleteSelected',
  @cancel='showDeleteDialog = false'
)
  .row.item-center.justify-center.km-heading-7 Delete Evaluation
  .row.text-center.justify-center {{ `You are going to delete ${selected?.length} selected Evaluation. Are you sure?` }}

km-popup-confirm(
  :visible='showRerunDialog',
  confirmButtonLabel='Run',
  cancelButtonLabel='Cancel',
  notificationIcon='fas fa-triangle-exclamation',
  @confirm='rerunSelected',
  @cancel='showRerunDialog = false'
)
  .row.item-center.justify-center.km-heading-7 Rerun Evaluation
  .row.text-center.justify-center {{ `You are going to rerun ${selected?.length} selected Evaluation. Are you sure?` }}
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useVueTable, getCoreRowModel, type ColumnDef } from '@tanstack/vue-table'
import { useDataTable } from '@/composables/useDataTable'
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
  { label: 'Evaluation job', value: 'job' },
  { label: 'Evaluated tool', value: 'tool' },
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
const { mutateAsync: removeEvalJob } = evalJobsQ.useRemove()
const { mutateAsync: createEvalJob } = evalJobsQ.useCreate()
const { data: modelListData } = queries.model.useList()
const modelItems = computed(() => modelListData.value?.items ?? [])

// Flat columns for individual evaluation jobs
const flatColumns: ColumnDef<EvaluationJob, unknown>[] = [
  componentColumn<EvaluationJob>('varian_name', 'Variant details', VariantName, {
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
    header: 'Model',
    enableSorting: true,
    cell: ({ getValue }) => {
      const val = getValue()
      return val || '-'
    },
    meta: { align: 'left' },
  } as ColumnDef<EvaluationJob, unknown>,
  componentColumn<EvaluationJob>('status', 'Status', Status, {
    accessorKey: 'status',
    sortable: true,
  }),
  componentColumn<EvaluationJob>('score', 'Avg score', Score, {
    accessorKey: 'average_score',
    sortable: true,
    sortFn: (a, b) => (a.average_score || 0) - (b.average_score || 0),
  }),
  componentColumn<EvaluationJob>('average_latency', 'Avg latency (ms)', Latency, {
    accessorKey: 'average_latency',
    sortable: true,
    sortFn: (a, b) => (a.average_latency || 0) - (b.average_latency || 0),
  }),
  componentColumn<EvaluationJob>('avg_cost', 'Avg cost ($)', Cost, {
    accessorKey: 'average_cost',
    sortable: true,
    sortFn: (a, b) => (a.average_cost || 0) - (b.average_cost || 0),
  }),
  componentColumn<EvaluationJob>('report', 'Report', Report, {
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
  componentColumn<EvaluationJob>('varian_name', 'Variant details', VariantName, {
    accessorKey: 'tool',
    sortable: true,
  }),
  componentColumn<EvaluationJob>('status', 'Status', Status, {
    accessorKey: 'status',
    sortable: true,
  }),
  componentColumn<EvaluationJob>('score', 'Avg score', Score, {
    accessorKey: 'average_score',
    sortable: true,
  }),
  componentColumn<EvaluationJob>('average_latency', 'Avg latency (ms)', Latency, {
    accessorKey: 'average_latency',
    sortable: true,
  }),
  componentColumn<EvaluationJob>('avg_cost', 'Avg cost ($)', Cost, {
    accessorKey: 'average_cost',
    sortable: true,
  }),
  componentColumn<EvaluationJob>('report', 'Report', Report, {
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
  await Promise.all(
    selected.value.map((obj) => removeEvalJob(obj._id!)),
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

    await createEvalJob({
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

<style lang="stylus">
.km-input:not(.q-field--readonly) .q-field__control::before
  background: #fff !important;
</style>

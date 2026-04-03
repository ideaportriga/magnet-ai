import { required, minLength } from '@shared/utils/validationRules'
import NameDescription from './component/NameDescription.vue'
import VariantName from './component/VariantName.vue'
import Report from './component/Report.vue'
import EvaluatedTools from './component/EvaluatedTools.vue'
import SubHeaderJob from './component/SubHeaderJob.vue'
import { markRaw } from 'vue'
import DateTime from './component/DateTime.vue'
import Type from './component/Type.vue'
import MaxScore from './component/MaxScore.vue'
import JobStatus from './component/JobStatus.vue'
import { formatDateTime } from '@shared/utils/dateTime'
import { m } from '@/paraglide/messages'

export const statusOptions = [
  { value: 'in_progress', label: m.status_inProgress() },
  { value: 'completed', label: m.status_completed() },
  { value: 'failed', label: m.status_failed() },
]

const controls = {
  id: {
    name: 'id',
    label: 'id',
    field: '_id',
    readonly: true,
    display: false,
    ignorePatch: true,
    fromMetadata: false,
  },
  _id: {
    name: 'id',
    label: 'id',
    field: '_id',
    readonly: true,
    display: false,
    ignorePatch: true,
    fromMetadata: false,
  },
  job_start: {
    name: 'job_start',
    label: m.evaluation_startedAt(),
    field: 'started_at',
    display: true,
    readonly: true,
    // type: 'Date',
    format: (val) => formatDateTime(val),
    ignorePatch: true,
    columnNumber: 6,
    fromMetadata: false,
    align: 'left',
    sortable: true,
    sort: (a, b) => {
      const dateObjectA = new Date(a)
      const dateObjectB = new Date(b)
      return dateObjectA - dateObjectB
    },
    component: markRaw(DateTime),
    type: 'component',
  },
  status: {
    name: 'status',
    label: m.common_status(),
    type: 'component',
    component: markRaw(JobStatus),
    display: true,
    sortable: true,
    field: (row) => {
      const status = row.status
      const statusOption = statusOptions.find((option) => option.value === status)
      return statusOption ? statusOption.label : status
    },
    align: 'left',
  },
  tool_type: {
    name: 'tool_type',
    display: true,
    label: m.evaluation_toolType(),
    type: 'component',
    readonly: true,
    align: 'left',
    component: markRaw(Type),
    style: 'max-width: 150px;', // Apply max-width to data cells
    headerStyle: 'max-width: 150px;', // Apply max-width to header cells
    rules: [required(), minLength(1, 'Evaluated tools must include at least 1 tool')],
    validate: true,
    field: (row) => {
      return row?.type || ''
    },
    sortable: true,
  },
  evaluated_tools: {
    name: 'evaluated_tools',
    display: true,
    label: m.evaluation_toolName(),
    type: 'component',
    readonly: true,
    align: 'left',
    component: markRaw(EvaluatedTools),
    style: 'max-width: 150px;', // Apply max-width to data cells
    headerStyle: 'max-width: 150px;', // Apply max-width to header cells
    rules: [required(), minLength(1, 'Evaluated tools must include at least 1 tool')],
    validate: true,
    field: (row) => {
      return row.tool?.name || ''
    },
    sortable: true,
  },
  varian_name: {
    name: 'varian_name',
    label: m.common_variants(),
    type: 'component',
    component: markRaw(VariantName),
    display: true,
    sortable: true,
    align: 'left',
    validate: true,
    field: (row) => {
      return row?.tool?.variant_name || ''
    },
    rules: [required()],
  },
  test_set_type: {
    name: 'test_set_type',
    label: m.entity_testSet(),
    type: 'component',
    component: markRaw(NameDescription),
    display: true,
    sortable: true,
    align: 'left',
    validate: true,
    field: (row) => {
      return row.test_set?.name || ''
    },
    rules: [required()],
  },
  // execution_time: {
  //   name: 'execution_time',
  //   display: true,
  //   label: 'Job run time',
  //   type: 'component',
  //   component: markRaw(ExecutionTime),
  //   align: 'left',
  //   sortable: false
  // },

  max_score: {
    name: 'max_score',
    label: m.evaluation_maxAvgScore(),
    type: 'component',
    component: markRaw(MaxScore),
    display: true,
    sortable: true,
    align: 'center',
  },

  // average_latency: {
  //   name: 'average_latency',
  //   label: 'Avg latency (ms)',
  //   field: 'average_latency',
  //   type: 'component',
  //   display: true,
  //   sortable: true,
  //   component: markRaw(Latency),
  //   format: (val) => val.toFixed(0),
  // },

  // iteration_count: {
  //   name: 'iteration_count',
  //   label: 'Iteration Count',
  //   field: 'iteration_count',
  //   validate: true,
  //   // display: true,
  //   sortable: true,
  //   align: 'left',
  //   rules: [required(), notGreaterThan(5), notLessThan(1)]
  // },
  // avg_cost: {
  //   name: 'avg_cost',
  //   label: 'Avg cost ($)',
  //   type: 'component',
  //   field: 'average_cost',
  //   component: markRaw(Cost),
  //   display: true,
  //   sortable: true,
  // },
  report: {
    name: 'report',
    code: 'report',
    type: 'component',
    display: true,
    label: m.common_report(),
    component: markRaw(Report),
    align: 'center',
  },
  subheader: {
    name: 'subheader',
    type: 'component',
    field: 'subheader',
    component: markRaw(SubHeaderJob),
    sortable: true,
  },
}

export default controls

import { required, minLength } from '@shared/utils/validationRules'
import Report from './component/Report.vue'
import MaxScore from './component/MaxScore.vue'
import EvaluatedTools from './component/EvaluatedTools.vue'
import Type from './component/Type.vue'
import { markRaw } from 'vue'
import DateTime from './component/DateTime.vue'
import { formatDateTime } from '@shared/utils/dateTime'

export const statusOptions = [
  { value: 'in_progress', label: 'In progress' },
  { value: 'completed', label: 'Completed' },
  { value: 'failed', label: 'Failed' },
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
  evaluated_tools: {
    name: 'evaluated_tools',
    display: true,
    label: 'Tool name',
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
  tool_type: {
    name: 'tool_type',
    display: true,
    label: 'Tool type',
    type: 'component',
    readonly: true,
    align: 'left',
    component: markRaw(Type),
    style: 'max-width: 150px;', // Apply max-width to data cells
    headerStyle: 'max-width: 150px;', // Apply max-width to header cells
    rules: [required(), minLength(1, 'Evaluated tools must include at least 1 tool')],
    validate: true,
    field: (row) => {
      return row.tool?.name || ''
    },
    sortable: true,
  },
  job_start: {
    name: 'job_start',
    label: 'Last Eval started',
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

  total_evaluations: {
    name: 'total_evaluations',
    label: 'Total evaluations',
    field: (row) => row?.records?.length || 0,
    display: true,
    sortable: true,
    align: 'left',
  },

  max_score: {
    name: 'max_score',
    label: 'Max score',
    type: 'component',
    component: markRaw(MaxScore),
    display: true,
    sortable: true,
    align: 'center',
  },

  // varian_name: {
  //   name: 'varian_name',
  //   label: 'Variant Info',
  //   type: 'component',
  //   component: markRaw(VariantName),
  //   display: true,
  //   sortable: true,
  //   align: 'left',
  //   validate: true,
  //   field: (row) => {
  //     return row?.tool?.variant_name || ''
  //   },
  //   rules: [required()]
  // },
  // test_set_type: {
  //   name: 'test_set_type',
  //   label: 'Test Set',
  //   type: 'component',
  //   component: markRaw(NameDescription),
  //   display: true,
  //   sortable: true,
  //   align: 'left',
  //   validate: true,
  //   field: (row) => {
  //     return row.test_set?.name || ''
  //   },
  //   rules: [required()]
  // },
  // // execution_time: {
  // //   name: 'execution_time',
  // //   display: true,
  // //   label: 'Job run time',
  // //   type: 'component',
  // //   component: markRaw(ExecutionTime),
  // //   align: 'left',
  // //   sortable: false
  // // },

  // score: {
  //   name: 'score',
  //   label: 'Avg score',
  //   type: 'component',
  //   field: 'average_score',
  //   component: markRaw(Score),
  //   display: true,
  //   sortable: true,
  // },

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
    label: 'Report',
    component: markRaw(Report),
    align: 'center',
  },
  // subheader: {
  //   name: 'subheader',
  //   type: 'component',
  //   field: 'subheader',
  //   component: markRaw(SubHeaderTool),
  //   sortable: true,
  // },
}

export default controls

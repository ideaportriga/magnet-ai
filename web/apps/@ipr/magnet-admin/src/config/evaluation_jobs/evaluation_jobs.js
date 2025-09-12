import { required, minLength, notGreaterThan, notLessThan } from '@shared/utils/validationRules'
import NameDescription from './component/NameDescription.vue'
import VariantName from './component/VariantName.vue'
import Latency from './component/Latency.vue'
import Report from './component/Report.vue'
import Cost from './component/Cost.vue'
import EvaluatedTools from './component/EvaluatedTools.vue'
import Score from './component/Score.vue'
import Status from './component/Status.vue'
import { markRaw } from 'vue'
import store from '@/store'

export const statusOptions = [
  { value: 'in_progress', label: 'In progress' },
  { value: 'completed', label: 'Completed' },
  { value: 'failed', label: 'Failed' },
  { value: 'ready_for_eval', label: 'Ready for eval' },
  { value: 'eval_in_progress', label: 'Eval in progress' },
  { value: 'eval_complited', label: 'Eval completed' },
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
  varian_name: {
    name: 'varian_name',
    label: 'Variant details',
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
  modelLabel: {
    name: 'modelLabel',
    display: true,
    sortable: true,
    label: 'Model',
    align: 'left',
    field: (row) => {
      const activeVariantModel = row.tool?.variant_object?.system_name_for_model
      const modelLabel = (store.getters['chroma/model'].items || []).find((option) => option.system_name == activeVariantModel)?.display_name
      return modelLabel
    },
  },
  status: {
    name: 'status',
    label: 'Status',
    type: 'component',
    component: markRaw(Status),
    display: true,
    sortable: true,
    field: (row) => {
      const status = row.status
      const statusOption = statusOptions.find((option) => option.value === status)
      return statusOption ? statusOption.label : status
    },
    align: 'left',
  },
  evaluated_tools: {
    name: 'evaluated_tools',
    display: false,
    label: 'Evaluated tools',
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

  test_set_type: {
    name: 'test_set_type',
    label: 'Test Set',
    type: 'component',
    component: markRaw(NameDescription),
    display: false,
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

  score: {
    name: 'score',
    label: 'Avg score',
    type: 'component',
    field: 'average_score',
    component: markRaw(Score),
    display: true,
    sortable: true,
  },

  average_latency: {
    name: 'average_latency',
    label: 'Avg latency (ms)',
    field: 'average_latency',
    type: 'component',
    display: true,
    sortable: true,
    component: markRaw(Latency),
    format: (val) => val.toFixed(0),
  },

  iteration_count: {
    name: 'iteration_count',
    label: 'Iteration Count',
    field: 'iteration_count',
    validate: true,
    // display: true,
    sortable: true,
    align: 'left',
    rules: [required(), notGreaterThan(5), notLessThan(1)],
  },
  avg_cost: {
    name: 'avg_cost',
    label: 'Avg cost ($)',
    type: 'component',
    field: 'average_cost',
    component: markRaw(Cost),
    display: true,
    sortable: true,
  },
  report: {
    name: 'report',
    code: 'report',
    type: 'component',
    display: true,
    label: 'Report',
    component: markRaw(Report),
    align: 'center',
  },
}

export default controls

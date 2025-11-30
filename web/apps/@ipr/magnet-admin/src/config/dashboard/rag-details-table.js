import { formatDateTime } from '@shared/utils/dateTime'
import { formatDuration } from '@shared/utils'
import Answer from './components/Answer.vue'
import Chip from './components/Chip.vue'
import FeedbackChip from './components/FeedbackChip.vue'
import NameVariant from './components/NameVariant.vue'
import Source from './components/Source.vue'
import { markRaw } from 'vue'
import ChipCell from './components/ChipCell.vue'

const controls = {
  start_time: {
    name: 'start_time',
    label: 'Start time',
    field: 'start_time',
    readonly: true,
    columnNumber: 1,
    format: (val) => formatDateTime(val),
    align: 'left',
    display: true,
    sortable: true,
    sort: (a, b) => {
      if (!a) return 1
      if (!b) return -1

      const dateObjectA = new Date(a)
      const dateObjectB = new Date(b)
      return dateObjectA - dateObjectB
    },
  },
  name: {
    name: 'name',
    label: 'Name & variant',
    field: 'name',
    readonly: true,
    columnNumber: 0,
    type: 'component',
    component: markRaw(NameVariant),
    align: 'left',
    display: true,
    sortable: true,
    action: 'select',
  },
  source: {
    name: 'source',
    label: 'Consumer info',
    field: 'source',
    readonly: true,
    columnNumber: 1,
    type: 'component',
    component: markRaw(Source),
    align: 'left',
    display: true,
    sortable: true,
  },
  latency: {
    name: 'latency',
    label: 'Latency',
    field: 'latency',
    readonly: true,
    display: true,
    sortable: true,
    format: (val) => formatDuration(val),
    align: 'left',
  },
  cost: {
    name: 'cost',
    label: 'Cost',
    field: 'cost',
    readonly: true,
    display: true,
    sortable: true,
    format: (val) => `${val?.toFixed(6)} $`,
    align: 'left',
  },

  trace_id: {
    name: 'trace_id',
    label: 'Trace ID',
    field: 'trace_id',
    readonly: true,
    columnNumber: 2,
    display: false,
  },
  // channel: {
  //   name: 'channel',
  //   label: 'Channel',
  //   field: 'channel',
  //   readonly: true,
  //   columnNumber: 2,
  //   align: 'left',
  //   class: 'text-capitalize',
  // },
  ['extra_data.question']: {
    name: 'extra_data.question',
    label: 'Question',
    readonly: true,
    columnNumber: 3,
    field: (row) => row?.extra_data?.question ?? '-',
    align: 'left',
    type: 'component',
    component: markRaw(Answer),
    style: 'max-width: 250px',
    display: true,
    sortable: true,
  },
  ['extra_data.answer']: {
    name: 'extra_data.answer',
    label: 'Answer',
    //field: 'response',
    readonly: true,
    columnNumber: 4,
    //field: (row) => row?.extra_data?.answer ?? 'N/A',
    type: 'component',
    component: markRaw(Answer),
    align: 'left',
    style: 'max-width: 250px',
    display: true,
    sortable: true,
  },
  topic: {
    name: 'topic',
    label: 'Question topic',
    field: 'topic',
    readonly: true,
    columnNumber: 6,
    field: (row) => row?.extra_data?.topic ?? '-',
    align: 'left',
    display: true,
    sortable: true,
  },
  ['extra_data.is_answered']: {
    name: 'extra_data.is_answered',
    label: 'Answered',
    field: 'is_answered',
    readonly: true,
    columnNumber: 5,
    type: 'component',
    component: markRaw(Chip),
    align: 'left',
    display: true,
    sortable: true,
  },
  ['extra_data.answer_feedback.type']: {
    name: 'extra_data.answer_feedback.type',
    label: 'User feedback',
    field: 'feedback',
    readonly: true,
    columnNumber: 7,
    type: 'component',
    component: markRaw(FeedbackChip),
    align: 'left',
    display: true,
    sortable: true,
  },
  // ['extra_data.language']: {
  //   name: 'extra_data.language',
  //   label: 'Language',
  //   field: 'language',
  //   readonly: true,
  //   columnNumber: 8,
  //   field: (row) => row?.extra_data?.language ?? '-',
  //   align: 'left',
  //   display: true,
  //   sortable: true,
  // },
  ['x_attributes.org-id']: {
    name: 'x_attributes.org-id',
    label: 'Organization',
    field: 'x_attributes.org-id',
    display: true,
    align: 'left',
    type: 'component',
    component: markRaw(ChipCell),
    sortable: true,
  },
}

export default controls

import { markRaw, h } from 'vue'
import NameVariant from './components/NameVariant.vue'
import { formatDateTime } from '@shared/utils/dateTime'
import { formatDuration } from '@shared/utils'
import ResolutionChip from './components/ResolutionChip.vue'
import AgentFeedback from './components/AgentFeedback.vue'
import Topics from './components/Topics.vue'
import Source from './components/Source.vue'
import ChipCell from './components/ChipCell.vue'

const controls = {
  start_time: {
    name: 'start_time',
    label: 'Start time',
    field: 'start_time',
    readonly: true,
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
    type: 'component',
    component: markRaw(NameVariant),
    align: 'left',
    display: true,
    sortable: true,
    //action: 'select',
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
  status: {
    name: 'status',
    label: 'Status',
    field: 'status',
    readonly: true,
    align: 'left',
    display: true,
    sortable: true,
  },
  ['conversation_data.avg_tool_call_latency']: {
    name: 'conversation_data.avg_tool_call_latency',
    label: 'Avg. latency',
    readonly: true,
    display: true,
    field: (row) => row?.conversation_data?.avg_tool_call_latency,
    format: (val) => formatDuration(val),
    align: 'left',
    sortable: true,
  },
  cost: {
    name: 'cost',
    label: 'Total cost',
    field: 'cost',
    readonly: true,
    align: 'left',
    sortable: true,
    display: true,
    format: (val) => {
      if (!val) return null
      return `${val?.toFixed(6)} $`
    },
  },
  ['conversation_data.topics']: {
    name: 'intent',
    label: 'Agent topic',
    readonly: true,
    align: 'left',
    display: true,
    type: 'component',
    component: markRaw(Topics),
  },
  ['conversation_data.resolution_status']: {
    name: 'conversation_data.resolution_status',
    label: 'Resolution status',
    field: 'conversation_data.resolution_status',
    readonly: true,
    align: 'left',
    display: true,
    type: 'component',
    component: markRaw(ResolutionChip),
    sortable: true,
  },

  feedback: {
    name: 'feedback',
    label: 'User feedback',
    field: 'feedback',
    readonly: true,
    align: 'left',
    display: true,
    type: 'component',
    component: markRaw(AgentFeedback),
  },

  ['conversation_data.language']: {
    name: 'conversation_data.language',
    label: 'Language',
    field: (row) => row?.conversation_data?.language ?? '-',
    readonly: true,
    align: 'left',
    display: true,
    sortable: true,
  },
  ['conversation_data.sentiment']: {
    name: 'conversation_data.sentiment',
    label: 'Sentiment',
    field: (row) => row?.conversation_data?.sentiment ?? '-',
    readonly: true,
    align: 'left',
    display: true,
    type: 'component',
    component: ({ row }) => {
      if (!row?.conversation_data?.sentiment) return null
      let colorProps = {
        color: 'in-progress',
        textColor: 'text-text-grey text-capitalize',
      }
      if (row?.conversation_data?.sentiment === 'positive') {
        colorProps = {
          color: 'like-bg',
          textColor: 'text-like-text text-capitalize',
        }
      } else if (row?.conversation_data?.sentiment === 'negative') {
        colorProps = {
          color: 'dislike-bg',
          textColor: 'text-error-text text-capitalize',
        }
      }
      const props = {
        row: row,
        name: 'conversation_data.sentiment',
        ...colorProps,
      }
      return h(ChipCell, props)
    },
    sortable: true,
  },
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

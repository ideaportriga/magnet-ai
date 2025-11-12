import { formatDuration } from '@shared/utils'
const controls = {
  name: {
    name: 'name',
    label: 'RAG Name',
    field: 'name',
    readonly: true,
    columnNumber: 0,
    fromMetadata: false,
    ignorePatch: true,
    action: 'drilldown',
    validate: true,
    align: 'left',
    sortable: true,
  },

  count: {
    name: 'count',
    label: 'Total tool calls',
    field: 'count',
    readonly: true,
    columnNumber: 0,
    fromMetadata: false,
    ignorePatch: true,
    validate: true,
    align: 'left',
    sortable: true,
  },
  unique_user_count: {
    name: 'unique_user_count',
    label: 'Unique users',
    field: 'unique_user_count',
    readonly: true,
    align: 'left',
    sortable: true,
  },
  avg_total_cost: {
    name: 'avg_total_cost',
    label: 'Avg tool call cost',
    field: 'avg_total_cost',
    readonly: true,
    align: 'left',
    format: (val) => (val ? `${Number(val).toFixed(6)} $` : ''),
    sortable: true,
  },
  avg_latency: {
    name: 'avg_latency',
    label: 'Avg tool call latency',
    field: 'avg_latency',
    readonly: true,
    align: 'left',
    format: (val) => (val ? `${formatDuration(val)}` : ''),
    sortable: true,
  },
}

export default controls

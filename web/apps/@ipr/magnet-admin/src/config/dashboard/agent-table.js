import { formatDuration } from '@shared/utils'

const controls = {
  name: {
    name: 'name',
    label: 'Agent Name',
    field: 'name',
    readonly: true,
    columnNumber: 0,
    align: 'left',
    action: 'filterAgent',
    sortable: true,
  },
  count: {
    name: 'count',
    label: 'Total conversations',
    field: 'count',
    readonly: true,
    columnNumber: 0,
    align: 'left',
    sortable: true,
  },
  unique_user_count: {
    name: 'unique_user_count',
    label: 'Unique users',
    field: 'unique_user_count',
    readonly: true,
    columnNumber: 0,
    align: 'left',
    sortable: true,
  },
  cost: {
    name: 'avg_total_cost',
    label: 'Avg. conversation cost',
    field: 'avg_total_cost',
    readonly: true,
    columnNumber: 0,
    format: (val) => (val ? `${Number(val).toFixed(6)} $` : ''),
    align: 'left',
    sortable: true,
  },
  avg_tool_call_latency: {
    name: 'avg_tool_call_latency',
    label: 'Avg. latency',
    field: 'avg_tool_call_latency',
    readonly: true,
    columnNumber: 0,
    format: (val) => (val ? `${formatDuration(val)}` : ''),
    align: 'left',
    sortable: true,
  },
}

export default controls

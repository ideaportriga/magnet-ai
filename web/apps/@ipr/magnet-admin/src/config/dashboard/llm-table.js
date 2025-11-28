import { formatDuration } from '@shared/utils'
const controls = {

  name: {
    name: 'name',
    label: 'Name',
    field: 'name',
    readonly: true,
    align: 'left',
    action: 'filterLlm',
    sortable: true,
  },
  type: {
    name: 'type',
    label: 'Type',
    field: 'type',
    readonly: true,
    align: 'left',
    sortable: true,

  },
  count: {
    name: 'count',
    label: 'Total requests',
    field: 'count',
    readonly: true,
    align: 'left',
    sortable: true,
  },
  avg_total_cost: {
    name: 'avg_total_cost',
    label: 'Avg. request cost',
    field: 'avg_total_cost',
    readonly: true,
    align: 'left',
    format: (val) => `${val.toFixed(6)} $`,
    sortable: true,
  },
  total_cost: {
    name: 'total_cost',
    label: 'Total cost',
    field: 'total_cost',
    readonly: true,
    align: 'left',
    format: (val) => `${val.toFixed(6)} $`,
    sortable: true,
  },
  avg_latency: {
    name: 'avg_latency',
    label: 'Avg. request latency',
    field: 'avg_latency',
    readonly: true,
    align: 'left',
    format: (val) => `${formatDuration(val)}`,
    sortable: true,
  },
  error_rate: {
    name: 'error_rate',
    label: 'Error rate',
    field: 'error_rate',
    readonly: true,
    align: 'left',
    format: (val) => `${val.toFixed(2)}%`,
  }
  
}

export default controls

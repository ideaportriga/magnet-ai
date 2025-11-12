import { markRaw } from 'vue'
import { StatusField, TypeField, ChannelField } from './components'
import { formatDuration } from '@shared/utils'
import { formatDateTime } from '@shared/utils/dateTime'

const controls = {
  id: {
    name: 'id',
    label: 'id',
    field: 'id',
    readonly: true,
    display: false,
    ignorePatch: true,
    fromMetadata: false,
  },
  status: {
    name: 'status',
    label: 'Status',
    field: 'status',
    display: true,
    align: 'center',
    type: 'component',
    component: markRaw(StatusField),
  },
  name: {
    name: 'name',
    label: 'Tracing Target',
    field: 'name',
    display: true,
    readonly: true,
    align: 'left',
    sortable: true,
  },
  type: {
    name: 'type',
    label: 'Type',
    field: 'type',
    display: true,
    align: 'left',
    sortable: true,
    type: 'component',
    component: markRaw(TypeField),
  },
  channel: {
    name: 'channel',
    label: 'Channel',
    field: 'channel',
    display: true,
    readonly: true,
    align: 'left',
    format: (val: string) => {
      if (!val) return ''
      return val?.[0]?.toUpperCase() + val?.slice(1)
    },
    sortable: true,
    type: 'component',
    component: markRaw(ChannelField),
  },
  start_time: {
    name: 'start_time',
    label: 'Start Time',
    field: 'start_time',
    display: true,
    readonly: true,
    format: (val) => formatDateTime(val),
    align: 'left',
    sortable: true,
    sort: (a: string, b: string) => {
      const dateObjectA = new Date(a)
      const dateObjectB = new Date(b)
      return dateObjectA.getTime() - dateObjectB.getTime()
    },
    style: 'min-width: 150px; max-width: 150px;',
  },
  end_time: {
    name: 'end_time',
    label: 'End Time',
    field: 'end_time',
    display: true,
    readonly: true,
    format: (val) => formatDateTime(val),
    align: 'left',
    sortable: true,
    sort: (a: string, b: string) => {
      const dateObjectA = new Date(a)
      const dateObjectB = new Date(b)
      return dateObjectA.getTime() - dateObjectB.getTime()
    },
    style: 'min-width: 150px; max-width: 150px;',
  },
  latency: {
    name: 'latency',
    label: 'Latency',
    field: 'latency',
    display: true,
    align: 'left',
    format: formatDuration,
    sortable: true,
  },
  total_cost: {
    name: 'cost_details.total',
    label: 'Total Cost',
    field: (row: any) => row?.cost_details?.total,
    display: true,
    align: 'left',
    sortable: true,
    format: (val: number) => (val ? `$${val?.toFixed(6)}` : null),
  },
}

export default controls

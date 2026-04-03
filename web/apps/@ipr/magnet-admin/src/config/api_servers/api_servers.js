import { formatDateTime } from '@shared/utils/dateTime'
import { ChipCopy } from '@ui'
import { markRaw } from 'vue'
import { m } from '@/paraglide/messages'

const controls = {
  name: {
    name: 'name',
    label: m.common_name(),
    field: 'name',
    display: true,
    align: 'left',
    sortable: true,
    class: 'km-title',
  },
  system_name: {
    name: 'system_name',
    label: m.common_systemName(),
    field: 'system_name',
    display: true,
    align: 'left',
    sortable: true,
    type: 'component',
    component: markRaw(ChipCopy),
  },
  created_at: {
    name: 'created_at',
    label: m.common_created(),
    field: 'created_at',
    display: true,
    align: 'left',
    sortable: true,
    // type: 'Date',
    format: (val) => formatDateTime(val),
    sort: (a, b) => {
      const dateObjectA = new Date(a)
      const dateObjectB = new Date(b)
      return dateObjectA - dateObjectB
    },
  },
  updated_at: {
    name: 'updated_at',
    label: m.common_lastUpdated(),
    field: 'updated_at',
    display: true,
    align: 'left',
    sortable: true,
    // type: 'Date',
    format: (val) => formatDateTime(val),
    sort: (a, b) => {
      const dateObjectA = new Date(a)
      const dateObjectB = new Date(b)
      return dateObjectA - dateObjectB
    },
  },
}

export default controls

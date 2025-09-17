import NameDescription from '@/config/assistant-tools/component/NameDescription.vue'
import { formatDateTime } from '@shared/utils/dateTime'
import { markRaw, h } from 'vue'
import { ChipCopy } from '@ui'

const controls = {
  name: {
    name: 'name',
    label: 'Name & URL',
    field: 'name',
    display: true,
    readonly: true,
    fromMetadata: false,
    type: 'component',
    component: ({ row }) => {
      const props = {
        row: {
          name: row.name,
          description: row.url,
        },
      }
      return markRaw(h(NameDescription, props))
    },
    sortable: true,
    align: 'left',
  },
  system_name: {
    name: 'system_name',
    label: 'System name',
    field: 'system_name',
    display: true,
    sortable: true,
    align: 'left',
    type: 'component',
    component: markRaw(ChipCopy),
  },
  last_synced_at: {
    name: 'last_synced_at',
    label: 'Last synced',
    field: 'last_synced_at',
    display: true,
    readonly: true,
    format: (val) => formatDateTime(val),
    align: 'left',
    sortable: true,
    sort: (a, b) => {
      const dateObjectA = new Date(a)
      const dateObjectB = new Date(b)
      return dateObjectA - dateObjectB
    },
  },
}

export default controls

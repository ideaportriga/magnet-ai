import NameDescription from '@/config/assistant-tools/component/NameDescription.vue'
import { formatDateTime } from '@shared/utils/dateTime'
import { markRaw, h } from 'vue'

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
    align: 'left',
  },
  system_name: {
    name: 'system_name',
    label: 'System name',
    field: 'system_name',
    display: true,
    align: 'left',
  },
  last_updated: {
    name: 'last_updated',
    label: 'Last synced',
    field: 'last_updated',
    display: true,
    readonly: true,
    format: (val) => formatDateTime(val),
    align: 'left',
  },
}

export default controls

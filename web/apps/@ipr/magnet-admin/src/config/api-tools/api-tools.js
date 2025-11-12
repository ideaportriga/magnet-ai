import NameDescription from '@/config/assistant-tools/component/NameDescription.vue'
import { ChipCopy } from '@ui'
import { markRaw } from 'vue'
import { formatDateTime } from '@shared/utils/dateTime'

const controls = {
  name: {
    name: 'name',
    label: 'Name & Description',
    field: 'name',
    display: true,
    readonly: true,
    fromMetadata: false,
    type: 'component',
    component: markRaw(NameDescription),
    style: 'max-width: 300px;',
  },
  system_name: {
    name: 'system_name',
    label: 'System name',
    field: 'system_name',
    display: true,
    type: 'component',
    readonly: true,
    fromMetadata: false,
    component: markRaw(ChipCopy),
    action: 'drilldown',
  },
  id: {
    name: 'id',
    label: 'id',
    field: 'id',
    readonly: true,
    display: false,
    ignorePatch: true,
    fromMetadata: false,
  },
  api_provider: {
    name: 'api_provider',
    label: 'API Provider',
    field: 'api_provider',
    display: true,
    readonly: true,
    fromMetadata: false,
  },
  description: {
    name: 'description',
    label: 'Description',
    field: 'description',
    display: false,
    readonly: true,
    fromMetadata: false,
  },
  active_variant: {
    name: 'active_variant',
    label: 'Active Variant',
    field: 'active_variant',
    display: false,
    readonly: true,
    fromMetadata: false,
  },
  method: {
    name: 'method',
    label: 'Method',
    field: 'method',
    display: false,
    readonly: true,
    fromMetadata: false,
  },

  path: {
    name: 'path',
    label: 'Path',
    field: 'path',
    display: false,
    readonly: true,
    fromMetadata: false,
  },
  created_at: {
    name: 'created_at',
    label: 'Created',
    field: (row) => row?.['created_at'],
    display: true,
    readonly: true,
    fromMetadata: true,
    type: 'Date',
    format: (val) => formatDateTime(val),
    sort: (a, b) => {
      const dateObjectA = new Date(a)
      const dateObjectB = new Date(b)
      return dateObjectA - dateObjectB
    },
  },
  updated_at: {
    name: 'modified_at',
    label: 'Last Updated',
    field: (row) => row?.['updated_at'],
    display: true,
    readonly: true,
    fromMetadata: true,
    type: 'Date',
    format: (val) => formatDateTime(val),
    sort: (a, b) => {
      const dateObjectA = new Date(a)
      const dateObjectB = new Date(b)
      return dateObjectA - dateObjectB
    },
  },
}

export default controls

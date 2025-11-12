import { required, minLength } from '@shared/utils/validationRules'
import Check from './component/Check.vue'
import Radio from './component/Radio.vue'
import { markRaw } from 'vue'
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
  label: {
    name: 'label',
    display: true,
    label: 'Label',
    field: 'label',
    readonly: true,
    columnNumber: 0,
    fromMetadata: false,
    ignorePatch: true,
    validate: true,
    rules: [required()],
    align: 'left',
  },

  system_name: {
    name: 'system_name',
    display: false,
    label: 'System name',
    field: 'system_name',
    readonly: true,
    columnNumber: 0,
    fromMetadata: false,
    ignorePatch: true,
    validate: true,
    rules: [required()],
    align: 'left',
  },
  display_name: {
    name: 'display_name',
    display: true,
    label: 'Display name',
    field: 'display_name',
    readonly: true,
    columnNumber: 0,
    fromMetadata: false,
    ignorePatch: true,
    validate: true,
    rules: [required()],
    align: 'left',
  },

  json_mode: {
    name: 'json_mode',
    label: 'JSON Mode',
    type: 'component',
    field: 'json_mode',
    component: markRaw(Check),
    display: true,
    align: 'center',
    sortable: true,
  },
  json_schema: {
    name: 'json_schema',
    type: 'component',
    display: true,
    label: 'JSON Schema',
    field: 'json_schema',
    component: markRaw(Check),
    align: 'center',
    sortable: true,
  },
  price_input: {
    name: 'price_input',
    display: true,
    label: 'Price Input',
    subLabel: 'Per 1M tokens',
    field: 'price_input',
    readonly: true,
    columnNumber: 0,
    fromMetadata: false,
    ignorePatch: true,
    align: 'left',
    format: (val) => {
      const num = Number(val)
      return isNaN(num) ? '-' : `$${num.toFixed(2)}`
    },
  },
  price_output: {
    name: 'price_output',
    display: true,
    label: 'Price Output',
    subLabel: 'Per 1M tokens',
    field: 'price_output',
    readonly: true,
    ignorePatch: true,
    align: 'left',
    format: (val) => {
      const num = Number(val)
      return isNaN(num) ? '-' : `$${num.toFixed(2)}`
    },
  },
  price_cached: {
    name: 'price_cached',
    display: true,
    label: 'Price Cached',
    subLabel: 'Per 1M tokens',
    field: 'price_cached',
    readonly: true,
    ignorePatch: true,
    align: 'left',
    format: (val) => {
      const num = Number(val)
      return isNaN(num) ? '-' : `$${num.toFixed(2)}`
    },
  },
  is_default: {
    name: 'is_default',
    type: 'component',
    component: markRaw(Radio),
    display: true,
    label: 'Default',
    readonly: true,
    align: 'left',
  },
  type: {
    name: 'type',
    display: false,
    label: 'Type',
    field: 'type',
    readonly: true,
    fromMetadata: false,
    ignorePatch: true,
    validate: true,
    align: 'left',
  },
  is_active: {
    name: 'is_active',
    display: false,
    label: 'Active',
    field: 'is_active',
    readonly: true,
    columnNumber: 0,
    fromMetadata: false,
    ignorePatch: true,
    validate: true,
    align: 'left',
  },
  description: {
    name: 'description',
    description: 'description',
    display: false,
    label: 'description',
    field: 'description',
    readonly: true,
    columnNumber: 0,
    fromMetadata: false,
    ignorePatch: true,
    action: 'drilldown',
    validate: true,
    rules: [minLength(3, 'Model description must consist of more than 3 characters')],
    align: 'left',
  },
  resources: {
    name: 'resources',
    description: 'resources',
    display: false,
    label: 'resources',
    field: 'resources',
    readonly: true,
    columnNumber: 0,
    fromMetadata: false,
    ignorePatch: true,
    align: 'left',
  },
  created: {
    name: 'created',
    label: 'Created',
    field: (row) => row?._metadata?.['created_at'],
    type: 'Date',
    display: false,
    format: (val) => formatDateTime(val),
    ignorePatch: true,
    columnNumber: 5,
    fromMetadata: false,
    align: 'left',
    sortable: true,
    sort: (a, b) => {
      const dateObjectA = new Date(a)
      const dateObjectB = new Date(b)
      return dateObjectA - dateObjectB
    },
  },
  last_updated: {
    name: 'last_updated',
    label: 'Last updated',
    field: (row) => row?._metadata?.['modified_at'],
    display: false,
    readonly: true,
    type: 'Date',
    format: (val) => formatDateTime(val),
    ignorePatch: true,
    columnNumber: 6,
    fromMetadata: false,
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

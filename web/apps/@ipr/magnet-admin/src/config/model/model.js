import { required, minLength } from '@shared/utils/validationRules'
import Check from './component/Check.vue'
import Features from './component/Features.vue'
import TypeChip from './component/TypeChip.vue'
import { markRaw } from 'vue'
import store from '@/store'
import { formatDateTime } from '@shared/utils/dateTime'

const categoryOptions = [
  { label: 'Chat Completion', value: 'prompts' },
  { label: 'Vector Embedding', value: 'embeddings' },
  { label: 'Re-ranking', value: 're-ranking' },
]


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
  provider: {
    name: 'provider',
    display: false,
    label: 'Provider',
    field: 'provider_name',
    readonly: true,
    columnNumber: 0,
    fromMetadata: false,
    ignorePatch: true,
    validate: true,
    rules: [required()],
    align: 'left',
  },
  providerLabel: {
    name: 'providerLabel',
    display: false,
    label: 'Provider',
    field: (row) => {
      const providerSystemName = row?.provider_system_name || row?.provider_name
      const providerLabel = (store.getters['chroma/provider'].items || []).find(
        (option) => option.system_name === providerSystemName || option.id === providerSystemName
      )
      return providerLabel ? providerLabel.label : providerSystemName // Fallback to the system_name if label not found
    },
    readonly: true,
    columnNumber: 0,
    fromMetadata: false,
    ignorePatch: true,
    rules: [required()],
    align: 'left',
    sortable: true,
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
    sortable: true,
  },
  model: {
    name: 'model',
    display: true,
    label: 'Name',
    field: 'ai_model',
    readonly: true,
    columnNumber: 0,
    fromMetadata: false,
    ignorePatch: true,
    validate: true,
    rules: [required()],
    align: 'left',
    sortable: true,
  },
  type: {
    name: 'type',
    display: true,
    label: 'Type',
    field: 'type',
    type: 'component',
    component: markRaw(TypeChip),
    readonly: true,
    fromMetadata: false,
    ignorePatch: true,
    validate: true,
    align: 'left',
    sortable: true,
  },
  features: {
    name: 'features',
    label: 'Features',
    type: 'component',
    field: 'features',
    component: markRaw(Features),
    display: true,
    align: 'left',
    sortable: false,
  },

  json_mode: {
    name: 'json_mode',
    label: 'JSON Mode',
    type: 'component',
    field: 'json_mode',
    component: markRaw(Check),
    display: false,
    align: 'center',
    sortable: true,
  },
  // json_schema: {
  //   name: 'json_schema',
  //   type: 'component',
  //   display: true,
  //   label: 'JSON Schema',
  //   field: 'json_schema',
  //   component: markRaw(Check),
  //   align: 'center',
  //   sortable: true,
  // },
  tool_calling: {
    name: 'tool_calling',
    type: 'component',
    display: false,
    label: 'Tool Calling',
    field: 'tool_calling',
    component: markRaw(Check),
    align: 'center',
    sortable: true,
  },
  reasoning: {
    name: 'reasoning',
    type: 'component',
    display: false,
    label: 'Reasoning',
    field: 'reasoning',
    component: markRaw(Check),
    align: 'center',
    sortable: true,
  },
  is_default: {
    name: 'is_default',
    field: 'is_default',
    type: 'component',
    component: markRaw(Check),
    display: true,
    label: 'Default',
    readonly: true,
    align: 'center',
    sortable: true,
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
    field: (row) => row?.['created_at'],
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
    field: (row) => row?.['updated_at'],
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
export { categoryOptions }

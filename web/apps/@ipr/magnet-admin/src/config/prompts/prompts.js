import { required, minLength } from '@shared/utils/validationRules'
import NameDescription from '@/config/rag-tools/component/NameDescription.vue'
import { markRaw } from 'vue'
import { formatDateTime } from '@shared/utils/dateTime'

import { ChipCopy } from '@ui'

export const categoryOptions = [
  { value: 'rag', label: 'RAG' },
  { value: 'agent', label: 'Agent' },
  { value: 'prompt_tool', label: 'Prompt Tool' },
  { value: 'generic', label: 'Generic' },
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
  nameDescription: {
    name: 'nameDescription',
    label: 'Name',
    type: 'component',
    field: 'name',
    component: markRaw(NameDescription),
    display: true,
    sortable: true,
    style: 'max-width: 300px;',
    align: 'left',
  },
  name: {
    name: 'name',
    display: false,
    label: 'Name',
    field: 'name',
    readonly: true,
    columnNumber: 0,
    fromMetadata: false,
    ignorePatch: true,
    action: 'drilldown',
    validate: true,
    rules: [required(), minLength(3, 'Prompt template name must consist of more than 3 characters')],
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
    rules: [required(), minLength(3, 'Prompt template description must consist of more than 3 characters')],
    align: 'left',
  },
  system_name: {
    name: 'system_name',
    code: 'system_name',
    display: true,
    label: 'System name',
    field: 'system_name',
    type: 'component',
    component: markRaw(ChipCopy),
    readonly: true,
    columnNumber: 0,
    fromMetadata: false,
    ignorePatch: true,
    validate: true,
    rules: [required(), minLength(3, 'RAG Tools system name must consist of more than 3 characters')],
    align: 'left',
    classes: 'km-button-xs-text',
    sortable: true,
  },
  category: {
    name: 'category',
    code: 'category',
    display: true,
    label: 'Category',
    field: 'category',
    readonly: true,
    columnNumber: 0,
    fromMetadata: false,
    ignorePatch: true,
    validate: true,
    sortable: true,
    rules: [required()],
    align: 'left',
    format: (val) => {
      return categoryOptions.find((option) => option.value === val)?.label
    },
  },
  // modelLabel: {
  //   name: 'modelLabel',
  //   display: true,
  //   sortable: true,
  //   label: 'Model',
  //   align: 'left',
  //   field: (row) => {
  //     const activeVariantModel = row.variants?.find((el) => el?.variant === row?.active_variant)?.system_name_for_model
  //     const defaultModelLabel = (store.getters['chroma/model'].items || []).find((option) => option.is_default)?.display_name
  //     const modelLabel = (store.getters['chroma/model'].items || []).find((option) => option.system_name == activeVariantModel)?.display_name
  //     return modelLabel ? modelLabel : defaultModelLabel
  //   }
  // },
  model: {
    name: 'model',
    label: 'Model',
    field: 'model',
    readonly: true,
    display: false,
    ignorePatch: true,
    fromMetadata: false,
    sortable: true,
  },
  variants: {
    name: 'variants',
    label: 'Variants',
    display: true,
    ignorePatch: true,
    fromMetadata: false,
    field: (row) => {
      return row.variants?.length ?? 1
    },
    align: 'left',
    sortable: true,
    sort: (a, b) => {
      return a - b
    },
  },
  created: {
    name: 'created',
    label: 'Created',
    field: 'created_at',
    type: 'Date',
    display: true,
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
    field: 'updated_at',
    display: true,
    readonly: true,
    type: 'Date',
    format: (val) => {
      val = val.endsWith('Z') ? val : val + 'Z'
      const dateObject = new Date(val)
      const localeDateString = dateObject.toLocaleDateString()
      const localeTimeString = dateObject.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      return `${localeDateString} ${localeTimeString}`
    },
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

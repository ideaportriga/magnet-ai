import { required, minLength } from '@shared/utils/validationRules'
import NameDescription from './component/NameDescription.vue'
import { markRaw } from 'vue'
import { formatDateTime } from '@shared/utils/dateTime'

export const typeOptions = [
  { value: 'rag_tool', label: 'RAG' },
  { value: 'prompt_template', label: 'Prompt Template' },
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
    rules: [required(), minLength(3, 'Evaluation test set name must consist of more than 3 characters')],
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
    rules: [required(), minLength(3, 'Evaluation test set description must consist of more than 3 characters')],
    align: 'left',
  },
  system_name: {
    name: 'system_name',
    system_name: 'system_name',
    display: false,
    label: 'system_name',
    field: 'system_name',
    readonly: true,
    columnNumber: 0,
    fromMetadata: false,
    ignorePatch: true,
    validate: true,
    rules: [required(), minLength(3, 'Evaluation test set system name must consist of more than 3 characters')],
    align: 'left',
  },

  nameDescription: {
    name: 'nameDescription',
    label: 'Name',
    type: 'component',
    component: markRaw(NameDescription),
    display: true,
    sortable: true,
    align: 'left',
    style: 'max-width: 300px;',
    sort: (a, b, rowA, rowB) => {
      console.log('sort', a, b, rowA, rowB)
      return rowA.name.localeCompare(rowB.name)
    },
  },
  type: {
    name: 'type',
    code: 'type',
    display: true,
    label: 'Type',
    field: (row) => {
      const type = row.type
      const typeOption = typeOptions.find((option) => option.value === type)
      return typeOption ? typeOption.label : type // Fallback to the code if label not found
    },
    readonly: true,
    columnNumber: 0,
    fromMetadata: false,
    ignorePatch: true,
    validate: true,
    rules: [required()],
    align: 'left',
    sortable: true,
  },
  created: {
    name: 'created',
    label: 'Created',
    field: (row) => row?.['created_at'],
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
    field: (row) => row?.['updated_at'],
    display: true,
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

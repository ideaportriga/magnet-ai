import { required, minLength, validSystemName } from '@shared/utils/validationRules'
import NameDescription from './component/NameDescription.vue'
import { markRaw } from 'vue'
import { formatDateTime } from '@shared/utils/dateTime'
import { m } from '@/paraglide/messages'

export const typeOptions = [
  { value: 'rag_tool', label: m.common_rag() },
  { value: 'prompt_template', label: m.common_promptTemplate() },
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
    label: m.common_name(),
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
    label: m.common_description(),
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
    label: m.common_systemName(),
    field: 'system_name',
    readonly: true,
    columnNumber: 0,
    fromMetadata: false,
    ignorePatch: true,
    validate: true,
    rules: [required(), minLength(3, 'Evaluation test set system name must consist of more than 3 characters'), validSystemName()],
    align: 'left',
  },

  nameDescription: {
    name: 'nameDescription',
    label: m.common_name(),
    type: 'component',
    component: markRaw(NameDescription),
    display: true,
    sortable: true,
    align: 'left',
    style: 'max-width: 300px;',
    sort: (a, b, rowA, rowB) => {
      return rowA.name.localeCompare(rowB.name)
    },
  },
  type: {
    name: 'type',
    code: 'type',
    display: true,
    label: m.common_type(),
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
    label: m.common_created(),
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
    label: m.common_lastUpdated(),
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

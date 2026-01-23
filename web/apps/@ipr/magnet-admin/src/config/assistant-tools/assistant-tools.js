import { required, minLength, validSystemName } from '@shared/utils/validationRules'
import NameDescription from './component/NameDescription.vue'
import { markRaw } from 'vue'
import { formatDateTime } from '@shared/utils/dateTime'
import { ChipCopy } from '@ui'

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
    validate: true,
    rules: [required(), minLength(3, 'Assistant tool name must consist of more than 3 characters')],
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
    rules: [required(), minLength(3, 'Assistant tool description must consist of more than 3 characters')],
    align: 'left',
  },

  soureces: {
    name: 'soureces',
    code: 'soureces',
    display: false,
    label: 'soureces',
    field: 'soureces',
    readonly: true,
    columnNumber: 0,
    fromMetadata: false,
    ignorePatch: true,
    validate: true,
    rules: [required(), minLength(1, 'Assistant tool knowledge soureces must consist at least 1 source')],
    align: 'left',
  },
  nameDescription: {
    name: 'nameDescription',
    label: 'Name',
    type: 'component',
    field: 'name',
    component: markRaw(NameDescription),
    display: true,
    sortable: true,
    align: 'left',
    style: 'max-width: 300px;',
    sort: (a, b, rowA, rowB) => {
      return rowA.name.localeCompare(rowB.name)
    },
    headerClasses: 'max-w-50 ellipsis',
    classes: 'max-w-50 ellipsis',
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
    rules: [required(), minLength(3, 'RAG Tools system name must consist of more than 3 characters'), validSystemName()],

    classes: 'km-button-xs-text',
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

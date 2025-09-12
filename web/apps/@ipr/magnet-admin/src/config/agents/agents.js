import { required, minLength } from '@shared/utils/validationRules'
import NameDescription from './component/NameDescription.vue'
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
    rules: [required(), minLength(3, 'RAG Tools name must consist of more than 3 characters')],
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
    rules: [required(), minLength(3, 'RAG Tools description must consist of more than 3 characters')],
    align: 'left',
  },
  system_name: {
    name: 'system_name',
    code: 'system_name',
    display: false,
    label: 'system_name',
    field: 'system_name',
    readonly: true,
    columnNumber: 0,
    fromMetadata: false,
    ignorePatch: true,
    validate: true,
    rules: [required(), minLength(3, 'RAG Tools system name must consist of more than 3 characters')],
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
    rules: [required(), minLength(1, 'RAG Tools knowledge soureces must consist at least 1 source')],
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
    sort: (a, b, rowA, rowB) => {
      console.log('sort', a, b, rowA, rowB)
      return rowA.name.localeCompare(rowB.name)
    },
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

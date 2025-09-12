import { markRaw } from 'vue'
import NameDescription from './component/NameDescription.vue'
import NameDescriptionAPITools from './component/NameDescriptionApiTools.vue'
import Type from './component/Type.vue'
import { formatDateTime } from '@shared/utils/dateTime'
import NameSystemName from './component/NameSystemName.vue'
import TextWrap from './component/TextWrap.vue'

export const agentPagination = {
  rowsPerPage: 5,
  sortBy: 'last_updated',
  descending: true,
}

export const columnsSettings = {
  nameSystemName: {
    name: 'nameSystemName',
    label: 'Name & system name',
    type: 'component',
    field: 'name',
    component: markRaw(NameSystemName),
    display: true,
    sortable: true,
    align: 'left',
    style: 'max-width: 150px;', // Adjusted max-width to 150px
  },
  instructions: {
    name: 'description',
    label: 'LLM description',
    field: 'description',
    display: true,
    type: 'String',
    align: 'left',
    sortable: true,
    type: 'component',
    component: markRaw(TextWrap),
    style: 'flex-grow: 1;', // Allow this column to take all available space
  },
  actions: {
    name: 'actions',
    code: 'actions',
    display: true,
    label: 'Actions',
    field: 'actions',
    readonly: true,
    columnNumber: 1,
    fromMetadata: false,
    ignorePatch: true,
    align: 'left',
    style: 'max-width: 100px;', // Adjusted max-width to 100px
  },
}

export const agentTopicActionsPopupColumns = {
  nameDescription: {
    name: 'nameDescription',
    label: 'Name & Description',
    type: 'component',
    field: 'name',
    component: markRaw(NameDescription),
    display: true,
    sortable: true,
    align: 'left',
    style: 'max-width: 300px;',
  },
}

export const agentTopicActionsAPIToolsPopupColumns = {
  nameDescription: {
    name: 'nameDescription',
    label: 'Name & Description',
    type: 'component',
    field: 'name',
    component: markRaw(NameDescriptionAPITools),
    display: true,
    sortable: true,
    align: 'left',
    style: 'max-width: 300px;',
  },
}

export const agentTopicActionsColumns = {
  nameDescription: {
    name: 'nameDescription',
    label: 'Name & Description',
    type: 'component',
    field: 'name',
    component: markRaw(NameDescription),
    display: true,
    sortable: true,
    align: 'left',
    style: 'max-width: 300px;',
  },
  type: {
    name: 'type',
    display: true,
    label: 'Type',
    type: 'component',
    readonly: true,
    align: 'left',
    component: markRaw(Type),
    validate: true,
    field: (row) => {
      return row?.type || ''
    },
    sortable: true,
  },
  topic: {
    name: 'topic',
    display: true,
    label: 'Topic',
    field: 'topic',
    type: 'String',
    align: 'left',
    sortable: true,
  },
  created: {
    name: 'created',
    label: 'Created',
    field: (row) => row?.metadata?.['created_at'],
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
    field: (row) => row?.metadata?.['modified_at'],
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

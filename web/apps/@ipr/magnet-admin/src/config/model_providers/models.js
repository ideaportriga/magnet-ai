import { markRaw } from 'vue'
import { ChipCopy } from '@ui'
import Check from './component/Check.vue'

const controls = {
  name: {
    name: 'name',
    label: 'Display name',
    field: 'name',
    align: 'left',
  },
  provider: {
    name: 'provider',
    label: 'Name',
    field: 'provider',
    align: 'left',
  },
  category: {
    name: 'category',
    label: 'Category',
    field: 'category',
    align: 'left',
    type: 'component',
    component: markRaw(ChipCopy),
  },
  json_mode: {
    name: 'json_mode',
    label: 'JSON Mode',
    field: 'json_mode',
    align: 'center',
    type: 'component',
    component: markRaw(Check),
  },
  structured_output: {
    name: 'structured_output',
    label: 'Structured Output',
    field: 'structured_output',
    align: 'center',
    type: 'component',
    component: markRaw(Check),
  },
  tool_calling: {
    name: 'tool_calling',
    type: 'component',
    display: true,
    label: 'Tool Calling',
    field: 'tool_calling',
    component: markRaw(Check),
    align: 'center',
    sortable: true,
  },
  reasoning: {
    name: 'reasoning',
    type: 'component',
    display: true,
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
    label: 'Default Model',
    readonly: true,
    align: 'left',
    sortable: true,
  },
}

export default controls
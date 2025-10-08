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
    label: 'Provider name',
    field: 'provider',
    align: 'left',
  },
  type: {
    name: 'type',
    label: 'Type',
    field: 'type',
    align: 'left',
    type: 'component',
    component: markRaw(ChipCopy),
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
    label: 'Default',
    readonly: true,
    align: 'left',
    sortable: true,
  },
}

export default controls
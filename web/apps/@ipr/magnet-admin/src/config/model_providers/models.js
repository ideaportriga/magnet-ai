import { markRaw } from 'vue'
import Features from './component/Features.vue'
import Check from './component/Check.vue'

const controls = {
  display_name: {
    name: 'display_name',
    label: 'Display Name',
    field: 'display_name',
    align: 'left',
    sortable: true,
  },
  name: {
    name: 'name',
    label: 'Name',
    field: 'name',
    align: 'left',
    sortable: true,
  },
  category: {
    name: 'category',
    label: 'Type',
    field: 'category',
    align: 'left',
    sortable: true,
  },
  features: {
    name: 'features',
    label: 'Features',
    field: 'features',
    align: 'left',
    type: 'component',
    component: markRaw(Features),
    sortable: false,
  },
  is_default: {
    name: 'is_default',
    label: 'Default',
    field: 'is_default',
    align: 'center',
    type: 'component',
    component: markRaw(Check),
    readonly: true,
    sortable: true,
  },
}

export default controls

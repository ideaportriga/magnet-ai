import { markRaw } from 'vue'
import Check from './components/Check.vue'
import { m } from '@/paraglide/messages'

export const columnsSettings = {
  enabled: {
    name: 'enabled',
    label: m.common_enabled(),
    field: 'enabled',
    type: 'component',
    component: markRaw(Check),
    display: true,
    align: 'center',
    style: 'width: 80px;',
    columnNumber: 0,
  },
  name: {
    name: 'name',
    label: m.common_name(),
    field: 'name',
    display: true,
    sortable: true,
    align: 'left',
    style: 'width: 200px;',
    columnNumber: 1,
  },
  mapping: {
    name: 'mapping',
    label: m.common_mapping(),
    field: 'mapping',
    display: true,
    sortable: true,
    align: 'left',
    style: 'max-width: 150px;',
    columnNumber: 2,
  },
  description: {
    name: 'description',
    label: m.common_description(),
    field: 'description',
    display: false,
    sortable: true,
    align: 'left',
    style: 'width: 100px; overflow: hidden; text-overflow: ellipsis;',
    columnNumber: 3,
  },
}

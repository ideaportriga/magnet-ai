import NameDescription from '@/config/assistant-tools/component/NameDescription.vue'
import { ChipCopy } from '@ui'
import { markRaw } from 'vue'
import { formatDateTime } from '@shared/utils/dateTime'

const controls = {
  name: {
    name: 'name',
    label: 'Name & Description',
    field: 'name',
    display: true,
    readonly: true,
    fromMetadata: false,
    type: 'component',
    component: markRaw(NameDescription),
    style: 'max-width: 50vw;',
    align: 'left',
  },
  system_name: {
    name: 'system_name',
    label: 'System name',
    field: 'system_name',
    display: true,
    type: 'component',
    readonly: true,
    fromMetadata: false,
    component: markRaw(ChipCopy),
    action: 'drilldown',
    align: 'left',
  },
  // created_at: {
  //   name: 'created_at',
  //   label: 'Created',
  //   field: 'created_at',
  //   display: true,
  //   readonly: true,
  //   fromMetadata: true,
  //   type: 'Date',
  //   format: (val) => formatDateTime(val),
  //   sort: (a, b) => {
  //     const dateObjectA = new Date(a)
  //     const dateObjectB = new Date(b)
  //     return dateObjectA - dateObjectB
  //   },
  //   align: 'left',
  // },
  // updated_at: {
  //   name: 'modified_at',
  //   label: 'Last Updated',
  //   field: 'modified_at',
  //   display: true,
  //   readonly: true,
  //   fromMetadata: true,
  //   type: 'Date',
  //   format: (val) => formatDateTime(val),
  //   sort: (a, b) => {
  //     const dateObjectA = new Date(a)
  //     const dateObjectB = new Date(b)
  //     return dateObjectA - dateObjectB
  //   },
  //   align: 'left',
  // },
}

export default controls

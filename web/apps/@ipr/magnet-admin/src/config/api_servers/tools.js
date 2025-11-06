import NameDescription from '@/config/assistant-tools/component/NameDescription.vue'
import { ChipCopy } from '@ui'
import { markRaw } from 'vue'

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

}

export default controls

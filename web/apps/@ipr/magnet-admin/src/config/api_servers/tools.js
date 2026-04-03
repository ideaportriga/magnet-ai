import NameDescription from '@/config/assistant-tools/component/NameDescription.vue'
import { ChipCopy } from '@ui'
import { markRaw } from 'vue'
import { m } from '@/paraglide/messages'

const controls = {
  name: {
    name: 'name',
    label: m.common_nameDescription(),
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
    label: m.common_systemName(),
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

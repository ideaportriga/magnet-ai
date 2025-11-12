import { markRaw } from 'vue'
import NameDescription from './component/NameDescription.vue'

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
    align: 'left',
    style: 'white-space: nowrap; max-width: 200px; overflow: hidden; text-overflow: ellipsis;',
  },
}

export default controls

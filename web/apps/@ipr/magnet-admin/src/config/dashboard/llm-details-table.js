import { formatDateTime } from '@shared/utils/dateTime'
import { formatDuration, featureTypeToRequestType } from '@shared/utils'
import { markRaw, h } from 'vue'
import StatusField from './components/StatusField.vue'
import ChipCell from './components/ChipCell.vue'
import NameVariant from './components/NameVariant.vue'

const controls = {
  _id: {
    name: '_id',
    label: 'ID',
    field: '_id',
    readonly: true,
    align: 'left',
  },
  start_time: {
    name: 'start_time',
    label: 'Start time',
    field: 'start_time',
    readonly: true,
    align: 'left',
    format: (val) => formatDateTime(val),
    display: true,
    sort: (a, b) => {
      if (!a) return 1
      if (!b) return -1
      const dateObjectA = new Date(a)
      const dateObjectB = new Date(b)
      return dateObjectA - dateObjectB
    },
    sortable: true,
  },

  prompt_template: {
    name: 'feature_name',
    label: 'Prompt template & variant',
    display: true,
    align: 'left',
    type: 'component',
    component: ({ row }) => {
      const props = {
        row: {
          variant: row.feature_variant,
          name: row.feature_name,
        },
      }
      return markRaw(h(NameVariant, props))
    },
    sortable: true,
  },

  source: {
    name: 'source',
    label: 'Consumer info',
    field: 'source',
    display: true,
    align: 'left',
    type: 'component',
    component: ({ row }) => {
      const props = {
        row: {
          variant: row.consumer_name,
          name: row?.source,
        },
      }
      return markRaw(h(NameVariant, props))
    },
    sortable: true,
  },
  status: {
    name: 'status',
    label: 'Status',
    field: 'status',
    display: true,
    align: 'center',
    type: 'component',
    component: markRaw(StatusField),
    headerStyle: 'width: 50px;',
    sortable: true,
  },
  latency: {
    name: 'latency',
    label: 'Latency',
    field: 'latency',
    display: true,
    align: 'left',
    format: formatDuration,
    sortable: true,
  },
  cost: {
    name: 'cost',
    label: 'Cost',
    field: 'cost',
    display: true,
    align: 'left',
    format: (val) => {
      if (!val) return null
      return `${val?.toFixed(6)} $`
    },
    sortable: true,
  },
  request_type: {
    name: 'feature_type',
    label: 'Request type',
    field: (row) => featureTypeToRequestType(row?.feature_type),
    display: true,
    align: 'left',
    sortable: true,
  },
  model: {
    name: 'extra_data.model_details.display_name',
    label: 'Model',
    field: (row) => row?.extra_data?.model_details?.display_name,
    display: true,
    align: 'left',
    sortable: true,
  },
  organization: {
    name: 'x_attributes.org-id',
    label: 'Organization',
    field: (row) => row?.x_attributes?.org_id,
    display: true,
    align: 'left',
    type: 'component',
    component: markRaw(ChipCell),
    sortable: true,
  },

  // tokens: {
  //   name: 'tokens',
  //   label: 'Total Usage',
  //   display: true,
  //   align: 'left',
  //   field: (row) => row?.usage_details?.total,
  //   format: (val, row) => {
  //     if (!val) return null
  //     return `${val?.toFixed(0)} ${row?.usage_details?.input_details?.units || ''}`
  //   },
  // },
}

export default controls

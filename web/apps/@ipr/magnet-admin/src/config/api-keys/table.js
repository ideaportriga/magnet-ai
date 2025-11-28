import { formatDateTime } from '@shared/utils/dateTime'

const controls = {
  name: {
    name: 'name',
    label: 'Name',
    field: 'name',
    display: true,
  },
  value_masked: {
    name: 'value_masked',
    label: 'Key',
    field: 'value_masked',
    format: (val) => `................${val}`,
    display: true,
  },
  created_at: {
    name: 'created_at',
    label: 'Created',
    field: 'created_at',
    display: true,
    readonly: true,
    fromMetadata: true,
    type: 'Date',
    format: (val) => formatDateTime(val),
    sort: (a, b) => {
      const dateObjectA = new Date(a)
      const dateObjectB = new Date(b)
      return dateObjectA - dateObjectB
    },
    style: 'width: 200px',
  },
}

export default controls

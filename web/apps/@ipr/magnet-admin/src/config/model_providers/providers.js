import { markRaw } from 'vue'
import { ChipCopy } from '@ui'
import { formatDateTime } from '@shared/utils/dateTime'

// Format provider type for display
const formatProviderType = (type) => {
  if (!type) return '-'
  const typeLabels = {
    openai: 'OpenAI',
    azure_open_ai: 'Azure OpenAI',
    azure_ai: 'Azure AI',
    groq: 'Groq',
    oci: 'OCI',
    oci_llama: 'OCI Llama',
  }
  return typeLabels[type] || type
}

const controls = {
  name: {
    name: 'name',
    label: 'Name',
    field: 'name',
    align: 'left',
    sortable: true,
  },
  system_name: {
    name: 'system_name',
    label: 'System name',
    field: 'system_name',
    type: 'component',
    component: markRaw(ChipCopy),
    align: 'left',
    sortable: true,
  },
  type: {
    name: 'type',
    label: 'API Type',
    field: 'type',
    align: 'left',
    sortable: true,
    format: formatProviderType,
  },
  created_at: {
    name: 'created_at',
    label: 'Created',
    field: 'created_at',
    align: 'left',
    sortable: true,
    format: (val) => formatDateTime(val),
    sort: (a, b) => {
      const dateObjectA = new Date(a)
      const dateObjectB = new Date(b)
      return dateObjectA - dateObjectB
    },
  },
  updated_at: {
    name: 'updated_at',
    label: 'Last Updated',
    field: 'updated_at',
    align: 'left',
    sortable: true,
    format: (val) => formatDateTime(val),
    sort: (a, b) => {
      const dateObjectA = new Date(a)
      const dateObjectB = new Date(b)
      return dateObjectA - dateObjectB
    },
  },
}

export default controls

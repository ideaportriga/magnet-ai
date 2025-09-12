import store from '@/store'

const filter = {
  start_time: {
    label: 'Time period',
    key: 'start_time',
    type: 'timePeriod',
    default: 'P1D',
    overviewFilter: true,
  },
  feature_system_name: {
    label: 'Prompt template',
    key: 'feature_system_name',
    search: true,
    get options() {
      return store.getters.chroma.promptTemplates?.items.map((item) => ({ label: item.display_name ?? item.name, value: item.system_name }))
    },
  },
  source: {
    label: 'Consumer type',
    key: 'source',
    type: 'component',
    options: [
      { label: 'Runtime API', value: 'Runtime API' },
      { label: 'Runtime AI App', value: 'Runtime AI App' },
      { label: 'Preview', value: 'preview' },
      { label: 'Evaluation', value: 'evaluation' },
    ],
    multiple: true,
    default: ['Runtime AI App', 'Runtime API'],
    overviewFilter: true,
  },
  consumer_name: {
    label: 'Consumer name',
    key: 'consumer_name',
    get options() {
      return store.getters.llmDashboardOptions?.consumer_names?.map((name) => ({ label: name, value: name })) ?? []
    },
    search: true,
    overviewFilter: true,
  },
  status: {
    label: 'Status',
    key: 'status',
    options: [
      { label: 'Success', value: 'success' },
      { label: 'Error', value: 'error' },
    ],
  },
  feature_type: {
    label: 'Request type',
    key: 'feature_type',
    options: [
      { label: 'Embedding', value: 'embedding-api' },
      { label: 'Reranking', value: 'reranking-api' },
      { label: 'Chat Completion', value: ['chat-completion-api', 'prompt-template'] },
    ],
  },
  ['model.display_name']: {
    label: 'Model',
    key: 'model.display_name',
    search: true,
    get options() {
      return store.getters.chroma.model?.items.map((item) => ({ label: item.display_name ?? item.name, value: item.display_name ?? item.name }))
    },
  },
  ['x_attributes.org-id']: {
    label: 'Organization',
    key: 'x_attributes.org-id',
    search: true,
    get options() {
      return store.getters.llmDashboardOptions?.organizations?.map((orgId) => ({ label: orgId, value: orgId })) ?? []
    },
  },
}

export default filter

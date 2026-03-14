import store from '@/store'

const getTracingTargetOptions = (knowledgeGraphNames: string[] = []) => {
  const options = []

  options.push(...(store.getters.chroma.agents.items?.map((item) => item.name) ?? []))
  options.push(...(store.getters.chroma.collections.items?.map((item) => item.name) ?? []))
  options.push(...(store.getters.chroma.promptTemplates.items?.map((item) => item.name) ?? []))
  options.push(...(store.getters.chroma.rag_tools.items?.map((item) => item.name) ?? []))
  options.push(...(store.getters.chroma.retrieval.items?.map((item) => item.name) ?? []))
  options.push(...knowledgeGraphNames)

  return [...new Set(options.filter(Boolean))]
    .map((name) => ({ label: name, value: name }))
    .sort((a, b) => a.label.localeCompare(b.label))
}

const createTraceFilters = (knowledgeGraphNames: string[] = []) => ({
  status: {
    label: 'Status',
    key: 'status',
    options: [
      { label: 'Success', value: 'success' },
      { label: 'Error', value: 'error' },
    ],
    multiple: true,
  },
  name: {
    label: 'Tracing Target',
    key: 'name',
    options: () => getTracingTargetOptions(knowledgeGraphNames),
    multiple: true,
    overviewFilter: true,
  },
  type: {
    label: 'Type',
    key: 'type',
    type: 'component',
    options: [
      { label: 'Prompt Template', value: 'prompt-template' },
      { label: 'RAG Tool', value: 'rag' },
      { label: 'Retrieval Tool', value: 'retrieval-tool' },
      { label: 'Knowledge Source', value: 'knowledge-source' },
      { label: 'Knowledge Graph', value: 'knowledge-graph' },
      { label: 'Agent', value: 'agent' },
    ],
    multiple: true,
    overviewFilter: true,
  },
  channel: {
    label: 'Channel',
    key: 'channel',
    type: 'component',
    options: [
      { label: 'Preview', value: 'preview' },
      { label: 'Job', value: 'Job' },
      { label: 'Production', value: 'production' },
      { label: 'Evaluation', value: 'evaluation' },
    ],
    multiple: true,
    overviewFilter: true,
  },
  start_time: {
    label: 'Time Period',
    key: 'start_time',
    type: 'timePeriod',
    default: 'P1D',
    overviewFilter: true,
  },
})

export default createTraceFilters

import { getCachedItems } from '@/queries/getCachedItems'

const getTracingTargetOptions = (knowledgeGraphNames: string[] = []) => {
  const options: string[] = []

  options.push(...(getCachedItems('agents')?.map((item: any) => item.name) ?? []))
  options.push(...(getCachedItems('collections')?.map((item: any) => item.name) ?? []))
  options.push(...(getCachedItems('promptTemplates')?.map((item: any) => item.name) ?? []))
  options.push(...(getCachedItems('rag_tools')?.map((item: any) => item.name) ?? []))
  options.push(...(getCachedItems('retrieval')?.map((item: any) => item.name) ?? []))
  options.push(...knowledgeGraphNames)

  return [...new Set(options.filter(Boolean))]
    .map((name: string) => ({ label: name, value: name }))
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

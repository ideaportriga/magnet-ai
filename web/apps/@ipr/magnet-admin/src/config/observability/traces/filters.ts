import { getCachedCatalog } from '@/queries/useCatalogOptions'
import { m } from '@/paraglide/messages'

const getTracingTargetOptions = (knowledgeGraphNames: string[] = []) => {
  const options: string[] = []

  // Use catalog instead of individual entity caches
  const catalogItems = getCachedCatalog()
  const entityTypes = ['agents', 'collections', 'promptTemplates', 'rag_tools', 'retrieval']
  for (const item of catalogItems) {
    if (entityTypes.includes(item.entity_type)) {
      options.push(item.name)
    }
  }
  options.push(...knowledgeGraphNames)

  return [...new Set(options.filter(Boolean))]
    .map((name: string) => ({ label: name, value: name }))
    .sort((a, b) => a.label.localeCompare(b.label))
}

const createTraceFilters = (knowledgeGraphNames: string[] = []) => ({
  status: {
    label: m.common_status(),
    key: 'status',
    options: [
      { label: m.common_success(), value: 'success' },
      { label: m.common_error(), value: 'error' },
    ],
    multiple: true,
  },
  name: {
    label: m.trace_tracingTarget(),
    key: 'name',
    options: () => getTracingTargetOptions(knowledgeGraphNames),
    multiple: true,
    overviewFilter: true,
  },
  type: {
    label: m.common_type(),
    key: 'type',
    type: 'component',
    options: [
      { label: m.entity_promptTemplate(), value: 'prompt-template' },
      { label: m.entity_ragTool(), value: 'rag' },
      { label: m.entity_retrievalTool(), value: 'retrieval-tool' },
      { label: m.entity_knowledgeSource(), value: 'knowledge-source' },
      { label: m.entity_knowledgeGraph(), value: 'knowledge-graph' },
      { label: m.entity_agent(), value: 'agent' },
    ],
    multiple: true,
    overviewFilter: true,
  },
  channel: {
    label: m.common_channel(),
    key: 'channel',
    type: 'component',
    options: [
      { label: m.trace_channelPreview(), value: 'preview' },
      { label: m.entity_job(), value: 'Job' },
      { label: m.trace_channelProduction(), value: 'production' },
      { label: m.entity_evaluation(), value: 'evaluation' },
    ],
    multiple: true,
    overviewFilter: true,
  },
  start_time: {
    label: m.agents_timePeriod(),
    key: 'start_time',
    type: 'timePeriod',
    default: 'P1D',
    overviewFilter: true,
  },
})

export default createTraceFilters

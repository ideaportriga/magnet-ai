import type { Filter } from '../types'

type FilterObject = Record<string, unknown>

export const convertFiltersToFilterObject = (filters: Filter[] | null | undefined): FilterObject | null => {
  if (!filters || filters.length === 0) return null

  const andClauses: FilterObject[] = []

  for (const filterItem of filters) {
    const { field, conditions } = filterItem
    if (!field || !conditions?.length) continue

    const orClauses: FilterObject[] = []

    for (const condition of conditions) {
      const isEqual = condition.operator === 'equal'

      if (condition.type === 'value') {
        orClauses.push({ [field]: { [isEqual ? '$eq' : '$ne']: condition.value ?? '' } })
      } else if (condition.type === 'empty') {
        orClauses.push({ [field]: { [isEqual ? '$in' : '$nin']: [null, ''] } })
      } else if (condition.type === 'exists') {
        orClauses.push({ [field]: { $exists: isEqual } })
      }
    }

    if (orClauses.length === 0) continue
    andClauses.push(orClauses.length === 1 ? orClauses[0] : { $or: orClauses })
  }

  if (andClauses.length === 0) return null
  return andClauses.length === 1 ? andClauses[0] : { $and: andClauses }
}

export const formatDuration = (value: number) => {
  if (value == 0) return '0s'
  if (!value) return ''
  if (value >= 60000) {
    const minutes = Math.floor(value / 60000)
    const seconds = Math.floor((value % 60000) / 1000)
    return `${minutes}m ${seconds}s`
  } else {
    return `${(value / 1000).toFixed(2)}s`
  }
}

export const formatTraceType = (value: string) => {
  switch (value?.toLowerCase()) {
    case 'prompt-template':
      return 'Prompt Template'
    case 'rag':
      return 'RAG Tool'
    case 'retrieval-tool':
      return 'Retrieval Tool'
    case 'knowledge-source':
      return 'Knowledge Source'
    case 'knowledge-graph':
      return 'Knowledge Graph'
    case 'agent':
      return 'Agent'
    default:
      return value
  }
}

export const featureTypeToRequestType = (value: string) => {
  switch (value?.toLowerCase()) {
    case 'prompt-template':
    case 'chat-completion-api':
      return 'Chat Completion'
    case 'embedding-api':
      return 'Embedding'
    case 'reranking-api':
      return 'Reranking'
    default:
      return ''
  }
}

export const formatScore = (value: string | number) => {
  if (typeof value === 'string') {
    value = parseFloat(value)
  }
  return value
}

export * from './dateTime'

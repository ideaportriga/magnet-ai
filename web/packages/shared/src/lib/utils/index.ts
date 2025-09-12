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

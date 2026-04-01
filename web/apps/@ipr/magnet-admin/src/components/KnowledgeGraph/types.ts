export interface KnowledgeGraphSettings {
  indexing?: {
    embedding_model?: string
    [key: string]: unknown
  }
  retrieval_tools?: {
    exit?: {
      outputFormat?: string
      [key: string]: unknown
    }
    [key: string]: unknown
  }
  retrieval_variant?: string
  metadata?: Record<string, unknown>
  chunking?: {
    content_settings?: unknown
    [key: string]: unknown
  }
  [key: string]: unknown
}

export interface KnowledgeGraphDetails {
  id?: string
  name?: string
  system_name?: string
  description?: string
  documents_count?: number
  created_at?: string
  state?: Record<string, unknown>
  settings?: KnowledgeGraphSettings
  [key: string]: unknown
}

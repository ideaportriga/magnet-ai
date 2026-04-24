/**
 * Base entity interface — common fields shared by most entities.
 * All fields are optional to avoid blocking migration from untyped Vuex.
 */
export interface BaseEntity {
  id?: string
  name?: string
  description?: string
  system_name?: string
  created_at?: string
  updated_at?: string
  created_by?: string
  updated_by?: string
  _metadata?: Record<string, unknown>
  [key: string]: unknown
}

// --- Entity-specific interfaces ---

export interface Collection extends BaseEntity {
  category?: string
  type?: string
  source_type?: string
  chunking_strategy?: string
  chunk_size?: number
  chunk_overlap?: number
  chunk_transformation_method?: string
  chunk_usage_method?: string
  semantic_search_supported?: boolean
  support_keyword_search?: boolean
  show_in_qa?: boolean
  last_synced?: string
  metadata?: Record<string, unknown>
}

export interface Document extends BaseEntity {
  content?: string
  content_override?: string
  originalContent?: string
  metadata?: {
    title?: string
    type?: string
    source?: string
    createdTime?: string
    modifiedTime?: string
    content_override?: string
    content?: {
      retrieval?: string
      unmodified?: string
    }
    [key: string]: unknown
  }
}

export interface RagTool extends BaseEntity {
  variants?: unknown[]
  active_variant?: string | null
}

export interface RetrievalTool extends BaseEntity {
  variants?: unknown[]
  active_variant?: string | null
}

export interface PromptTemplate extends BaseEntity {
  category?: string
  model?: string
  variants?: unknown[]
  active_variant?: string | null
}

export interface AiApp extends BaseEntity {
  variants?: unknown[]
  active_variant?: string | null
  tabs?: unknown[]
}

export interface EvaluationSet extends BaseEntity {
  type?: string
  items?: unknown[]
}

export interface EvaluationJob extends BaseEntity {
  _id?: string
  status?: 'in_progress' | 'completed' | 'failed' | 'ready_for_eval' | 'eval_in_progress' | 'eval_completed'
  average_score?: number
  average_latency?: number
  average_cost?: number
  iteration_count?: number
  tool?: {
    variant_name?: string
    variant_object?: Record<string, unknown>
    [key: string]: unknown
  }
  test_set?: {
    name?: string
    [key: string]: unknown
  }
  job_start?: string
}

export interface Model extends BaseEntity {
  is_default?: boolean
  type?: string
  display_name?: string
  model?: string
}

export interface Provider extends BaseEntity {
  type?: string
}

export interface Agent extends BaseEntity {
  variants?: unknown[]
  active_variant?: string | null
  channels?: Record<string, unknown>
}

export interface AssistantTool extends BaseEntity {
  definition?: unknown
}


export interface Job extends BaseEntity {
  status?: string
  last_run?: string
  next_run?: string
  job_interval?: string
  job_type?: string
  definition?: {
    run_configuration?: {
      type?: string
      params?: Record<string, unknown>
    }
    [key: string]: unknown
  }
}

export interface McpServer extends BaseEntity {
  url?: string
  last_synced_at?: string
}

export interface ApiKey extends BaseEntity {
  value_masked?: string
  is_active?: boolean
  expires_at?: string | null
  notes?: string | null
}

export interface ApiServer extends BaseEntity {
  url?: string
}

export interface ObservabilityTrace extends BaseEntity {
  start_time?: string
  end_time?: string
  latency?: number
  status?: string
  status_message?: string
  type?: string
  channel?: string
  source?: string
  user_id?: string
  cost_details?: {
    total?: number
    [key: string]: unknown
  }
}

export interface KnowledgeGraph extends BaseEntity {
  documents_count?: number
  state?: Record<string, unknown>
  settings?: {
    indexing?: { embedding_model?: string; [key: string]: unknown }
    retrieval_tools?: { exit?: { outputFormat?: string; [key: string]: unknown }; [key: string]: unknown }
    retrieval_variant?: string
    metadata?: Record<string, unknown>
    chunking?: { content_settings?: unknown; [key: string]: unknown }
    [key: string]: unknown
  }
}

export interface Plugin extends BaseEntity {
  source_type?: string
  plugin_type?: string
}

export interface StoredFile extends BaseEntity {
  filename?: string
  content_type?: string
  size?: number
  backend_key?: string
  entity_type?: string
  entity_id?: string
  expires_at?: string
}

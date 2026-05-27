export type ToolCategory = 'filter' | 'retrieval' | 'exit'

export interface Tool {
  id: string
  name: string
  label: string
  description: string
  category: ToolCategory
  enabled: boolean
  isStub?: boolean
  ui?: {
    previewExecutionFlowColor?: string
  }

  // Filter/Retrieval specific
  searchControl?: string
  scopeControl?: string
  searchMethod?: string
  rrfK?: number
  scoreThreshold?: number
  limit?: number
  candidatePoolSize?: number
  keywordVariants?: number
  vectorVariants?: number
  promptTemplateName?: string
  metadataMergeStrategy?: 'merge_and' | 'merge_or' | 'agent_priority' | 'caller_priority'

  // Exit specific
  strategy?: string
  maxIterations?: number
  additionalOutputInstructions?: string
  outputFormat?: 'plain' | 'markdown' | 'html'
  sourceAttribution?: string
  answerMode?: 'answer_only' | 'sources_only' | 'answer_with_sources'
}

export const tools: Tool[] = [
  {
    id: 'findDocumentsByMetadata',
    name: 'findDocumentsByMetadata',
    label: 'Document Metadata Search',
    description: 'Filter documents by their metadata fields',
    category: 'filter',
    searchControl: 'agent',
    metadataMergeStrategy: 'merge_and',
    enabled: true,
    ui: {
      previewExecutionFlowColor: 'orange',
    },
  },
  {
    id: 'findDocumentsBySummary',
    name: 'findDocumentsBySummarySimilarity',
    label: 'Document Summary Search',
    description: 'Find documents by summary similarity',
    category: 'filter',
    scopeControl: 'configuration',
    searchMethod: 'hybrid',
    rrfK: 60,
    scoreThreshold: 0,
    limit: 5,
    enabled: true,
    ui: {
      previewExecutionFlowColor: 'purple',
    },
  },
  {
    id: 'findDocumentsByEntity',
    name: 'findDocumentsByEntitySimilarity',
    label: 'Document Entity Search',
    description: '',
    category: 'filter',
    searchControl: 'configuration',
    scopeControl: 'configuration',
    searchMethod: 'hybrid',
    rrfK: 60,
    scoreThreshold: 0,
    limit: 5,
    enabled: false,
    isStub: true, // Coming Soon
    ui: {
      previewExecutionFlowColor: 'cyan',
    },
  },
  {
    id: 'retrieveChunks',
    name: 'retrieveChunks',
    label: 'Chunk Retrieval',
    description:
      "Searches the document corpus for passages relevant to an information need. You don't need to think about retrieval mechanics - just describe what you're looking for.",
    category: 'retrieval',
    scopeControl: 'configuration',
    searchMethod: 'hybrid',
    rrfK: 60,
    scoreThreshold: 0,
    limit: 5,
    candidatePoolSize: 30,
    keywordVariants: 1,
    vectorVariants: 1,
    promptTemplateName: 'KG_CHUNK_QUERY_REFORMULATION',
    enabled: true,
    ui: {
      previewExecutionFlowColor: 'indigo',
    },
  },
  {
    id: 'exit',
    name: 'exit',
    label: 'Exit & Respond',
    description: 'Exit the tool call loop',
    category: 'exit',
    enabled: true,
    strategy: 'confidence',
    maxIterations: 5,
    additionalOutputInstructions: '',
    outputFormat: 'markdown',
    sourceAttribution: 'all',
    answerMode: 'answer_with_sources',
    ui: {
      previewExecutionFlowColor: 'teal',
    },
  },
]

export const searchMethodOptions = [
  {
    label: 'Vector',
    value: 'vector',
    description: 'Semantic similarity search using embeddings. Best for meaning-based queries where exact wording may differ.',
  },
  {
    label: 'Full Text',
    value: 'full_text',
    description: 'Full-text search using tsvector indexing. Fast exact and stemmed word matching with language-aware tokenization.',
  },
  {
    label: 'Full Text + Fuzzy',
    value: 'keyword',
    description: 'Combines full-text search with trigram fuzzy matching to catch typos and partial words. Uses RRF to merge results.',
  },
  {
    label: 'Hybrid (Vector + Full Text + Fuzzy)',
    value: 'hybrid',
    description: 'Runs vector, full-text, and fuzzy searches in parallel and fuses rankings with RRF. Broadest recall at a higher compute cost.',
  },
]

export interface ToolDefinition {
  name: string
  description: string
  enabled: boolean
}

export interface PromptSections {
  persona: string
  instructions: string
  additionalOutputInstructions: string
}

export interface RetrievalConfig {
  promptSections: PromptSections
  temperature: number
  topP: number
  model?: string
  examples: RetrievalExample[]
  enabledTools: ToolDefinition[]
}

export interface PromptTemplateVariant {
  variant: string
  text: string
  temperature: number
  topP: number
  description?: string
  system_name_for_model?: string
  retrieve?: {
    collection_system_names: string[]
  }
  display_name?: string
}

export interface PromptTemplate {
  id?: string
  name: string
  system_name: string
  description?: string
  active_variant: string
  variants: PromptTemplateVariant[]
}

export interface ValidationError {
  type: 'missing_section' | 'invalid_section' | 'parse_error' | 'incompatible' | 'not_found'
  message: string
  section?: string
  details?: string
}

export interface ConversionResult<T> {
  success: boolean
  data?: T
  errors: ValidationError[]
  warnings: string[]
}

export interface RetrievalExample {
  id: string
  title: string
  input: string
  output: string
}

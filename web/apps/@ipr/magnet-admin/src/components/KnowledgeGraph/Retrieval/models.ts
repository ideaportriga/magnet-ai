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
  hybridWeight?: number
  scoreThreshold?: number
  limit?: number

  // Exit specific
  strategy?: string
  maxIterations?: number
  additionalOutputInstructions?: string
  outputFormat?: 'plain' | 'markdown'
  sourceAttribution?: string
  answerMode?: 'answer_only' | 'sources_only' | 'answer_with_sources'
}

export const tools: Tool[] = [
  {
    id: 'findDocumentsByMetadata',
    name: 'findDocumentsByMetadata',
    label: 'Document Metadata Search',
    description: '',
    category: 'filter',
    searchControl: 'configuration',
    scopeControl: 'configuration',
    searchMethod: 'vector',
    hybridWeight: 0,
    scoreThreshold: 0,
    limit: 10,
    enabled: false,
    isStub: true, // Coming Soon
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
    searchControl: 'configuration',
    scopeControl: 'configuration',
    searchMethod: 'vector',
    hybridWeight: 0.5,
    scoreThreshold: 0.7,
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
    searchMethod: 'vector',
    hybridWeight: 0.5,
    scoreThreshold: 0.7,
    limit: 5,
    enabled: false,
    isStub: true, // Coming Soon
    ui: {
      previewExecutionFlowColor: 'cyan',
    },
  },
  {
    id: 'findChunksBySimilarity',
    name: 'findChunksBySimilarity',
    label: 'Chunk Similarity Search',
    description: 'Find chunks by similarity',
    category: 'retrieval',
    searchControl: 'configuration',
    scopeControl: 'configuration',
    searchMethod: 'vector',
    hybridWeight: 0.5,
    scoreThreshold: 0.7,
    limit: 5,
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
  { label: 'Vector', value: 'vector' },
  { label: 'Keyword', value: 'keyword' },
  { label: 'Hybrid (Vector + Keyword)', value: 'hybrid' },
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
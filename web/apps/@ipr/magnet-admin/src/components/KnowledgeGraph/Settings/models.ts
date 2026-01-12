export interface ContentConfigRow {
  name: string
  glob_pattern: string
  enabled: boolean
  source_ids?: string[]
  chunker?: {
    strategy?: string
  }
  reader?: {
    name?: string
  }
}

export const readerOptions = [
  { label: 'Plain Text Reader', value: 'plain_text' },
  { label: 'PDF Reader', value: 'pdf' },
]

export const chunkingStrategyOptions = [
  {
    label: 'None',
    value: 'none',
    description: 'No chunking; entire content is treated as a single chunk. If content is larger than chunk max size, it will be truncated.',
  },
  {
    label: 'Recursive Splitting',
    value: 'recursive_character_text_splitting',
    description:
      "Deterministic splitter, recursively applies separators until chunk size is reached. Heavily inspired by LangChain's RecursiveCharacterTextSplitter.",
  },
  {
    label: 'LLM-Based Chunking',
    value: 'llm',
    description: 'Uses LLM to infer semantically coherent chunk boundaries. Best for complex, unstructured text.',
  },
]

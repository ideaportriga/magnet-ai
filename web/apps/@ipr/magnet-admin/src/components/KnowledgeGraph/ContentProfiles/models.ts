import { getSourceTypeName, type SourceRow } from '../Sources/models'

export interface ContentConfigRow {
  name: string
  glob_pattern: string
  enabled: boolean
  source_ids?: string[]
  source_types?: string[]
  _virtual_profile?: string
  chunker?: {
    strategy?: string
    options?: Record<string, any>
  }
  reader?: {
    name?: string
    options?: Record<string, any>
  }
}

export const FLUID_TOPICS_SOURCE_TYPE = 'fluid_topics'
export const FLUID_TOPICS_NATIVE_PROFILE_NAME = 'Fluid Topics Native Format'
export const FLUID_TOPICS_STRUCTURED_READER = 'fluid_topics_structured_documents'
export const FLUID_TOPICS_STRUCTURED_READER_LABEL = 'Fluid Topics Structured Document Reader'
export const FLUID_TOPICS_STRUCTURED_AUTO_MANAGED_KEY = '_auto_managed_profile'
export const FLUID_TOPICS_STRUCTURED_AUTO_MANAGED_VALUE = FLUID_TOPICS_STRUCTURED_READER
export const SHAREPOINT_SOURCE_TYPE = 'sharepoint'
export const SHAREPOINT_PAGE_READER = 'sharepoint_page'
export const SHAREPOINT_PAGE_READER_LABEL = 'SharePoint Page Reader'
export const SHAREPOINT_PAGE_PROMPT_TEMPLATE_SYSTEM_NAME = 'SHAREPOINT_PAGE_CHUNKING'
export const VIRTUAL_FALLBACK_PROFILE_NAME = '<default>'
export const VIRTUAL_FALLBACK_PROFILE_KEY = '_virtual_profile'
export const VIRTUAL_FALLBACK_PROFILE_VALUE = 'fallback_plain_text'

export const KREUZBERG_READER = 'kreuzberg'
export const KREUZBERG_READER_LABEL = 'Kreuzberg'
export const LITEPARSE_READER = 'liteparse'
export const LITEPARSE_READER_LABEL = 'LiteParse'
export const SOURCE_METADATA_READER = 'source_metadata'
export const SOURCE_METADATA_READER_LABEL = 'Metadata Reader'

export const readerOptions = [
  { label: 'Plain Text Reader', value: 'plain_text' },
  { label: 'PyPDF', value: 'pdf' },
  { label: KREUZBERG_READER_LABEL, value: KREUZBERG_READER },
  { label: LITEPARSE_READER_LABEL, value: LITEPARSE_READER },
  { label: SHAREPOINT_PAGE_READER_LABEL, value: SHAREPOINT_PAGE_READER },
  {
    label: FLUID_TOPICS_STRUCTURED_READER_LABEL,
    value: FLUID_TOPICS_STRUCTURED_READER,
  },
  {
    label: SOURCE_METADATA_READER_LABEL,
    value: SOURCE_METADATA_READER,
  },
]

export const selectableReaderOptions = readerOptions.filter((option) => option.value !== FLUID_TOPICS_STRUCTURED_READER)

type ContentConfigLike = {
  name?: string
  _virtual_profile?: string
  glob_pattern?: string
  source_ids?: string[]
  source_types?: string[]
  reader?: {
    name?: string
    options?: Record<string, any>
  }
}

export const isFluidTopicsStructuredReader = (readerName?: string) => readerName === FLUID_TOPICS_STRUCTURED_READER

export const hasReservedFluidTopicsNativeProfileName = (profileName?: string) =>
  String(profileName || '')
    .trim()
    .toLowerCase() === FLUID_TOPICS_NATIVE_PROFILE_NAME.toLowerCase()

export const hasReservedVirtualFallbackProfileName = (profileName?: string) =>
  String(profileName || '')
    .trim()
    .toLowerCase() === VIRTUAL_FALLBACK_PROFILE_NAME.toLowerCase()

export const isLockedFluidTopicsNativeProfile = (config?: ContentConfigLike) =>
  isFluidTopicsStructuredReader(config?.reader?.name) || hasReservedFluidTopicsNativeProfileName(config?.name)

export const isVirtualFallbackContentProfile = (config?: ContentConfigLike) =>
  config?.[VIRTUAL_FALLBACK_PROFILE_KEY] === VIRTUAL_FALLBACK_PROFILE_VALUE || hasReservedVirtualFallbackProfileName(config?.name)

export const isProtectedContentProfile = (config?: ContentConfigLike) =>
  isLockedFluidTopicsNativeProfile(config) || isVirtualFallbackContentProfile(config)

export const isAutoManagedFluidTopicsStructuredProfile = (config?: ContentConfigLike) =>
  isFluidTopicsStructuredReader(config?.reader?.name) &&
  config?.reader?.options?.[FLUID_TOPICS_STRUCTURED_AUTO_MANAGED_KEY] === FLUID_TOPICS_STRUCTURED_AUTO_MANAGED_VALUE

const ALL_SOURCES_KEY = '__ALL__'
const NONE_SELECTED_KEY = '__NONE__'
const GROUP_KEY_PREFIX = '__GROUP__'

const normalizeProfileName = (profileName?: string) =>
  String(profileName || '')
    .trim()
    .toLowerCase()

export const hasDuplicateContentProfileName = (profileName?: string, configs: ContentConfigLike[] = [], currentProfileName?: string) => {
  const normalizedName = normalizeProfileName(profileName)
  if (!normalizedName) {
    return false
  }

  const normalizedCurrentName = normalizeProfileName(currentProfileName)
  const matches = configs.filter((config) => normalizeProfileName(config?.name) === normalizedName).length

  if (!normalizedCurrentName || normalizedCurrentName !== normalizedName) {
    return matches > 0
  }

  return matches > 1
}

const getSourceSelectorLabel = (selector: string, sources: SourceRow[]) => {
  if (selector.startsWith(GROUP_KEY_PREFIX)) {
    const sourceType = selector.slice(GROUP_KEY_PREFIX.length)
    return sourceType === 'upload' ? 'manual uploads' : `any ${getSourceTypeName(sourceType)} source`
  }

  return sources.find((source) => source.id === selector)?.name || null
}

const getContentProfileSourceLabel = (sourceIds: string[] | undefined, sources: SourceRow[]) => {
  const selectors = Array.isArray(sourceIds) ? sourceIds.filter(Boolean) : []

  if (selectors.length === 0 || selectors.includes(ALL_SOURCES_KEY)) {
    return 'any source'
  }

  if (selectors.includes(NONE_SELECTED_KEY)) {
    return 'no source'
  }

  const labels = selectors.map((selector) => getSourceSelectorLabel(selector, sources)).filter((label): label is string => Boolean(label))

  if (labels.length === 0) {
    return selectors.length === 1 ? 'selected source' : `${selectors.length} selected sources`
  }

  if (labels.length === 1) {
    return labels[0]
  }

  return `${labels.length} sources`
}

export const getContentMatchingSentence = (config?: ContentConfigLike, sources: SourceRow[] = []) => {
  if (!config) {
    return '-'
  }

  if (isVirtualFallbackContentProfile(config)) {
    return 'Used only when no other content profile matches.'
  }

  if (isLockedFluidTopicsNativeProfile(config)) {
    return 'Applies to all Fluid Topics sources.'
  }

  const sourceLabel = getContentProfileSourceLabel(config.source_ids, sources)
  if (sourceLabel === 'no source') {
    return 'Matches no content because no source is selected.'
  }

  const globPattern = String(config.glob_pattern || '').trim()
  const patternLabel = globPattern ? `files matching "${globPattern}"` : 'any file'
  return `Applies to ${patternLabel} from ${sourceLabel}.`
}

export const chunkContentTypeOptions = [
  { label: 'Plain Text', value: 'plain_text' },
  { label: 'Markdown', value: 'markdown' },
  { label: 'HTML', value: 'html' },
]

export const chunkingStrategyOptions = [
  {
    label: 'None',
    value: 'none',
    description: 'No chunking; entire content is treated as a single chunk. If content is larger than chunk max size, it will be truncated.',
  },
  {
    label: "LangChain's RecursiveCharacterTextSplitter",
    value: 'recursive_character_text_splitting',
    description: 'Deterministic splitter, recursively applies separators until chunk size is reached.',
  },
  {
    label: 'LLM-Based Chunking',
    value: 'llm',
    description: 'Uses LLM to infer semantically coherent chunk boundaries. Best for complex, unstructured text.',
  },
  {
    label: "Kreuzberg's Markdown Splitter",
    value: 'kreuzberg',
    description: 'Markdown-aware deterministic splitter powered by Kreuzberg.',
  },
]

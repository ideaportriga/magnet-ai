/**
 * Metadata management models for Knowledge Graph
 */

// Metadata value types
export type MetadataValueType = 'string' | 'number' | 'boolean' | 'date' | 'array' | 'object'

// Origin of metadata - where it came from
export type MetadataOrigin = 'file' | 'llm' | 'source'

export const MetadataOriginLabels: Record<MetadataOrigin, string> = {
  file: 'File',
  llm: 'Smart Extraction',
  source: 'Source Metadata',
}

export const MetadataOriginColors: Record<MetadataOrigin, string> = {
  file: 'teal-2',
  llm: 'purple-2',
  source: 'indigo-2',
}

export const MetadataOriginTextColors: Record<MetadataOrigin, string> = {
  file: 'teal-9',
  llm: 'purple-9',
  source: 'indigo-9',
}

// Value type options for select
export const ValueTypeOptions = [
  { label: 'Text', value: 'string', icon: 'text_fields' },
  { label: 'Number', value: 'number', icon: 'tag' },
  { label: 'Boolean', value: 'boolean', icon: 'toggle_on' },
  { label: 'Date', value: 'date', icon: 'calendar_today' },
]

// Allowed value with optional LLM hint
export interface AllowedValue {
  value: string
  hint?: string
}

/**
 * Metadata value resolution / fallback chain (per source).
 *
 * This lets admins define where a schema field should be populated from, in what order:
 * - source: metadata provided by the ingestion source
 * - file: native document metadata
 * - llm: extracted by LLM
 * - constant: a user-defined constant (terminal step)
 */
export type MetadataFieldValueSourceKind = 'file' | 'llm' | 'source' | 'constant'

export interface MetadataFieldValueSourceStep {
  kind: MetadataFieldValueSourceKind
  /**
   * Discovered metadata field name to read from for the given origin.
   * Required for kind in: file | llm | source
   */
  field_name?: string
  /**
   * Constant values for kind=constant (terminal).
   * Use either constant_value (single) or constant_values (multi).
   */
  constant_value?: string
  constant_values?: string[]
}

export interface MetadataFieldSourceValueResolution {
  source_id: string
  /**
   * Ordered chain of sources to try. The first non-empty value wins.
   * Note: kind=constant should be last.
   */
  chain: MetadataFieldValueSourceStep[]
}

// Metadata field definition - user-defined schema
export interface MetadataFieldDefinition {
  id: string
  name: string
  display_name?: string
  description: string
  /**
   * Per-source value resolution chain.
   */
  source_value_resolution?: MetadataFieldSourceValueResolution[]
}

// Discovered metadata field - auto-detected from data
export interface DiscoveredMetadataField {
  name: string
  sample_values: string[]
  value_count: number
  origin: MetadataOrigin | null
  inferred_type: MetadataValueType
  is_defined: boolean
}

// Aggregated metadata value for display
export interface MetadataValueAggregation {
  field_name: string
  value: string
  count: number
  sources: string[]
}

// Metadata extraction settings
export type MetadataExtractionApproach = 'disabled' | 'chunks' | 'document'

export interface MetadataExtractionSettings {
  /**
   * Legacy toggle (pre-approach UI). Kept for backward compatibility with persisted configs.
   * Prefer `approach`.
   */
  enabled?: boolean

  /**
   * Extraction scope / strategy.
   * - disabled: do not run AI extraction
   * - chunks: extract from already-produced chunks
   * - document: extract from whole document (may segment large docs)
   */
  approach?: MetadataExtractionApproach

  /**
   * Prompt template system name (preferred).
   * This is the identifier used by the prompt templates service.
   */
  prompt_template_system_name?: string

  /**
   * Preview prompt template system name.
   * Used to preview extraction results before full extraction.
   */
  preview_prompt_template_system_name?: string

  /**
   * Legacy prompt storage (raw template text or legacy key).
   * Kept to avoid breaking older persisted configs.
   */
  prompt_template?: string

  /**
   * Document segmentation (used when approach=document).
   * - segment_size: max chars per segment
   * - segment_overlap: overlap ratio 0..0.9
   */
  segment_size?: number
  segment_overlap?: number

  model_system_name?: string
  fields_to_extract?: string[]
  auto_discover?: boolean
}

// Lightweight source link info
export interface SourceLink {
  id: string
  name: string
  type: string
}

// Discovered metadata field definition
export interface MetadataDiscoveredField {
  id: string
  name: string
  description: string
  value_type: MetadataValueType
  origin: MetadataOrigin | null
  source: SourceLink | null
  is_defined: boolean
  sample_values: string[]
}

// Smart extraction field definition
export interface MetadataExtractedField {
  id: string
  name: string
  value_type: MetadataValueType
  is_multiple: boolean
  allowed_values?: AllowedValue[]
  llm_extraction_hint?: string
  sample_values?: string[]
  value_count?: number
  created_at?: string
  updated_at?: string
}

// Default extraction prompt template
export const DEFAULT_EXTRACTION_PROMPT = `Extract metadata from the following document content.

Analyze the document and identify the following information if present:
- Title or document name
- Author or creator
- Creation date
- Document type or category
- Keywords or tags
- Language
- Any other relevant properties

Return the extracted metadata as a JSON object with appropriate field names.
Only include fields that have values found in the document.

Document content:
{content}`

// Preset field definition including both schema and smart extraction properties
export interface PresetFieldDefinition {
  // Schema field properties
  name: string
  display_name: string
  description: string
  // Smart extraction properties
  value_type: MetadataValueType
  is_multiple?: boolean
  allowed_values?: AllowedValue[]
  llm_extraction_hint?: string
}

// Preset schema fields for common metadata with smart extraction configuration
export const PRESET_FIELDS: PresetFieldDefinition[] = [
  {
    name: 'author',
    display_name: 'Author',
    description: 'The creator or author of the document',
    value_type: 'string',
    is_multiple: true,
    llm_extraction_hint: 'Extract the name(s) of the author(s) or creator(s) of this document. Look for bylines, credits, or author attribution.',
  },
  {
    name: 'language_2l',
    display_name: 'Language (ISO 639-1)',
    description: 'Language(s) of the document using ISO 639-1 two-letter codes',
    value_type: 'string',
    is_multiple: false,
    allowed_values: [
      { value: 'en', hint: 'English' },
      { value: 'de', hint: 'German' },
      { value: 'fr', hint: 'French' },
      { value: 'es', hint: 'Spanish' },
      { value: 'it', hint: 'Italian' },
      { value: 'pt', hint: 'Portuguese' },
      { value: 'nl', hint: 'Dutch' },
      { value: 'pl', hint: 'Polish' },
      { value: 'ru', hint: 'Russian' },
      { value: 'ja', hint: 'Japanese' },
      { value: 'zh', hint: 'Chinese' },
      { value: 'ko', hint: 'Korean' },
    ],
    llm_extraction_hint:
      'Identify the primary language of this document. Return the ISO 639-1 two-letter language code (e.g., "en" for English, "de" for German).',
  },
  {
    name: 'language_3l',
    display_name: 'Language (ISO 639-2)',
    description: 'Language(s) of the document using ISO 639-2 three-letter codes',
    value_type: 'string',
    is_multiple: false,
    allowed_values: [
      { value: 'eng', hint: 'English' },
      { value: 'deu', hint: 'German' },
      { value: 'fra', hint: 'French' },
      { value: 'spa', hint: 'Spanish' },
      { value: 'ita', hint: 'Italian' },
      { value: 'por', hint: 'Portuguese' },
      { value: 'nld', hint: 'Dutch' },
      { value: 'pol', hint: 'Polish' },
      { value: 'rus', hint: 'Russian' },
      { value: 'jpn', hint: 'Japanese' },
      { value: 'zho', hint: 'Chinese' },
      { value: 'kor', hint: 'Korean' },
    ],
    llm_extraction_hint:
      'Identify the primary language of this document. Return the ISO 639-2 three-letter language code (e.g., "eng" for English, "deu" for German).',
  },
  {
    name: 'document_type',
    display_name: 'Document Type',
    description: 'Type of document (manual, guide, article, etc.)',
    value_type: 'string',
    is_multiple: false,
    allowed_values: [
      { value: 'manual', hint: 'User or technical manual' },
      { value: 'guide', hint: 'How-to guide or tutorial' },
      { value: 'article', hint: 'Article or blog post' },
      { value: 'specification', hint: 'Technical specification' },
      { value: 'report', hint: 'Report or analysis' },
      { value: 'policy', hint: 'Policy or procedure document' },
      { value: 'faq', hint: 'Frequently asked questions' },
      { value: 'release_notes', hint: 'Release notes or changelog' },
    ],
    llm_extraction_hint: 'Determine the type or category of this document based on its structure and content.',
  },
  {
    name: 'version',
    display_name: 'Version',
    description: 'Document version number',
    value_type: 'string',
    is_multiple: false,
    llm_extraction_hint: 'Extract the version number or revision of this document if mentioned (e.g., "1.0", "2.3.1", "Rev A").',
  },
  {
    name: 'created_date',
    display_name: 'Created Date',
    description: 'When the document was originally created',
    value_type: 'date',
    is_multiple: false,
    llm_extraction_hint: 'Extract the creation date or publication date of this document. Return in ISO 8601 format (YYYY-MM-DD) if possible.',
  },
]

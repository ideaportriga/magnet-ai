/**
 * Metadata management models for Knowledge Graph
 */

// Metadata value types
export type MetadataValueType = 'string' | 'number' | 'boolean' | 'date' | 'array' | 'object'

// Origin of metadata - where it came from
export type MetadataOrigin = 'static' | 'document' | 'llm' | 'system'

export const MetadataOriginLabels: Record<MetadataOrigin, string> = {
  static: 'Source Config',
  document: 'Document Native',
  llm: 'LLM Extracted',
  system: 'System',
}

export const MetadataOriginColors: Record<MetadataOrigin, string> = {
  static: 'blue-2',
  document: 'teal-2',
  llm: 'purple-2',
  system: 'grey-3',
}

export const MetadataOriginTextColors: Record<MetadataOrigin, string> = {
  static: 'blue-9',
  document: 'teal-9',
  llm: 'purple-9',
  system: 'grey-8',
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

// Metadata field definition - user-defined schema
export interface MetadataFieldDefinition {
  id: string
  name: string
  display_name?: string
  description: string
  value_type: MetadataValueType
  is_multiple: boolean
  is_required: boolean
  allowed_values?: AllowedValue[]
  default_value?: string
  default_values?: string[]
  llm_extraction_hint?: string
  created_at?: string
  updated_at?: string
}

// Discovered metadata field - auto-detected from data
export interface DiscoveredMetadataField {
  name: string
  sample_values: string[]
  value_count: number
  origins: MetadataOrigin[]
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
export interface MetadataExtractionSettings {
  enabled: boolean
  prompt_template: string
  model_system_name?: string
  fields_to_extract?: string[]
  auto_discover: boolean
}

// Combined view of defined and discovered metadata
export interface MetadataFieldRow {
  id: string
  name: string
  display_name?: string
  description: string
  value_type: MetadataValueType
  origins: MetadataOrigin[]
  is_defined: boolean
  sample_values: string[]
  allowed_values?: AllowedValue[]
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

// Preset field definitions for common metadata
export const PRESET_FIELDS: Partial<MetadataFieldDefinition>[] = [
  {
    name: 'author',
    display_name: 'Author',
    description: 'The creator or author of the document',
    value_type: 'string',
    is_multiple: false,
    llm_extraction_hint: `Extract the author or creator name from the document.
Look for: bylines, "Written by", "Author:", signature blocks, or document metadata.
Return the full name if available.`,
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
      { value: 'zh', hint: 'Chinese' },
      { value: 'ja', hint: 'Japanese' },
      { value: 'ko', hint: 'Korean' },
      { value: 'ar', hint: 'Arabic' },
      { value: 'hi', hint: 'Hindi' },
      { value: 'sv', hint: 'Swedish' },
      { value: 'da', hint: 'Danish' },
      { value: 'no', hint: 'Norwegian' },
      { value: 'fi', hint: 'Finnish' },
      { value: 'cs', hint: 'Czech' },
      { value: 'hu', hint: 'Hungarian' },
      { value: 'ro', hint: 'Romanian' },
      { value: 'tr', hint: 'Turkish' },
      { value: 'th', hint: 'Thai' },
      { value: 'vi', hint: 'Vietnamese' },
      { value: 'id', hint: 'Indonesian' },
      { value: 'he', hint: 'Hebrew' },
      { value: 'uk', hint: 'Ukrainian' },
      { value: 'el', hint: 'Greek' },
      { value: 'bg', hint: 'Bulgarian' },
      { value: 'hr', hint: 'Croatian' },
      { value: 'sk', hint: 'Slovak' },
      { value: 'sl', hint: 'Slovenian' },
      { value: 'sr', hint: 'Serbian' },
      { value: 'ca', hint: 'Catalan' },
      { value: 'eu', hint: 'Basque' },
    ],
    llm_extraction_hint: `Detect the primary language of the document content.
Use the ISO 639-1 two-letter code from the allowed values: {values}.
Analyze the text and return one of the allowed values.`,
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
      { value: 'zho', hint: 'Chinese' },
      { value: 'jpn', hint: 'Japanese' },
      { value: 'kor', hint: 'Korean' },
      { value: 'ara', hint: 'Arabic' },
      { value: 'hin', hint: 'Hindi' },
      { value: 'swe', hint: 'Swedish' },
      { value: 'dan', hint: 'Danish' },
      { value: 'nor', hint: 'Norwegian' },
      { value: 'fin', hint: 'Finnish' },
      { value: 'ces', hint: 'Czech' },
      { value: 'hun', hint: 'Hungarian' },
      { value: 'ron', hint: 'Romanian' },
      { value: 'tur', hint: 'Turkish' },
      { value: 'tha', hint: 'Thai' },
      { value: 'vie', hint: 'Vietnamese' },
      { value: 'ind', hint: 'Indonesian' },
      { value: 'heb', hint: 'Hebrew' },
      { value: 'ukr', hint: 'Ukrainian' },
      { value: 'ell', hint: 'Greek' },
      { value: 'bul', hint: 'Bulgarian' },
      { value: 'hrv', hint: 'Croatian' },
      { value: 'slk', hint: 'Slovak' },
      { value: 'slv', hint: 'Slovenian' },
      { value: 'srp', hint: 'Serbian' },
      { value: 'cat', hint: 'Catalan' },
      { value: 'eus', hint: 'Basque' },
      { value: 'lat', hint: 'Latin' },
      { value: 'sqi', hint: 'Albanian' },
      { value: 'est', hint: 'Estonian' },
      { value: 'lav', hint: 'Latvian' },
      { value: 'lit', hint: 'Lithuanian' },
      { value: 'mlt', hint: 'Maltese' },
      { value: 'gle', hint: 'Irish' },
      { value: 'cym', hint: 'Welsh' },
      { value: 'bre', hint: 'Breton' },
    ],
    llm_extraction_hint: `Detect the primary language of the document content.
Use the ISO 639-2 three-letter code from the allowed values: {values}.
Analyze the text and return one of the allowed values.`,
  },
  {
    name: 'document_type',
    display_name: 'Document Type',
    description: 'Type of document (manual, guide, article, etc.)',
    value_type: 'string',
    is_multiple: false,
    llm_extraction_hint: `Classify the document type based on its structure and content.
Common types: Manual, Guide, Article, Report, Policy, Specification, Tutorial, FAQ, Release Notes.
Look for explicit labels or infer from document structure.`,
  },
  {
    name: 'version',
    display_name: 'Version',
    description: 'Document version number',
    value_type: 'string',
    is_multiple: false,
    llm_extraction_hint: `Extract the version number or revision identifier.
Look for: "Version X.Y", "Rev.", "v1.0", or version tables.
Return the version string as-is (e.g., "2.1.0", "Rev A").`,
  },
  {
    name: 'created_date',
    display_name: 'Created Date',
    description: 'When the document was originally created',
    value_type: 'date',
    is_multiple: false,
    llm_extraction_hint: `Extract the document creation or publication date.
Look for: "Date:", "Published:", "Created:", or date stamps in headers/footers.
Return in ISO format (YYYY-MM-DD) if possible.`,
  },
]

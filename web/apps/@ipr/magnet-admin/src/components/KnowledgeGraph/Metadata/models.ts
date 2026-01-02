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

// Metadata field definition - user-defined schema
export interface MetadataFieldDefinition {
  id: string
  name: string
  display_name?: string
  description: string
  value_type: MetadataValueType
  is_searchable: boolean
  is_filterable: boolean
  is_required: boolean
  allowed_values?: string[]
  default_value?: string
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
  is_searchable: boolean
  is_filterable: boolean
  is_defined: boolean
  sample_values: string[]
  allowed_values?: string[]
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
    is_searchable: true,
    is_filterable: true,
  },
  {
    name: 'language',
    display_name: 'Language',
    description: 'Primary language of the document',
    value_type: 'string',
    is_searchable: false,
    is_filterable: true,
    allowed_values: ['en', 'de', 'fr', 'es', 'it', 'pt', 'nl', 'pl', 'ru', 'zh', 'ja', 'ko'],
  },
  {
    name: 'document_type',
    display_name: 'Document Type',
    description: 'Type of document (manual, guide, article, etc.)',
    value_type: 'string',
    is_searchable: false,
    is_filterable: true,
  },
  {
    name: 'version',
    display_name: 'Version',
    description: 'Document version number',
    value_type: 'string',
    is_searchable: false,
    is_filterable: true,
  },
  {
    name: 'created_date',
    display_name: 'Created Date',
    description: 'When the document was originally created',
    value_type: 'date',
    is_searchable: false,
    is_filterable: true,
  },
]

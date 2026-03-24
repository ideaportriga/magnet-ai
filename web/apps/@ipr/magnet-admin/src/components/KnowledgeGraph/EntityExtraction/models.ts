export type EntityColumnType = 'string' | 'number' | 'boolean' | 'date'
export type EntityExtractionApproach = 'document' | 'chunks'

export const DEFAULT_ENTITY_EXTRACTION_PROMPT_TEMPLATE_SYSTEM_NAME = 'KG_ENTITY_EXTRACTION'
export const DEFAULT_ENTITY_EXTRACTION_SEGMENT_SIZE = 18000
export const DEFAULT_ENTITY_EXTRACTION_SEGMENT_OVERLAP = 0.1

export const ColumnTypeOptions = [
  { label: 'Text', value: 'string', icon: 'text_fields' },
  { label: 'Number', value: 'number', icon: 'tag' },
  { label: 'Boolean', value: 'boolean', icon: 'toggle_on' },
  { label: 'Date', value: 'date', icon: 'calendar_today' },
]

export interface EntityColumn {
  id: string
  name: string
  description: string
  type: EntityColumnType
  is_identifier: boolean
  is_required: boolean
}

export interface EntityDefinition {
  id: string
  name: string
  description: string
  enabled: boolean
  columns: EntityColumn[]
}

export interface EntityExtractionRunSettings {
  approach: EntityExtractionApproach
  prompt_template_system_name: string
  segment_size: number
  segment_overlap: number
}

export interface EntityExtractionSettings {
  entity_definitions: EntityDefinition[]
  extraction: EntityExtractionRunSettings
}

const ENTITY_EXTRACTION_SETTINGS_KEY = 'entity_extraction'
const ENTITY_COLUMN_TYPES: EntityColumnType[] = ['string', 'number', 'boolean', 'date']
const ENTITY_EXTRACTION_APPROACHES: EntityExtractionApproach[] = ['document', 'chunks']

function normalizeColumnType(value: unknown): EntityColumnType {
  const normalizedValue = String(value || '').trim()
  return ENTITY_COLUMN_TYPES.includes(normalizedValue as EntityColumnType) ? (normalizedValue as EntityColumnType) : 'string'
}

function normalizeExtractionApproach(value: unknown): EntityExtractionApproach {
  const normalizedValue = String(value || '').trim()
  return ENTITY_EXTRACTION_APPROACHES.includes(normalizedValue as EntityExtractionApproach)
    ? (normalizedValue as EntityExtractionApproach)
    : 'document'
}

function normalizeSegmentSize(value: unknown): number {
  const normalizedValue = Number(value)
  return Number.isFinite(normalizedValue) && normalizedValue > 0 ? normalizedValue : DEFAULT_ENTITY_EXTRACTION_SEGMENT_SIZE
}

function normalizeSegmentOverlap(value: unknown): number {
  const normalizedValue = Number(value)
  return Number.isFinite(normalizedValue) ? Math.min(Math.max(normalizedValue, 0), 0.9) : DEFAULT_ENTITY_EXTRACTION_SEGMENT_OVERLAP
}

function getEntityExtractionRaw(settings?: Record<string, unknown>): Record<string, unknown> | undefined {
  const entityExtractionRaw = settings?.[ENTITY_EXTRACTION_SETTINGS_KEY]
  return entityExtractionRaw && typeof entityExtractionRaw === 'object' ? (entityExtractionRaw as Record<string, unknown>) : undefined
}

export function createDefaultEntityExtractionRunSettings(): EntityExtractionRunSettings {
  return {
    approach: 'document',
    prompt_template_system_name: DEFAULT_ENTITY_EXTRACTION_PROMPT_TEMPLATE_SYSTEM_NAME,
    segment_size: DEFAULT_ENTITY_EXTRACTION_SEGMENT_SIZE,
    segment_overlap: DEFAULT_ENTITY_EXTRACTION_SEGMENT_OVERLAP,
  }
}

export function cloneEntityColumn(column: EntityColumn): EntityColumn {
  return { ...column }
}

export function cloneEntityDefinition(entity: EntityDefinition): EntityDefinition {
  return {
    ...entity,
    columns: (entity.columns || []).map(cloneEntityColumn),
  }
}

export function cloneEntityDefinitions(entityDefinitions: EntityDefinition[]): EntityDefinition[] {
  return (entityDefinitions || []).map(cloneEntityDefinition)
}

export function cloneEntityExtractionRunSettings(settings?: EntityExtractionRunSettings | null): EntityExtractionRunSettings {
  const defaults = createDefaultEntityExtractionRunSettings()
  return {
    approach: normalizeExtractionApproach(settings?.approach ?? defaults.approach),
    prompt_template_system_name: String(settings?.prompt_template_system_name ?? defaults.prompt_template_system_name).trim(),
    segment_size: normalizeSegmentSize(settings?.segment_size ?? defaults.segment_size),
    segment_overlap: normalizeSegmentOverlap(settings?.segment_overlap ?? defaults.segment_overlap),
  }
}

export function cloneEntityExtractionSettings(settings?: EntityExtractionSettings | null): EntityExtractionSettings {
  return {
    entity_definitions: cloneEntityDefinitions(settings?.entity_definitions || []),
    extraction: cloneEntityExtractionRunSettings(settings?.extraction),
  }
}

export function getEntityDefinitionsFromSettings(settings?: Record<string, unknown>): EntityDefinition[] {
  const entityExtraction = getEntityExtractionRaw(settings)
  const entityDefinitions = entityExtraction?.entity_definitions
  if (!Array.isArray(entityDefinitions)) {
    return []
  }

  return entityDefinitions
    .filter((entity): entity is Record<string, unknown> => !!entity && typeof entity === 'object')
    .map((entity) => ({
      id: String(entity.id || crypto.randomUUID()),
      name: String(entity.name || ''),
      description: String(entity.description || ''),
      enabled: entity.enabled !== false,
      columns: Array.isArray(entity.columns)
        ? entity.columns
            .filter((column): column is Record<string, unknown> => !!column && typeof column === 'object')
            .map((column) => ({
              id: String(column.id || crypto.randomUUID()),
              name: String(column.name || ''),
              description: String(column.description || ''),
              type: normalizeColumnType(column.type),
              is_identifier: !!column.is_identifier,
              is_required: !!column.is_required,
            }))
        : [],
    }))
}

export function getEntityExtractionRunSettingsFromSettings(settings?: Record<string, unknown>): EntityExtractionRunSettings {
  const defaults = createDefaultEntityExtractionRunSettings()
  const entityExtraction = getEntityExtractionRaw(settings)
  const extraction =
    entityExtraction?.extraction && typeof entityExtraction.extraction === 'object'
      ? (entityExtraction.extraction as Record<string, unknown>)
      : undefined
  const hasPromptSystemName =
    !!extraction && Object.prototype.hasOwnProperty.call(extraction, 'prompt_template_system_name')
  const isExplicitlyDisabled = extraction?.enabled === false

  return cloneEntityExtractionRunSettings({
    approach: normalizeExtractionApproach(extraction?.approach),
    prompt_template_system_name: hasPromptSystemName
      ? String(extraction?.prompt_template_system_name || '').trim()
      : isExplicitlyDisabled
        ? ''
        : defaults.prompt_template_system_name,
    segment_size: normalizeSegmentSize(extraction?.segment_size),
    segment_overlap: normalizeSegmentOverlap(extraction?.segment_overlap),
  })
}

export function getEntityExtractionSettingsFromSettings(settings?: Record<string, unknown>): EntityExtractionSettings {
  return {
    entity_definitions: getEntityDefinitionsFromSettings(settings),
    extraction: getEntityExtractionRunSettingsFromSettings(settings),
  }
}

export function withEntityDefinitions(settings: Record<string, unknown> | undefined, entityDefinitions: EntityDefinition[]): Record<string, unknown> {
  const nextSettings = settings && typeof settings === 'object' ? { ...settings } : {}
  const currentEntityExtraction = nextSettings[ENTITY_EXTRACTION_SETTINGS_KEY]

  nextSettings[ENTITY_EXTRACTION_SETTINGS_KEY] = {
    ...(currentEntityExtraction && typeof currentEntityExtraction === 'object' ? currentEntityExtraction : {}),
    entity_definitions: cloneEntityDefinitions(entityDefinitions),
  }

  return nextSettings
}

export function withEntityExtractionRunSettings(
  settings: Record<string, unknown> | undefined,
  extractionSettings: EntityExtractionRunSettings
): Record<string, unknown> {
  const nextSettings = settings && typeof settings === 'object' ? { ...settings } : {}
  const currentEntityExtraction = nextSettings[ENTITY_EXTRACTION_SETTINGS_KEY]

  nextSettings[ENTITY_EXTRACTION_SETTINGS_KEY] = {
    ...(currentEntityExtraction && typeof currentEntityExtraction === 'object' ? currentEntityExtraction : {}),
    extraction: {
      enabled: !!String(extractionSettings.prompt_template_system_name || '').trim(),
      approach: normalizeExtractionApproach(extractionSettings.approach),
      prompt_template_system_name: String(extractionSettings.prompt_template_system_name || '').trim() || undefined,
      segment_size: normalizeSegmentSize(extractionSettings.segment_size),
      segment_overlap: normalizeSegmentOverlap(extractionSettings.segment_overlap),
    },
  }

  return nextSettings
}

// --- Extraction Status ---

export type EntityExtractionStatus = 'idle' | 'running' | 'cancelling' | 'cancelled' | 'completed' | 'error'

export interface EntityExtractionStatusInfo {
  status: EntityExtractionStatus
  started_at?: string | null
  completed_at?: string | null
  progress?: { processed: number; total: number } | null
  result?: {
    approach?: string
    processed_documents?: number
    processed_chunks?: number
    skipped_documents?: number
    upserted_records?: number
    errors?: number
  } | null
  error_message?: string | null
}

const VALID_EXTRACTION_STATUSES: EntityExtractionStatus[] = ['idle', 'running', 'cancelling', 'cancelled', 'completed', 'error']

export function getExtractionStatusFromGraphDetails(graphDetails?: Record<string, any> | null): EntityExtractionStatusInfo {
  const state = graphDetails?.state
  if (!state || typeof state !== 'object') {
    return { status: 'idle' }
  }
  const raw = (state as Record<string, unknown>).entity_extraction
  if (!raw || typeof raw !== 'object') {
    return { status: 'idle' }
  }
  const statusObj = raw as Record<string, unknown>
  const status = String(statusObj.status || 'idle')
  const progressRaw = statusObj.progress && typeof statusObj.progress === 'object' ? (statusObj.progress as Record<string, unknown>) : null
  return {
    status: VALID_EXTRACTION_STATUSES.includes(status as EntityExtractionStatus) ? (status as EntityExtractionStatus) : 'idle',
    started_at: statusObj.started_at ? String(statusObj.started_at) : null,
    completed_at: statusObj.completed_at ? String(statusObj.completed_at) : null,
    progress: progressRaw
      ? { processed: Number(progressRaw.processed) || 0, total: Number(progressRaw.total) || 0 }
      : null,
    result: statusObj.result && typeof statusObj.result === 'object' ? (statusObj.result as EntityExtractionStatusInfo['result']) : null,
    error_message: statusObj.error_message ? String(statusObj.error_message) : null,
  }
}

export function createEmptyColumn(): EntityColumn {
  return {
    id: crypto.randomUUID(),
    name: '',
    description: '',
    type: 'string',
    is_identifier: false,
    is_required: false,
  }
}

export function createEmptyEntity(): EntityDefinition {
  return {
    id: crypto.randomUUID(),
    name: '',
    description: '',
    enabled: true,
    columns: [createEmptyColumn()],
  }
}

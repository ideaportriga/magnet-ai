export type EntityColumnType = 'string' | 'number' | 'boolean' | 'date'
export type EntityExtractionApproach = 'document' | 'chunks'
export type EntityExtractionMode = 'basic' | 'advanced' | 'reflective' | 'self-tuning'
export type EntityExtractionSchemaFormat = 'json_schema' | 'typescript' | 'markdown'

export const DEFAULT_ENTITY_EXTRACTION_PROMPT_TEMPLATE_SYSTEM_NAME = 'KG_ENTITY_EXTRACTION'
export const DEFAULT_ENTITY_EXTRACTION_ANALYSIS_PROMPT_TEMPLATE_SYSTEM_NAME = 'KG_ENTITY_EXTRACTION_ANALYSIS'
export const DEFAULT_ENTITY_EXTRACTION_REFLECTIVE_PROMPT_TEMPLATE_SYSTEM_NAME = 'KG_ENTITY_EXTRACTION_REFLECTIVE'
export const DEFAULT_ENTITY_EXTRACTION_SELF_TUNING_PROMPT_TEMPLATE_SYSTEM_NAME = 'KG_ENTITY_EXTRACTION_SELF_TUNING'
export const DEFAULT_ENTITY_EXTRACTION_SELF_TUNING_ANALYSIS_PROMPT_TEMPLATE_SYSTEM_NAME =
  'KG_ENTITY_EXTRACTION_SELF_TUNING_ANALYSIS'
export const DEFAULT_ENTITY_EXTRACTION_RELEVANCE_FILTER_PROMPT_TEMPLATE_SYSTEM_NAME =
  'KG_ENTITY_EXTRACTION_RELEVANCE_FILTER'
export const DEFAULT_ENTITY_EXTRACTION_MODE: EntityExtractionMode = 'basic'
export const DEFAULT_ENTITY_EXTRACTION_SCHEMA_FORMAT: EntityExtractionSchemaFormat = 'typescript'
export const DEFAULT_ENTITY_EXTRACTION_SEGMENT_SIZE = 18000
export const DEFAULT_ENTITY_EXTRACTION_SEGMENT_OVERLAP = 0.1
export const DEFAULT_ENTITY_EXTRACTION_MAX_ITERATIONS = 3
export const MIN_ENTITY_EXTRACTION_MAX_ITERATIONS = 1
export const MAX_ENTITY_EXTRACTION_MAX_ITERATIONS = 10

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
  mode: EntityExtractionMode
  schema_format: EntityExtractionSchemaFormat
  prompt_template_system_name: string
  analysis_prompt_template_system_name: string
  reflective_prompt_template_system_name: string
  self_tuning_prompt_template_system_name: string
  self_tuning_analysis_prompt_template_system_name: string
  segment_size: number
  segment_overlap: number
  max_extraction_iterations: number
}

export interface EntityExtractionRelevanceFilterSettings {
  prompt_template_system_name: string
}

export interface EntityExtractionPerformanceOptimizationsSettings {
  relevance_filter: EntityExtractionRelevanceFilterSettings
}

export interface EntityExtractionSettings {
  entity_definitions: EntityDefinition[]
  extraction: EntityExtractionRunSettings
  performance_optimizations: EntityExtractionPerformanceOptimizationsSettings
}

const ENTITY_EXTRACTION_SETTINGS_KEY = 'entity_extraction'
const ENTITY_EXTRACTION_PERFORMANCE_OPTIMIZATIONS_KEY = 'performance_optimizations'
const ENTITY_COLUMN_TYPES: EntityColumnType[] = ['string', 'number', 'boolean', 'date']
const ENTITY_EXTRACTION_APPROACHES: EntityExtractionApproach[] = ['document', 'chunks']
export const ENTITY_EXTRACTION_MODES: EntityExtractionMode[] = ['basic', 'advanced', 'reflective', 'self-tuning']
export const ENTITY_EXTRACTION_SCHEMA_FORMATS: EntityExtractionSchemaFormat[] = ['json_schema', 'typescript', 'markdown']

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

function normalizeExtractionMode(value: unknown): EntityExtractionMode {
  const normalizedValue = String(value || '').trim()
  return ENTITY_EXTRACTION_MODES.includes(normalizedValue as EntityExtractionMode)
    ? (normalizedValue as EntityExtractionMode)
    : DEFAULT_ENTITY_EXTRACTION_MODE
}

function normalizeSchemaFormat(value: unknown): EntityExtractionSchemaFormat {
  const normalizedValue = String(value || '').trim()
  return ENTITY_EXTRACTION_SCHEMA_FORMATS.includes(normalizedValue as EntityExtractionSchemaFormat)
    ? (normalizedValue as EntityExtractionSchemaFormat)
    : DEFAULT_ENTITY_EXTRACTION_SCHEMA_FORMAT
}

function normalizeSegmentSize(value: unknown): number {
  const normalizedValue = Number(value)
  return Number.isFinite(normalizedValue) && normalizedValue > 0 ? normalizedValue : DEFAULT_ENTITY_EXTRACTION_SEGMENT_SIZE
}

function normalizeSegmentOverlap(value: unknown): number {
  const normalizedValue = Number(value)
  return Number.isFinite(normalizedValue) ? Math.min(Math.max(normalizedValue, 0), 0.9) : DEFAULT_ENTITY_EXTRACTION_SEGMENT_OVERLAP
}

function normalizeMaxExtractionIterations(value: unknown): number {
  const normalizedValue = Number(value)
  if (!Number.isFinite(normalizedValue)) {
    return DEFAULT_ENTITY_EXTRACTION_MAX_ITERATIONS
  }
  const integer = Math.trunc(normalizedValue)
  return Math.min(Math.max(integer, MIN_ENTITY_EXTRACTION_MAX_ITERATIONS), MAX_ENTITY_EXTRACTION_MAX_ITERATIONS)
}

function getEntityExtractionRaw(settings?: Record<string, unknown>): Record<string, unknown> | undefined {
  const entityExtractionRaw = settings?.[ENTITY_EXTRACTION_SETTINGS_KEY]
  return entityExtractionRaw && typeof entityExtractionRaw === 'object' ? (entityExtractionRaw as Record<string, unknown>) : undefined
}

export function createDefaultEntityExtractionRelevanceFilterSettings(): EntityExtractionRelevanceFilterSettings {
  return {
    prompt_template_system_name: '',
  }
}

export function createDefaultPerformanceOptimizationsSettings(): EntityExtractionPerformanceOptimizationsSettings {
  return {
    relevance_filter: createDefaultEntityExtractionRelevanceFilterSettings(),
  }
}

export function cloneEntityExtractionRelevanceFilterSettings(
  settings?: EntityExtractionRelevanceFilterSettings | null
): EntityExtractionRelevanceFilterSettings {
  return {
    prompt_template_system_name: String(settings?.prompt_template_system_name ?? '').trim(),
  }
}

export function cloneEntityExtractionPerformanceOptimizationsSettings(
  settings?: EntityExtractionPerformanceOptimizationsSettings | null
): EntityExtractionPerformanceOptimizationsSettings {
  return {
    relevance_filter: cloneEntityExtractionRelevanceFilterSettings(settings?.relevance_filter),
  }
}

export function createDefaultEntityExtractionRunSettings(): EntityExtractionRunSettings {
  return {
    approach: 'document',
    mode: DEFAULT_ENTITY_EXTRACTION_MODE,
    schema_format: DEFAULT_ENTITY_EXTRACTION_SCHEMA_FORMAT,
    prompt_template_system_name: DEFAULT_ENTITY_EXTRACTION_PROMPT_TEMPLATE_SYSTEM_NAME,
    analysis_prompt_template_system_name: DEFAULT_ENTITY_EXTRACTION_ANALYSIS_PROMPT_TEMPLATE_SYSTEM_NAME,
    reflective_prompt_template_system_name: DEFAULT_ENTITY_EXTRACTION_REFLECTIVE_PROMPT_TEMPLATE_SYSTEM_NAME,
    self_tuning_prompt_template_system_name: DEFAULT_ENTITY_EXTRACTION_SELF_TUNING_PROMPT_TEMPLATE_SYSTEM_NAME,
    self_tuning_analysis_prompt_template_system_name:
      DEFAULT_ENTITY_EXTRACTION_SELF_TUNING_ANALYSIS_PROMPT_TEMPLATE_SYSTEM_NAME,
    segment_size: DEFAULT_ENTITY_EXTRACTION_SEGMENT_SIZE,
    segment_overlap: DEFAULT_ENTITY_EXTRACTION_SEGMENT_OVERLAP,
    max_extraction_iterations: DEFAULT_ENTITY_EXTRACTION_MAX_ITERATIONS,
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
    mode: normalizeExtractionMode(settings?.mode ?? defaults.mode),
    schema_format: normalizeSchemaFormat(settings?.schema_format ?? defaults.schema_format),
    prompt_template_system_name: String(settings?.prompt_template_system_name ?? defaults.prompt_template_system_name).trim(),
    analysis_prompt_template_system_name: String(
      settings?.analysis_prompt_template_system_name ?? defaults.analysis_prompt_template_system_name
    ).trim(),
    reflective_prompt_template_system_name: String(
      settings?.reflective_prompt_template_system_name ?? defaults.reflective_prompt_template_system_name
    ).trim(),
    self_tuning_prompt_template_system_name: String(
      settings?.self_tuning_prompt_template_system_name ?? defaults.self_tuning_prompt_template_system_name
    ).trim(),
    self_tuning_analysis_prompt_template_system_name: String(
      settings?.self_tuning_analysis_prompt_template_system_name ??
        defaults.self_tuning_analysis_prompt_template_system_name
    ).trim(),
    segment_size: normalizeSegmentSize(settings?.segment_size ?? defaults.segment_size),
    segment_overlap: normalizeSegmentOverlap(settings?.segment_overlap ?? defaults.segment_overlap),
    max_extraction_iterations: normalizeMaxExtractionIterations(settings?.max_extraction_iterations ?? defaults.max_extraction_iterations),
  }
}

export function cloneEntityExtractionSettings(settings?: EntityExtractionSettings | null): EntityExtractionSettings {
  return {
    entity_definitions: cloneEntityDefinitions(settings?.entity_definitions || []),
    extraction: cloneEntityExtractionRunSettings(settings?.extraction),
    performance_optimizations: cloneEntityExtractionPerformanceOptimizationsSettings(
      settings?.performance_optimizations
    ),
  }
}

function normalizeEntityDefinitionFromRaw(raw: Record<string, unknown>): EntityDefinition {
  return {
    id: String(raw.id || crypto.randomUUID()),
    name: String(raw.name || ''),
    description: String(raw.description || ''),
    enabled: raw.enabled !== false,
    columns: Array.isArray(raw.columns)
      ? raw.columns
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
    .map(normalizeEntityDefinitionFromRaw)
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
    mode: normalizeExtractionMode(extraction?.mode),
    schema_format: normalizeSchemaFormat(extraction?.schema_format),
    prompt_template_system_name: hasPromptSystemName
      ? String(extraction?.prompt_template_system_name || '').trim()
      : isExplicitlyDisabled
        ? ''
        : defaults.prompt_template_system_name,
    analysis_prompt_template_system_name:
      typeof extraction?.analysis_prompt_template_system_name === 'string'
        ? String(extraction.analysis_prompt_template_system_name).trim()
        : defaults.analysis_prompt_template_system_name,
    reflective_prompt_template_system_name:
      typeof extraction?.reflective_prompt_template_system_name === 'string'
        ? String(extraction.reflective_prompt_template_system_name).trim()
        : defaults.reflective_prompt_template_system_name,
    self_tuning_prompt_template_system_name:
      typeof extraction?.self_tuning_prompt_template_system_name === 'string'
        ? String(extraction.self_tuning_prompt_template_system_name).trim()
        : defaults.self_tuning_prompt_template_system_name,
    self_tuning_analysis_prompt_template_system_name:
      typeof extraction?.self_tuning_analysis_prompt_template_system_name === 'string'
        ? String(extraction.self_tuning_analysis_prompt_template_system_name).trim()
        : defaults.self_tuning_analysis_prompt_template_system_name,
    segment_size: normalizeSegmentSize(extraction?.segment_size),
    segment_overlap: normalizeSegmentOverlap(extraction?.segment_overlap),
    max_extraction_iterations: normalizeMaxExtractionIterations(extraction?.max_extraction_iterations),
  })
}

export function getPerformanceOptimizationsFromSettings(
  settings?: Record<string, unknown>
): EntityExtractionPerformanceOptimizationsSettings {
  const entityExtraction = getEntityExtractionRaw(settings)
  const raw = entityExtraction?.[ENTITY_EXTRACTION_PERFORMANCE_OPTIMIZATIONS_KEY]
  const performanceOptimizations =
    raw && typeof raw === 'object' ? (raw as Record<string, unknown>) : undefined
  const relevanceFilterRaw = performanceOptimizations?.relevance_filter
  const relevanceFilter =
    relevanceFilterRaw && typeof relevanceFilterRaw === 'object'
      ? (relevanceFilterRaw as Record<string, unknown>)
      : undefined

  return cloneEntityExtractionPerformanceOptimizationsSettings({
    relevance_filter: {
      prompt_template_system_name: String(relevanceFilter?.prompt_template_system_name || '').trim(),
    },
  })
}

export function getEntityExtractionSettingsFromSettings(settings?: Record<string, unknown>): EntityExtractionSettings {
  return {
    entity_definitions: getEntityDefinitionsFromSettings(settings),
    extraction: getEntityExtractionRunSettingsFromSettings(settings),
    performance_optimizations: getPerformanceOptimizationsFromSettings(settings),
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
      enabled:
        extractionSettings.mode === 'reflective'
          ? !!String(extractionSettings.reflective_prompt_template_system_name || '').trim()
          : extractionSettings.mode === 'self-tuning'
            ? !!String(extractionSettings.self_tuning_prompt_template_system_name || '').trim() &&
              !!String(extractionSettings.self_tuning_analysis_prompt_template_system_name || '').trim()
            : !!String(extractionSettings.prompt_template_system_name || '').trim(),
      approach: normalizeExtractionApproach(extractionSettings.approach),
      mode: normalizeExtractionMode(extractionSettings.mode),
      schema_format: normalizeSchemaFormat(extractionSettings.schema_format),
      prompt_template_system_name: String(extractionSettings.prompt_template_system_name || '').trim() || undefined,
      analysis_prompt_template_system_name:
        String(extractionSettings.analysis_prompt_template_system_name || '').trim() || undefined,
      reflective_prompt_template_system_name:
        String(extractionSettings.reflective_prompt_template_system_name || '').trim() || undefined,
      self_tuning_prompt_template_system_name:
        String(extractionSettings.self_tuning_prompt_template_system_name || '').trim() || undefined,
      self_tuning_analysis_prompt_template_system_name:
        String(extractionSettings.self_tuning_analysis_prompt_template_system_name || '').trim() ||
        undefined,
      segment_size: normalizeSegmentSize(extractionSettings.segment_size),
      segment_overlap: normalizeSegmentOverlap(extractionSettings.segment_overlap),
      max_extraction_iterations: normalizeMaxExtractionIterations(extractionSettings.max_extraction_iterations),
    },
  }

  return nextSettings
}

export function withEntityExtractionPerformanceOptimizations(
  settings: Record<string, unknown> | undefined,
  performanceOptimizations: EntityExtractionPerformanceOptimizationsSettings
): Record<string, unknown> {
  const nextSettings = settings && typeof settings === 'object' ? { ...settings } : {}
  const currentEntityExtraction = nextSettings[ENTITY_EXTRACTION_SETTINGS_KEY]
  const cloned = cloneEntityExtractionPerformanceOptimizationsSettings(performanceOptimizations)

  nextSettings[ENTITY_EXTRACTION_SETTINGS_KEY] = {
    ...(currentEntityExtraction && typeof currentEntityExtraction === 'object' ? currentEntityExtraction : {}),
    [ENTITY_EXTRACTION_PERFORMANCE_OPTIMIZATIONS_KEY]: {
      relevance_filter: {
        prompt_template_system_name: cloned.relevance_filter.prompt_template_system_name || undefined,
      },
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

// --- Export / Import ---

export const ENTITY_DEFINITIONS_EXPORT_VERSION = 1

export interface EntityDefinitionExportColumn {
  name: string
  description: string
  type: EntityColumnType
  is_identifier: boolean
  is_required: boolean
}

export interface EntityDefinitionExportEntry {
  name: string
  description: string
  enabled: boolean
  columns: EntityDefinitionExportColumn[]
}

export interface EntityDefinitionsExportEnvelope {
  magnet_kg_entity_definitions_version: number
  exported_at: string
  entity_definitions: EntityDefinitionExportEntry[]
}

export interface EntityDefinitionsImportResult {
  entities: EntityDefinition[]
  warnings: string[]
}

export interface EntityDefinitionsMergeResult {
  merged: EntityDefinition[]
  added: string[]
  overwritten: string[]
}

export function serializeEntityDefinitionsForExport(entities: EntityDefinition[]): string {
  const cloned = cloneEntityDefinitions(entities)
  const envelope: EntityDefinitionsExportEnvelope = {
    magnet_kg_entity_definitions_version: ENTITY_DEFINITIONS_EXPORT_VERSION,
    exported_at: new Date().toISOString(),
    entity_definitions: cloned.map((entity) => ({
      name: entity.name,
      description: entity.description,
      enabled: entity.enabled,
      columns: entity.columns.map((column) => ({
        name: column.name,
        description: column.description,
        type: column.type,
        is_identifier: column.is_identifier,
        is_required: column.is_required,
      })),
    })),
  }

  return JSON.stringify(envelope, null, 2)
}

export function parseEntityDefinitionsFromImport(text: string): EntityDefinitionsImportResult {
  let parsed: unknown
  try {
    parsed = JSON.parse(text)
  } catch {
    throw new Error('File is not valid JSON')
  }

  if (!parsed || typeof parsed !== 'object') {
    throw new Error('File does not contain an entity-definitions export')
  }

  const envelope = parsed as Record<string, unknown>
  const rawEntities = envelope.entity_definitions
  if (!Array.isArray(rawEntities)) {
    throw new Error('File does not contain an "entity_definitions" array')
  }

  const warnings: string[] = []
  const entities: EntityDefinition[] = []
  const seenNames = new Set<string>()

  rawEntities.forEach((raw, index) => {
    if (!raw || typeof raw !== 'object') {
      warnings.push(`Entry #${index + 1} is not an object — skipped`)
      return
    }

    const entity = normalizeEntityDefinitionFromRaw(raw as Record<string, unknown>)
    entity.id = crypto.randomUUID()
    entity.columns = entity.columns.map((column) => ({ ...column, id: crypto.randomUUID() }))

    const trimmedName = entity.name.trim()
    if (!trimmedName) {
      warnings.push(`Entry #${index + 1} has no name — skipped`)
      return
    }

    const dedupeKey = trimmedName.toLowerCase()
    if (seenNames.has(dedupeKey)) {
      warnings.push(`Duplicate entity "${trimmedName}" in file — only first kept`)
      return
    }
    seenNames.add(dedupeKey)

    entity.name = trimmedName
    entities.push(entity)
  })

  return { entities, warnings }
}

export function mergeEntityDefinitions(
  existing: EntityDefinition[],
  incoming: EntityDefinition[]
): EntityDefinitionsMergeResult {
  const merged = cloneEntityDefinitions(existing)
  const indexByName = new Map<string, number>()
  merged.forEach((entity, index) => {
    indexByName.set(entity.name.trim().toLowerCase(), index)
  })

  const added: string[] = []
  const overwritten: string[] = []

  incoming.forEach((incomingEntity) => {
    const key = incomingEntity.name.trim().toLowerCase()
    const existingIndex = indexByName.get(key)
    if (existingIndex !== undefined) {
      const preservedId = merged[existingIndex].id
      merged[existingIndex] = { ...cloneEntityDefinition(incomingEntity), id: preservedId }
      overwritten.push(merged[existingIndex].name)
    } else {
      const fresh = cloneEntityDefinition(incomingEntity)
      indexByName.set(key, merged.length)
      merged.push(fresh)
      added.push(fresh.name)
    }
  })

  return { merged, added, overwritten }
}

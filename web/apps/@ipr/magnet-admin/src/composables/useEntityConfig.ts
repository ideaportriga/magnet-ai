/**
 * Provides static entity field configuration (labels, validation rules, options)
 * without going through Vuex/chroma. Direct import from config files.
 *
 * Replaces: `const { config, requiredFields } = useChroma('entityName')`
 * With:     `const { config, requiredFields } = useEntityConfig('entityName')`
 */
import chromaConfig from '@/config/entityFieldConfig'

interface FieldConfig {
  name: string
  label?: string
  field?: string | ((...args: unknown[]) => unknown)
  type?: string
  display?: boolean
  readonly?: boolean | ((...args: unknown[]) => boolean)
  sortable?: boolean
  align?: string
  validate?: boolean
  rules?: unknown[]
  component?: unknown
  options?: Array<{ label: string; value: unknown }>
  columnNumber?: number
  [key: string]: unknown
}

interface EntityConfig {
  config: Record<string, FieldConfig>
  requiredFields: string[]
}

const configCache = new Map<string, EntityConfig>()

export function useEntityConfig(entityName: string): EntityConfig {
  if (configCache.has(entityName)) {
    return configCache.get(entityName)!
  }

  const entityDef = (chromaConfig as Record<string, { config?: Record<string, FieldConfig> }>)[entityName]
  const config = entityDef?.config ?? {}

  const requiredFields = Object.values(config)
    .filter((f) => f.validate)
    .map((f) => f.name)

  const result: EntityConfig = { config, requiredFields }
  configCache.set(entityName, result)
  return result
}

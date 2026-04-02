import { useEntityQueries, type AllEntityQueries } from '@/queries/entities'
import { useEditBufferStore } from '@/stores/editBufferStore'
import { ENTITY_READ_ONLY_FIELDS } from '@/constants/entityFields'
import { ROUTE_ENTITY_TO_BUFFER_TYPE, ROUTE_ENTITY_TO_QUERY_KEY } from '@/constants/entityMapping'

interface SaveResult {
  success: boolean
  error?: unknown
}

/**
 * Service for saving/reverting entities from LayoutDefault toolbar.
 *
 * Replaces the old entityRegistry pattern that depended on Pinia entity detail stores.
 * Works through editBufferStore directly.
 */
export function useEntitySaveService() {
  const queries = useEntityQueries()
  const editBuffer = useEditBufferStore()

  function _findBufferKey(routeEntity: string): string | null {
    const bufferType = ROUTE_ENTITY_TO_BUFFER_TYPE[routeEntity]
    if (!bufferType) return null
    return editBuffer.findBufferKeyByEntityType(bufferType)
  }

  function buildPayload(bufferKey: string): Record<string, unknown> | null {
    const draft = editBuffer.getDraft(bufferKey)
    if (!draft) return null
    const payload = { ...draft }
    for (const field of ENTITY_READ_ONLY_FIELDS) delete payload[field]
    return payload
  }

  async function save(routeEntity: string): Promise<SaveResult> {
    const bufferKey = _findBufferKey(routeEntity)
    if (!bufferKey) return { success: false, error: `No buffer found for ${routeEntity}` }

    const buf = editBuffer.getBuffer(bufferKey)
    if (!buf?.entityId) return { success: false }

    const queryKey = ROUTE_ENTITY_TO_QUERY_KEY[routeEntity]
    if (!queryKey) return { success: false, error: `Unknown query key for ${routeEntity}` }

    const payload = buildPayload(bufferKey)
    if (!payload) return { success: false }

    const entityQueries = queries[queryKey]
    const { mutateAsync } = entityQueries.useUpdate()
    const result = await mutateAsync({ id: buf.entityId, data: payload })
    editBuffer.commitBuffer(bufferKey, result as Record<string, unknown>)
    return { success: true }
  }

  function revert(routeEntity: string) {
    const bufferKey = _findBufferKey(routeEntity)
    if (bufferKey) editBuffer.revertBuffer(bufferKey)
  }

  function isDirty(routeEntity: string): boolean {
    const bufferType = ROUTE_ENTITY_TO_BUFFER_TYPE[routeEntity]
    if (!bufferType) return false
    return editBuffer.isEntityTypeDirty(bufferType)
  }

  return { save, revert, isDirty }
}

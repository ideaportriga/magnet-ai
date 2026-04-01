import type { AllEntityQueries } from '@/queries/entities'
import type { BaseEntity } from '@/types'
import { useEntityDetailBase, type UseEntityDetailBaseOptions } from './useEntityDetailBase'

export type UseEntityDetailOptions = UseEntityDetailBaseOptions

/**
 * Composable that bridges TanStack Query (server state) <-> editBuffer (form state) <-> workspace tab (dirty indicator).
 *
 * Usage in a detail page:
 * ```ts
 * const { draft, isLoading, isDirty, updateField, save, revert } = useEntityDetail<Provider>('provider')
 * ```
 */
export function useEntityDetail<T extends BaseEntity>(
  entityKey: keyof AllEntityQueries,
  options?: UseEntityDetailOptions,
) {
  const base = useEntityDetailBase<T>(entityKey, options)

  return {
    /** Raw server data (from TanStack Query) */
    data: base.data,
    /** Draft data (editable copy from editBuffer) */
    draft: base.draft,
    /** Entity ID from route */
    id: base.id,
    /** Buffer key (entityType:entityId) */
    bufferKey: base.bufferKey,
    /** Loading state from TanStack Query */
    isLoading: base.isLoading,
    /** Whether draft differs from original */
    isDirty: base.isDirty,
    /** Update a single field path in the draft */
    updateField: base.updateField,
    /** Update multiple field paths in the draft */
    updateFields: base.updateFields,
    /** Revert draft to original server data */
    revert: base.revert,
    /** Save draft to server via TanStack mutation */
    save: base.save,
    /** Delete entity */
    remove: base.remove,
    /** Manually refetch from server */
    refetch: base.refetch,
    /** Build save payload (draft minus read-only fields) */
    buildPayload: base.buildPayload,
  }
}

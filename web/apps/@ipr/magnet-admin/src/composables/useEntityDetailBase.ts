import { computed, ref, watch, onMounted, onActivated, onBeforeUnmount, type Ref, type ComputedRef } from 'vue'
import { useRoute } from 'vue-router'
import { useEntityQueries, type AllEntityQueries } from '@/queries/entities'
import { useEditBufferStore } from '@/stores/editBufferStore'
import { useWorkspaceStore } from '@/stores/workspaceStore'
import type { BaseEntity } from '@/types'
import { ENTITY_READ_ONLY_FIELDS } from '@/constants/entityFields'

export interface UseEntityDetailBaseOptions {
  /** Custom route param name for entity ID. Default: 'id' */
  idParam?: string
  /** If true, re-init editBuffer when server data changes (e.g., after save). Default: false */
  syncOnRefetch?: boolean
  /** Fields to strip before sending to server. Default: id, created_at, updated_at, created_by, updated_by */
  readOnlyFields?: string[]
  /** Called when editBuffer is initialized from server data (e.g., to init variant selection) */
  onBufferInit?: (data: Record<string, unknown>) => void
}

export interface UseEntityDetailBaseReturn<T extends BaseEntity> {
  /** Raw server data (from TanStack Query) */
  data: Ref<T | undefined>
  /** Draft data (editable copy from editBuffer) */
  draft: ComputedRef<T | undefined>
  /** Entity ID from route */
  id: Ref<string | undefined>
  /** Buffer key (entityType:entityId) */
  bufferKey: ComputedRef<string>
  /** Loading state from TanStack Query */
  isLoading: Ref<boolean>
  /** Whether draft differs from original */
  isDirty: ComputedRef<boolean>
  /** Update a single field path in the draft */
  updateField: (path: string, value: unknown) => void
  /** Update multiple field paths in the draft */
  updateFields: (partial: Record<string, unknown>) => void
  /** Revert draft to original server data */
  revert: () => void
  /** Save draft to server via TanStack mutation */
  save: () => Promise<{ success: boolean; data?: T; error?: unknown }>
  /** Delete entity */
  remove: () => Promise<{ success: boolean; error?: unknown }>
  /** Manually refetch from server */
  refetch: () => void
  /** Build save payload (draft minus read-only fields) */
  buildPayload: () => Record<string, unknown> | null
  /** Access to underlying stores/queries for advanced usage */
  editBuffer: ReturnType<typeof useEditBufferStore>
  workspace: ReturnType<typeof useWorkspaceStore>
  entityQueries: ReturnType<typeof useEntityQueries>[keyof AllEntityQueries]
}

/**
 * Base composable that bridges TanStack Query (server state) <-> editBuffer (form state) <-> workspace tab (dirty indicator).
 * Used by useEntityDetail and useVariantEntityDetail to avoid code duplication.
 */
export function useEntityDetailBase<T extends BaseEntity>(
  entityKey: keyof AllEntityQueries,
  options?: UseEntityDetailBaseOptions,
): UseEntityDetailBaseReturn<T> {
  const route = useRoute()
  const queries = useEntityQueries()
  const editBuffer = useEditBufferStore()
  const workspace = useWorkspaceStore()

  const idParam = options?.idParam ?? 'id'
  const readOnlyFields = options?.readOnlyFields ?? ENTITY_READ_ONLY_FIELDS

  // Only read route ID when the current route's entity matches the requested entityKey.
  // Prevents fetching the wrong entity when a component using useEntityDetail('collections')
  // is rendered on a different entity's page (e.g. CreateNew dialog on knowledge-providers detail).
  const resolveId = () =>
    (route.meta?.entity as string | undefined) === entityKey
      ? (route.params[idParam] as string | undefined)
      : undefined

  // Stable ref: does NOT reactively track the global route object.
  // Keep-alive caches multiple component instances; if we used computed(() => route.params.id),
  // ALL cached instances would recompute when ANY tab is switched, firing N backend requests.
  const id = ref<string | undefined>(resolveId())

  onMounted(() => {
    id.value = resolveId()
  })
  onActivated(() => {
    id.value = resolveId()

    // Re-initialize editBuffer if it was removed while the component was cached by keep-alive
    // (e.g., user closed a workspace tab then navigated back to the same entity).
    // The data watcher won't fire if TanStack Query's data ref hasn't changed,
    // so we must manually check and re-init the buffer here.
    const key = bufferKey.value
    if (id.value && data.value && !editBuffer.hasBuffer(key)) {
      editBuffer.initBuffer(key, entityKey as string, id.value, data.value as Record<string, unknown>)
      options?.onBufferInit?.(data.value as Record<string, unknown>)
    }
  })

  const bufferKey = computed(() => `${entityKey}:${id.value}`)

  // 1. Fetch entity + prepare mutations
  const entityQueries = queries[entityKey]
  const { data, isLoading, refetch } = entityQueries.useDetail(id)
  const { mutateAsync: updateEntity } = entityQueries.useUpdate()
  const { mutateAsync: removeEntity } = entityQueries.useRemove()

  // 2. Init editBuffer when server data arrives
  watch(
    data,
    (newData) => {
      if (!newData || !id.value) return
      const key = bufferKey.value
      const entity = newData as Record<string, unknown>

      if (!editBuffer.hasBuffer(key)) {
        editBuffer.initBuffer(key, entityKey as string, id.value, entity)
        options?.onBufferInit?.(entity)
      } else if (options?.syncOnRefetch) {
        editBuffer.commitBuffer(key, entity)
      }
    },
    { immediate: true },
  )

  // 3. Reactive draft + dirty state
  const draft = computed(() => editBuffer.getDraft(bufferKey.value) as T | undefined)
  const isDirty = computed(() => editBuffer.isDirty(bufferKey.value))

  // 4. Sync dirty flag to workspace tab
  watch(isDirty, (dirty) => {
    const tab = workspace.tabs.find(
      (t) => t.entityType === entityKey && t.entityId === id.value,
    )
    if (tab) workspace.markDirty(tab.id, dirty)
  })

  // 5. Helpers
  function updateField(path: string, value: unknown) {
    editBuffer.updateDraft(bufferKey.value, path, value)
  }

  function updateFields(partial: Record<string, unknown>) {
    editBuffer.updateDraftBatch(bufferKey.value, partial)
  }

  function revert() {
    editBuffer.revertBuffer(bufferKey.value)
  }

  function buildPayload(): Record<string, unknown> | null {
    const draftData = editBuffer.getDraft(bufferKey.value)
    if (!draftData) return null
    const payload: Record<string, unknown> = { ...draftData }
    for (const field of readOnlyFields) {
      delete payload[field]
    }
    return payload
  }

  async function save(): Promise<{ success: boolean; data?: T; error?: unknown }> {
    const key = bufferKey.value
    const entityId = editBuffer.getBuffer(key)?.entityId
    const payload = buildPayload()
    if (!payload || !entityId) return { success: false }

    try {
      const result = await updateEntity({ id: entityId, data: payload as Partial<T> })
      editBuffer.commitBuffer(key, result as Record<string, unknown>)
      return { success: true, data: result as T }
    } catch (error) {
      // Error toast is handled by the global onMutationError handler in initNewStack.ts
      return { success: false, error }
    }
  }

  async function remove(): Promise<{ success: boolean; error?: unknown }> {
    const entityId = editBuffer.getBuffer(bufferKey.value)?.entityId
    if (!entityId) return { success: false }

    try {
      await removeEntity(entityId)
      editBuffer.removeBuffer(bufferKey.value)
      return { success: true }
    } catch (error) {
      // Error toast is handled by the global onMutationError handler in initNewStack.ts
      return { success: false, error }
    }
  }

  onBeforeUnmount(() => {
    const tabExists = workspace.tabs.some(
      (t) => t.entityType === entityKey && t.entityId === id.value,
    )
    if (!tabExists) {
      editBuffer.removeBuffer(bufferKey.value)
    }
  })

  return {
    data: data as Ref<T | undefined>,
    draft,
    id,
    bufferKey,
    isLoading,
    isDirty,
    updateField,
    updateFields,
    revert,
    save,
    remove,
    refetch,
    buildPayload,
    editBuffer,
    workspace,
    entityQueries,
  }
}

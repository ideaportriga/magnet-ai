import { defineStore } from 'pinia'
import { ref } from 'vue'
import { cloneDeep, isEqual, set as lodashSet, get as lodashGet } from 'lodash'

export interface EditBuffer {
  entityType: string
  entityId: string | null
  original: Record<string, unknown>
  draft: Record<string, unknown>
}

export const useEditBufferStore = defineStore('editBuffer', () => {
  const buffers = ref<Map<string, EditBuffer>>(new Map())

  function initBuffer(key: string, entityType: string, entityId: string | null, data: Record<string, unknown>) {
    buffers.value.set(key, {
      entityType,
      entityId,
      original: cloneDeep(data),
      draft: cloneDeep(data),
    })
  }

  function getBuffer(key: string): EditBuffer | undefined {
    return buffers.value.get(key)
  }

  function getDraft(key: string): Record<string, unknown> | undefined {
    return buffers.value.get(key)?.draft
  }

  function getOriginal(key: string): Record<string, unknown> | undefined {
    return buffers.value.get(key)?.original
  }

  function updateDraft(key: string, path: string, value: unknown) {
    const buf = buffers.value.get(key)
    if (!buf) return
    const clone = cloneDeep(buf.draft)
    lodashSet(clone, path, value)
    buf.draft = clone
  }

  function updateDraftBatch(key: string, partial: Record<string, unknown>) {
    const buf = buffers.value.get(key)
    if (!buf) return
    const clone = cloneDeep(buf.draft)
    for (const [path, value] of Object.entries(partial)) {
      lodashSet(clone, path, value)
    }
    buf.draft = clone
  }

  /** Replace entire draft (useful for variant operations that change whole sub-objects) */
  function replaceDraft(key: string, newDraft: Record<string, unknown>) {
    const buf = buffers.value.get(key)
    if (!buf) return
    buf.draft = cloneDeep(newDraft)
  }

  function isDirty(key: string): boolean {
    const buf = buffers.value.get(key)
    if (!buf) return false
    return !isEqual(buf.original, buf.draft)
  }

  function getDiff(key: string): Record<string, unknown> {
    const buf = buffers.value.get(key)
    if (!buf) return {}
    const diff: Record<string, unknown> = {}
    const allKeys = new Set([...Object.keys(buf.draft), ...Object.keys(buf.original)])
    for (const draftKey of allKeys) {
      if (!isEqual(lodashGet(buf.original, draftKey), lodashGet(buf.draft, draftKey))) {
        diff[draftKey] = buf.draft[draftKey]
      }
    }
    return diff
  }

  function revertBuffer(key: string) {
    const buf = buffers.value.get(key)
    if (!buf) return
    buf.draft = cloneDeep(buf.original)
  }

  function commitBuffer(key: string, serverData?: Record<string, unknown>) {
    const buf = buffers.value.get(key)
    if (!buf) return
    const data = serverData ?? buf.draft
    buf.original = cloneDeep(data)
    buf.draft = cloneDeep(data)
  }

  function removeBuffer(key: string) {
    buffers.value.delete(key)
  }

  function hasBuffer(key: string): boolean {
    return buffers.value.has(key)
  }

  /** Check if server data has diverged while the user has unsaved changes */
  function hasServerConflict(key: string, newServerData: Record<string, unknown>): boolean {
    const buf = buffers.value.get(key)
    if (!buf) return false
    return !isEqual(buf.original, newServerData) && isDirty(key)
  }

  /** Find buffer key by entityType. Returns the first dirty match, or any match as fallback. */
  function findBufferKeyByEntityType(entityType: string): string | null {
    let fallback: string | null = null
    for (const [key, buf] of buffers.value.entries()) {
      if (buf.entityType === entityType) {
        if (isDirty(key)) return key
        if (!fallback) fallback = key
      }
    }
    return fallback
  }

  /** Check if any buffer of the given entityType has unsaved changes. */
  function isEntityTypeDirty(entityType: string): boolean {
    for (const [key, buf] of buffers.value.entries()) {
      if (buf.entityType === entityType && isDirty(key)) return true
    }
    return false
  }

  return {
    buffers,
    initBuffer,
    getBuffer,
    getDraft,
    getOriginal,
    updateDraft,
    updateDraftBatch,
    replaceDraft,
    isDirty,
    getDiff,
    revertBuffer,
    commitBuffer,
    removeBuffer,
    hasBuffer,
    hasServerConflict,
    findBufferKeyByEntityType,
    isEntityTypeDirty,
  }
})

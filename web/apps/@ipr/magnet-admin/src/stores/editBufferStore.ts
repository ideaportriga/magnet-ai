import { defineStore } from 'pinia'
import { ref } from 'vue'
import { cloneDeep, isEqual, set as lodashSet, get as lodashGet } from 'lodash'

/**
 * Recursive structural diff. Emits dot-paths (with `[idx]` for arrays)
 * for every leaf where `before` and `after` disagree. Identical to the
 * convention used by the backend audit `compute_diff`, so the same
 * path syntax is rendered everywhere.
 */
function walkDiff(
  before: unknown,
  after: unknown,
  prefix: string,
  out: Set<string>,
): void {
  if (isEqual(before, after)) return

  const isObj = (v: unknown): v is Record<string, unknown> =>
    typeof v === 'object' && v !== null && !Array.isArray(v)

  if (isObj(before) && isObj(after)) {
    const keys = new Set([...Object.keys(before), ...Object.keys(after)])
    for (const k of keys) {
      const child = prefix ? `${prefix}.${k}` : k
      walkDiff(before[k], after[k], child, out)
    }
    return
  }
  if (Array.isArray(before) && Array.isArray(after)) {
    const len = Math.max(before.length, after.length)
    for (let i = 0; i < len; i++) {
      const child = prefix ? `${prefix}[${i}]` : `[${i}]`
      walkDiff(before[i], after[i], child, out)
    }
    return
  }
  out.add(prefix || '$')
}

export interface EditBuffer {
  entityType: string
  entityId: string | null
  original: Record<string, unknown>
  draft: Record<string, unknown>
  /** Set of dot-paths suggested by the AI editor on the most recent
   *  ai_edit call. Drives the "AI-suggested" highlight in the form. */
  aiSuggestedPaths: Set<string>
  /** ai_edit_request id that produced the current `aiSuggestedPaths`.
   *  Cleared on revert/commit. The save request forwards it as the
   *  ``X-AI-Request-Id`` header so the audit row gets the bridge column
   *  populated. */
  aiRequestId: string | null
}

export const useEditBufferStore = defineStore('editBuffer', () => {
  const buffers = ref<Map<string, EditBuffer>>(new Map())

  function initBuffer(key: string, entityType: string, entityId: string | null, data: Record<string, unknown>) {
    buffers.value.set(key, {
      entityType,
      entityId,
      original: cloneDeep(data),
      draft: cloneDeep(data),
      aiSuggestedPaths: new Set<string>(),
      aiRequestId: null,
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

  /**
   * Flat set of dot-paths where `draft` differs from `original`. Used by
   * the form to render per-field "unsaved" / "AI-suggested" highlights.
   * Recurses into both objects and lists (compared by index).
   */
  function getChangedPaths(key: string): Set<string> {
    const buf = buffers.value.get(key)
    if (!buf) return new Set<string>()
    const out = new Set<string>()
    walkDiff(buf.original, buf.draft, '', out)
    return out
  }

  /** Apply an AI-suggested state on top of the current draft.
   *
   *  Replaces the draft wholesale (so unspecified fields are reset to
   *  what the AI sent — typically the previous state, since the model is
   *  instructed to preserve untouched fields), and records the set of
   *  paths that differ from the **current draft** so the UI can mark
   *  them as "AI-suggested". Manual edits made before the AI call stay
   *  recorded as plain "dirty" by the next render via the normal
   *  original-vs-draft diff. */
  function applyAiPatch(
    key: string,
    newDraft: Record<string, unknown>,
    aiRequestId: string | null = null,
  ): Set<string> {
    const buf = buffers.value.get(key)
    if (!buf) return new Set<string>()
    const suggested = new Set<string>()
    walkDiff(buf.draft, newDraft, '', suggested)
    buf.draft = cloneDeep(newDraft)
    buf.aiSuggestedPaths = suggested
    buf.aiRequestId = aiRequestId
    return suggested
  }

  /** Drop the AI-suggested highlight (called on save / revert / new AI call). */
  function clearAiSuggested(key: string) {
    const buf = buffers.value.get(key)
    if (!buf) return
    buf.aiSuggestedPaths = new Set<string>()
    buf.aiRequestId = null
  }

  function getAiSuggestedPaths(key: string): Set<string> {
    return buffers.value.get(key)?.aiSuggestedPaths ?? new Set<string>()
  }

  function getAiRequestId(key: string): string | null {
    return buffers.value.get(key)?.aiRequestId ?? null
  }

  function revertBuffer(key: string) {
    const buf = buffers.value.get(key)
    if (!buf) return
    buf.draft = cloneDeep(buf.original)
    buf.aiSuggestedPaths = new Set<string>()
    buf.aiRequestId = null
  }

  function commitBuffer(key: string, serverData?: Record<string, unknown>) {
    const buf = buffers.value.get(key)
    if (!buf) return
    const data = serverData ?? buf.draft
    buf.original = cloneDeep(data)
    buf.draft = cloneDeep(data)
    buf.aiSuggestedPaths = new Set<string>()
    buf.aiRequestId = null
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
    getChangedPaths,
    applyAiPatch,
    clearAiSuggested,
    getAiSuggestedPaths,
    getAiRequestId,
    revertBuffer,
    commitBuffer,
    removeBuffer,
    hasBuffer,
    hasServerConflict,
    findBufferKeyByEntityType,
    isEntityTypeDirty,
  }
})

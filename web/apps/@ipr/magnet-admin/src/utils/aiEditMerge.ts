/**
 * Merge an AI-suggested variant body into a full entity draft.
 *
 * Two shapes exist across the codebase:
 *
 *   - Agent ─ `variants[].value` carries the body, with `variant` and
 *     `description` siblings. Merge → `variants[idx].value = newState`.
 *   - Prompt / RagTool / RetrievalTool ─ each `variants[i]` IS the body
 *     (the `variant` key is just a field inside it). Merge →
 *     `variants[idx] = newState` (preserving the `variant` field if the
 *     LLM dropped it).
 *
 * Returns the new draft. The caller hands it to `editBuffer.applyAiPatch`.
 */

import { cloneDeep } from 'lodash'
import { setNextSaveContext } from '@/api/saveContext'
import type { AIEditResponse } from '@/api/aiEdit'

export type AiEditVariantShape = 'wrapped' | 'flat'

export interface MergeAiEditOptions {
  /**
   * 'wrapped' — Agent-style; new_state is the inner `value` payload.
   * 'flat' — Prompt/RAG/Retrieval-style; new_state IS the variant.
   */
  shape: AiEditVariantShape
}

export function mergeAiVariantPatch(
  currentDraft: Record<string, unknown>,
  newState: Record<string, unknown>,
  { shape }: MergeAiEditOptions,
): Record<string, unknown> | null {
  const next = cloneDeep(currentDraft)
  const variants = Array.isArray(next.variants) ? (next.variants as Record<string, unknown>[]) : null
  if (!variants) return null

  const active = (next as { active_variant?: string }).active_variant
  const idx = variants.findIndex((v) => v?.variant === active)
  if (idx === -1) return null

  if (shape === 'wrapped') {
    variants[idx] = { ...variants[idx], value: newState }
  } else {
    // Always keep the variant key — the LLM is told to preserve it but
    // we'd rather not trust it on every call.
    const preservedVariant = variants[idx]?.variant ?? active
    variants[idx] = { ...newState, variant: preservedVariant }
  }
  next.variants = variants
  return next
}

export function applyAiVariantResult(
  editBuffer: {
    getDraft: (key: string) => Record<string, unknown> | undefined
    applyAiPatch: (
      key: string,
      newDraft: Record<string, unknown>,
      aiRequestId?: string | null,
    ) => Set<string>
  },
  key: string,
  result: AIEditResponse,
  options: MergeAiEditOptions,
): boolean {
  const currentDraft = editBuffer.getDraft(key)
  if (!currentDraft) return false
  const next = mergeAiVariantPatch(currentDraft, result.new_state, options)
  if (!next) return false
  editBuffer.applyAiPatch(key, next, result.ai_request_id ?? null)
  return true
}

export function setAiSaveContext(
  editBuffer: { getAiRequestId: (key: string) => string | null },
  key: string,
  entityType: string,
  entityId: string,
): void {
  const aiRequestId = editBuffer.getAiRequestId(key)
  if (aiRequestId) setNextSaveContext({ aiRequestId, entityType, entityId })
}

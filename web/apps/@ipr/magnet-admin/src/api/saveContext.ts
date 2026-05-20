/**
 * Tiny global "next save context" used to forward an AI-edit request
 * id from a details page through the regular `useUpdate` mutation
 * (which doesn't expose per-call headers) to the underlying fetch.
 *
 * Usage:
 *
 *   beforeSave({ aiRequestId: buffer.getAiRequestId(key), entityType, entityId })
 *   await save()      // useUpdate.mutateAsync internally — does PATCH
 *
 * The fetch wrapper installed in `entityApis.ts` reads the context on
 * matching PATCH and adds an ``X-AI-Request-Id`` header when it's set.
 * The slot is single-use: it self-clears only after a matching request so
 * unrelated concurrent PATCHes don't steal the AI context.
 *
 * The context is global because saves trigger through generic mutation
 * helpers that we don't want to fork per-feature; the single-use
 * semantics keeps the surface small.
 */

interface SaveContext {
  aiRequestId: string | null
  entityType?: string | null
  entityId?: string | null
}

let _next: SaveContext | null = null

export function setNextSaveContext(ctx: SaveContext): void {
  _next = ctx
}

export function peekNextSaveContext(): SaveContext | null {
  return _next
}

export function clearNextSaveContext(ctx?: SaveContext | null): void {
  if (!ctx || _next === ctx) _next = null
}

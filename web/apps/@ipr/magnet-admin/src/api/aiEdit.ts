/**
 * Admin-API wrapper for the AI entity editor.
 *
 * Backed by Litestar controller in
 * ``api/src/core/domain/ai_edit/controller.py``:
 *   POST /ai-edit/{entity_type}/{entity_id}
 *   GET  /ai-edit/history
 *   GET  /ai-edit/history/{request_id}
 */

import { getApiClient } from './entityApis'

export interface AIEditUsage {
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
  cost_usd: number
  latency_ms: number
  model?: string | null
}

export interface AIEditDiffValue {
  from: unknown
  to: unknown
}

export interface AIEditResponse {
  ai_request_id: string
  entity_type: string
  entity_id: string
  status: 'succeeded' | 'schema_invalid' | 'llm_error' | string
  new_state: Record<string, unknown>
  diff: Record<string, AIEditDiffValue>
  usage: AIEditUsage
}

export interface AIEditRequestPayload {
  instruction: string
  model?: string | null
}

export async function proposeEntityAiEdit(
  entityType: string,
  entityId: string,
  payload: AIEditRequestPayload,
): Promise<AIEditResponse> {
  const client = getApiClient()
  return client.post<AIEditResponse>(`ai-edit/${entityType}/${entityId}`, payload)
}

// ── History ────────────────────────────────────────────────────────

export interface AIEditHistoryEntry {
  id: string
  tenant_id: string
  actor_id?: string | null
  entity_type: string
  entity_id: string
  instruction: string
  model?: string | null
  status: string
  error_message?: string | null
  prompt_tokens: number
  completion_tokens: number
  total_tokens: number
  cost_usd: number
  latency_ms: number
  created_at: string
}

export interface AIEditHistoryDetail extends AIEditHistoryEntry {
  snapshot_before?: Record<string, unknown> | null
  snapshot_after?: Record<string, unknown> | null
}

export interface AIEditHistoryFilters {
  entity_type?: string
  entity_id?: string
  actor_id?: string
  status?: string
  date_from?: string
  date_to?: string
  limit?: number
  offset?: number
}

export async function listAiEditHistory(
  filters: AIEditHistoryFilters = {},
): Promise<AIEditHistoryEntry[]> {
  const client = getApiClient()
  const params: Record<string, string | number> = {}
  for (const [k, v] of Object.entries(filters)) {
    if (v !== undefined && v !== null && v !== '') params[k] = v as string | number
  }
  return client.get<AIEditHistoryEntry[]>('ai-edit/history', params)
}

export async function getAiEditHistoryDetail(
  requestId: string,
): Promise<AIEditHistoryDetail> {
  const client = getApiClient()
  return client.get<AIEditHistoryDetail>(`ai-edit/history/${requestId}`)
}

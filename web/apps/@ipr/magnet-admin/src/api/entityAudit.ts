/**
 * Admin-API wrapper for the entity audit trail.
 *
 * Backed by Litestar controller in
 * ``api/src/core/domain/entity_audit_log/controller.py``:
 *   GET  /audit/entity-trail              — list
 *   GET  /audit/entity-trail/{id}         — detail with snapshots
 *   POST /audit/entity-trail/{id}/restore — apply snapshot_before
 *
 * Paths here are relative to the admin baseUrl (same as adminAccess.ts).
 */

import { getApiClient } from './entityApis'

export type EntityAuditAction = 'create' | 'update' | 'delete' | 'restore'

export interface EntityAuditDiffValue {
  from: unknown
  to: unknown
}

export interface EntityAuditEntry {
  id: string
  tenant_id: string
  entity_type: string
  entity_id: string
  action: EntityAuditAction | string
  actor_id?: string | null
  actor_type: string
  actor_display: string
  source: string
  request_id?: string | null
  ai_request_id?: string | null
  can_restore?: boolean
  diff: Record<string, EntityAuditDiffValue>
  created_at: string
}

export interface EntityAuditDetail extends EntityAuditEntry {
  snapshot_before: Record<string, unknown> | null
  snapshot_after: Record<string, unknown> | null
}

export interface EntityAuditRestoreResponse {
  entity_type: string
  entity_id: string
  restored_from_audit_id: string
  restore_audit_id?: string | null
  snapshot_applied: Record<string, unknown>
}

export interface EntityAuditFilters {
  entity_type?: string
  entity_id?: string
  actor_id?: string
  action?: EntityAuditAction | string
  date_from?: string
  date_to?: string
  limit?: number
  offset?: number
}

export async function listEntityAudit(
  filters: EntityAuditFilters = {},
): Promise<EntityAuditEntry[]> {
  const client = getApiClient()
  const params: Record<string, string | number> = {}
  if (filters.entity_type) params.entity_type = filters.entity_type
  if (filters.entity_id) params.entity_id = filters.entity_id
  if (filters.actor_id) params.actor_id = filters.actor_id
  if (filters.action) params.action = filters.action
  if (filters.date_from) params.date_from = filters.date_from
  if (filters.date_to) params.date_to = filters.date_to
  if (filters.limit !== undefined) params.limit = filters.limit
  if (filters.offset !== undefined) params.offset = filters.offset
  return client.get<EntityAuditEntry[]>('audit/entity-trail', params)
}

export async function getEntityAuditEntry(id: string): Promise<EntityAuditDetail> {
  const client = getApiClient()
  return client.get<EntityAuditDetail>(`audit/entity-trail/${id}`)
}

export async function restoreEntityAuditEntry(
  id: string,
): Promise<EntityAuditRestoreResponse> {
  const client = getApiClient()
  return client.post<EntityAuditRestoreResponse>(`audit/entity-trail/${id}/restore`)
}

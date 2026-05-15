/**
 * Admin-API surface for the access-control plan (PR 5).
 *
 * Wraps `/api/admin/permissions`, `/api/admin/roles`, `/api/admin/users`,
 * `/api/admin/access-log`. Uses the same shared `apiClient` that already
 * holds the `urlAdmin` baseUrl, so paths here are relative ("roles", not
 * "/api/admin/roles").
 *
 * Each call returns the backend payload as-is; the Vue pages massage it.
 */

import { getApiClient } from './entityApis'

// ── Permissions catalog ─────────────────────────────────────────────────

export interface PermissionEntry {
  code: string
  resource_type: string
  action: string
  description?: string | null
  is_system: boolean
}

export async function listPermissions(resourceType?: string): Promise<PermissionEntry[]> {
  const client = getApiClient()
  const params = resourceType ? { resource_type: resourceType } : undefined
  return client.get<PermissionEntry[]>('permissions', params)
}

export async function reloadPermissionsCache(): Promise<{ status: string }> {
  const client = getApiClient()
  return client.post<{ status: string }>('permissions/cache/reload')
}

// ── Roles ───────────────────────────────────────────────────────────────

export interface RoleSummary {
  id: string
  slug: string
  name: string
  description?: string | null
  is_system: boolean
  tenant_id?: string | null
  permissions: string[]
  user_count: number
  created_at?: string | null
  updated_at?: string | null
}

export interface RoleCreatePayload {
  slug: string
  name: string
  description?: string | null
  permissions: string[]
}

export interface RoleUpdatePayload {
  name?: string
  description?: string | null
}

export async function listRoles(): Promise<RoleSummary[]> {
  const client = getApiClient()
  return client.get<RoleSummary[]>('roles')
}

export async function getRole(id: string): Promise<RoleSummary> {
  const client = getApiClient()
  return client.get<RoleSummary>(`roles/${id}`)
}

export async function createRole(payload: RoleCreatePayload): Promise<RoleSummary> {
  const client = getApiClient()
  return client.post<RoleSummary>('roles', payload)
}

export async function updateRole(id: string, payload: RoleUpdatePayload): Promise<RoleSummary> {
  const client = getApiClient()
  return client.patch<RoleSummary>(`roles/${id}`, payload)
}

export async function replaceRolePermissions(id: string, permissions: string[]): Promise<RoleSummary> {
  const client = getApiClient()
  return client.put<RoleSummary>(`roles/${id}/permissions`, { permissions })
}

export async function deleteRole(id: string): Promise<void> {
  const client = getApiClient()
  await client.delete(`roles/${id}`)
}

// ── Users (admin view) ──────────────────────────────────────────────────

export interface AdminUser {
  id: string
  email?: string
  name?: string
  preferred_username?: string
  tenant_id?: string | null
  is_active?: boolean
  is_superuser?: boolean
  last_login_at?: string | null
  created_at?: string | null
  updated_at?: string | null
  roles?: string[]
  // Some backends echo extra fields — keep open shape.
  [key: string]: unknown
}

export async function listUsers(): Promise<AdminUser[]> {
  const client = getApiClient()
  return client.get<AdminUser[]>('users')
}

export async function getUser(id: string): Promise<AdminUser> {
  const client = getApiClient()
  return client.get<AdminUser>(`users/${id}`)
}

export interface UserRolesPatchPayload {
  add?: string[]
  remove?: string[]
}

export interface UserRolesPatchResponse {
  added: string[]
  removed: string[]
  skipped_already_assigned?: string[]
  skipped_not_assigned?: string[]
}

export async function patchUserRoles(
  id: string,
  payload: UserRolesPatchPayload,
): Promise<UserRolesPatchResponse> {
  const client = getApiClient()
  return client.patch<UserRolesPatchResponse>(`users/${id}/roles`, payload)
}

// ── Access (audit) log ──────────────────────────────────────────────────

export interface AccessAuditEntry {
  id: string
  tenant_id: string
  actor_id?: string | null
  action: string
  target_type: string
  target_id?: string | null
  payload: Record<string, unknown>
  created_at: string
}

export interface AccessLogFilters {
  actor_id?: string
  action?: string
  target_type?: string
  limit?: number
  offset?: number
}

export async function listAccessLog(filters: AccessLogFilters = {}): Promise<AccessAuditEntry[]> {
  const client = getApiClient()
  const params: Record<string, string | number> = {}
  if (filters.actor_id) params.actor_id = filters.actor_id
  if (filters.action) params.action = filters.action
  if (filters.target_type) params.target_type = filters.target_type
  if (filters.limit !== undefined) params.limit = filters.limit
  if (filters.offset !== undefined) params.offset = filters.offset
  return client.get<AccessAuditEntry[]>('access-log', params)
}

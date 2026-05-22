/**
 * Admin API surface for tenant management (superuser only).
 * Wraps /api/admin/tenants. Uses the shared apiClient that holds urlAdmin.
 */

import { getApiClient } from './entityApis'

export interface AdminTenant {
  id: string
  slug: string
  name: string
  is_active: boolean
  user_count: number
  department_count: number
  created_at?: string | null
  updated_at?: string | null
}

export interface TenantCreatePayload {
  slug: string
  name: string
  is_active?: boolean
}

export interface TenantUpdatePayload {
  slug?: string
  name?: string
  is_active?: boolean
}

export interface TenantUserSummary {
  id: string
  email?: string | null
  name?: string | null
  is_active: boolean
  is_superuser: boolean
}

export async function listTenants(): Promise<AdminTenant[]> {
  return getApiClient().get<AdminTenant[]>('tenants')
}

export async function getTenant(id: string): Promise<AdminTenant> {
  return getApiClient().get<AdminTenant>(`tenants/${id}`)
}

export async function createTenant(payload: TenantCreatePayload): Promise<AdminTenant> {
  return getApiClient().post<AdminTenant>('tenants', payload)
}

export async function updateTenant(id: string, payload: TenantUpdatePayload): Promise<AdminTenant> {
  return getApiClient().patch<AdminTenant>(`tenants/${id}`, payload)
}

export async function listTenantUsers(id: string): Promise<TenantUserSummary[]> {
  return getApiClient().get<TenantUserSummary[]>(`tenants/${id}/users`)
}

export async function moveUserToTenant(userId: string, tenantId: string): Promise<unknown> {
  return getApiClient().patch(`users/${userId}/tenant`, { tenant_id: tenantId })
}

/**
 * Admin API surface for department management.
 * Wraps /api/admin/departments and the user-department endpoints under
 * /api/admin/users/{id}/departments.
 */

import { getApiClient } from './entityApis'

export interface AdminDepartment {
  id: string
  tenant_id: string
  slug: string
  name: string
  parent_id?: string | null
  member_count: number
  created_at?: string | null
  updated_at?: string | null
}

export interface DepartmentMember {
  user_id: string
  email?: string | null
  name?: string | null
  is_lead: boolean
}

export interface AdminDepartmentDetail extends AdminDepartment {
  members: DepartmentMember[]
}

export interface DepartmentCreatePayload {
  slug: string
  name: string
  parent_id?: string | null
}

export interface DepartmentUpdatePayload {
  slug?: string
  name?: string
  parent_id?: string | null
}

export interface UserDepartmentMembership {
  department_id: string
  department_slug: string
  department_name: string
  is_lead: boolean
}

export interface UserDepartmentMembershipInput {
  department_id: string
  is_lead: boolean
}

export async function listDepartments(): Promise<AdminDepartment[]> {
  return getApiClient().get<AdminDepartment[]>('departments')
}

export async function getDepartment(id: string): Promise<AdminDepartmentDetail> {
  return getApiClient().get<AdminDepartmentDetail>(`departments/${id}`)
}

export async function createDepartment(payload: DepartmentCreatePayload): Promise<AdminDepartment> {
  return getApiClient().post<AdminDepartment>('departments', payload)
}

export async function updateDepartment(id: string, payload: DepartmentUpdatePayload): Promise<AdminDepartment> {
  return getApiClient().patch<AdminDepartment>(`departments/${id}`, payload)
}

export async function deleteDepartment(id: string): Promise<void> {
  await getApiClient().delete(`departments/${id}`)
}

export async function addDepartmentMember(
  departmentId: string,
  payload: { user_id: string; is_lead?: boolean },
): Promise<DepartmentMember> {
  return getApiClient().post<DepartmentMember>(
    `departments/${departmentId}/members`,
    payload,
  )
}

export async function updateDepartmentMember(
  departmentId: string,
  userId: string,
  is_lead: boolean,
): Promise<DepartmentMember> {
  return getApiClient().patch<DepartmentMember>(
    `departments/${departmentId}/members/${userId}`,
    { is_lead },
  )
}

export async function removeDepartmentMember(
  departmentId: string,
  userId: string,
): Promise<void> {
  await getApiClient().delete(`departments/${departmentId}/members/${userId}`)
}

// — User-side membership view —

export async function listUserDepartments(userId: string): Promise<UserDepartmentMembership[]> {
  return getApiClient().get<UserDepartmentMembership[]>(`users/${userId}/departments`)
}

export async function replaceUserDepartments(
  userId: string,
  memberships: UserDepartmentMembershipInput[],
): Promise<UserDepartmentMembership[]> {
  return getApiClient().patch<UserDepartmentMembership[]>(
    `users/${userId}/departments`,
    { memberships },
  )
}

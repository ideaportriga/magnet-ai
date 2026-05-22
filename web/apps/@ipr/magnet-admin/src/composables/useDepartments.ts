/**
 * Shared department list query for record-level access controls.
 *
 * Populates the `<access-control>` department picker (visibility='department').
 * Cached for the session so opening different details pages doesn't refetch.
 */
import { useQuery } from '@tanstack/vue-query'
import { listDepartments, type AdminDepartment } from '@/api/departments'

export function useDepartments() {
  return useQuery<AdminDepartment[]>({
    queryKey: ['departments', 'list'],
    queryFn: listDepartments,
    staleTime: 5 * 60 * 1000,
  })
}

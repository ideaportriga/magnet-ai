import { computed } from 'vue'
import { useSharedAuthStore } from '../stores/authStore'

type RecordAction = 'view' | 'edit' | 'delete' | 'share' | 'execute'

interface RecordWithPermissions {
  _permissions?: Partial<Record<RecordAction, boolean>>
}

/**
 * Permission-aware composable for UX gating.
 *
 * Backend is the only security boundary — these helpers only decide whether
 * to render/enable UI affordances. A user without the permission will still
 * be blocked by the backend if they call the endpoint directly.
 *
 * - `can(p)` / `canAny(...p)` / `canAll(...p)` — global permission checks
 *   against `userInfo.permissions` (string codes like `read:agents`).
 * - `canOn(record, action, [resourceType])` — record-level check. If the
 *   record ships a `_permissions` block (PR 8 of the access-control plan)
 *   we trust it. Otherwise we fall through to global capability for the
 *   given `resourceType` so legacy entities (not yet on the new pipeline)
 *   keep working without UX regressions.
 * - `isSuperuser` / `hasAnyAccess` — convenience flags.
 */
export default function usePermissions() {
  const store = useSharedAuthStore()

  const permissions = computed<Set<string>>(() => {
    const list = store.userInfo?.permissions ?? []
    return new Set(list)
  })

  const isSuperuser = computed<boolean>(() => Boolean(store.userInfo?.is_superuser))

  const hasAnyAccess = computed<boolean>(() => isSuperuser.value || permissions.value.size > 0)

  function can(permission: string): boolean {
    if (isSuperuser.value) return true
    return permissions.value.has(permission)
  }

  function canAny(...required: string[]): boolean {
    if (isSuperuser.value) return true
    return required.some((p) => permissions.value.has(p))
  }

  function canAll(...required: string[]): boolean {
    if (isSuperuser.value) return true
    return required.every((p) => permissions.value.has(p))
  }

  function canOn(
    record: RecordWithPermissions | null | undefined,
    action: RecordAction,
    resourceType?: string,
  ): boolean {
    if (!record) return false
    if (isSuperuser.value) return true

    const recordPerms = record._permissions
    if (recordPerms && typeof recordPerms[action] === 'boolean') {
      return recordPerms[action] === true
    }

    // Legacy / not-yet-migrated record: fall through to global capability
    // for `<action>:<resourceType>` so existing UX doesn't regress.
    if (resourceType) {
      const code = `${action === 'edit' ? 'write' : action === 'view' ? 'read' : action}:${resourceType}`
      return can(code)
    }

    // No record-level block and no resource type to map → conservative.
    return false
  }

  return {
    permissions,
    isSuperuser,
    hasAnyAccess,
    can,
    canAny,
    canAll,
    canOn,
  }
}

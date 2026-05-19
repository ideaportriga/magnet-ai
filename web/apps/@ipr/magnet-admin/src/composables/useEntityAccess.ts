import { computed, provide, type ComputedRef, type Ref } from 'vue'
import { usePermissions } from '@shared'
import { getEntityAccessConfig, type EntityAccessKey } from '@/config/entityAccess'
import type { BaseEntity } from '@/types'

type MaybeRecordRef<T extends BaseEntity> = Ref<T | null | undefined> | ComputedRef<T | null | undefined>

export function useEntityAccess<T extends BaseEntity>(
  entityKey: EntityAccessKey,
  record?: MaybeRecordRef<T>,
) {
  const config = getEntityAccessConfig(entityKey)
  const { can, canOn } = usePermissions()

  const canRead = computed(() => can(config.readPermission))
  const canCreate = computed(() => can(config.writePermission))
  const canEdit = computed(() => {
    const current = record?.value
    if (!current) return can(config.writePermission)
    return canOn(current, 'edit', config.permissionResource)
  })
  const canDelete = computed(() => {
    const current = record?.value
    if (!current) return can(config.deletePermission)

    const recordPerms = current._permissions
    if (recordPerms && typeof recordPerms.delete === 'boolean') {
      return recordPerms.delete === true
    }

    return can(config.deletePermission)
  })
  const recordReadonly = computed(() => {
    if (!record?.value) return false
    return canEdit.value === false
  })

  function provideReadonly() {
    provide(config.readonlyProvideKey, recordReadonly)
  }

  return {
    config,
    canRead,
    canCreate,
    canEdit,
    canDelete,
    recordReadonly,
    provideReadonly,
  }
}

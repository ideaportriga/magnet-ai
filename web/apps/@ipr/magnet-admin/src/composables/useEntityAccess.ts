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
  const canEdit = computed(() => canOn(record?.value, 'edit', config.permissionResource))
  const canDelete = computed(() => canOn(record?.value, 'delete', config.permissionResource))
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

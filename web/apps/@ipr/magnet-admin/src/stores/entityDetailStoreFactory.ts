/**
 * Factory for creating Pinia entity detail stores.
 *
 * These stores bridge the old component API (entity/initEntity/updateProperty) with
 * the new editBuffer system (automatic dirty tracking, diff-based save, workspace tab sync).
 *
 * Components continue to use store.entity, store.updateProperty(), etc. — no changes needed.
 * Under the hood, all mutations go through editBufferStore for proper change tracking.
 */
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { cloneDeep, isEqual, set as lodashSet, get as lodashGet } from 'lodash'
import { useEditBufferStore } from './editBufferStore'
import { useWorkspaceStore } from './workspaceStore'
import { ENTITY_READ_ONLY_FIELDS } from '@/constants/entityFields'

interface VariantRecord extends Record<string, unknown> {
  variant: string
}

interface VariantEntityData extends Record<string, unknown> {
  variants?: VariantRecord[]
  active_variant?: string | null
}

function makeBufferKey(entityName: string, entityId: string | null): string {
  return `${entityName}:${entityId}`
}

/**
 * Creates the shared base state and methods used by both simple and variant detail stores.
 */
function createBaseState(entityName: string) {
  const editBuffer = useEditBufferStore()
  const workspace = useWorkspaceStore()

  const entity = ref<Record<string, unknown> | null>(null)
  const initEntity = ref<Record<string, unknown> | null>(null)
  const _entityId = ref<string | null>(null)

  function _bufferKey(): string {
    return makeBufferKey(entityName, _entityId.value)
  }

  function _syncToBuffer() {
    if (!entity.value || !_entityId.value) return
    editBuffer.replaceDraft(_bufferKey(), entity.value)
  }

  function _syncDirtyToWorkspace() {
    if (!_entityId.value) return
    const dirty = editBuffer.isDirty(_bufferKey())
    const tab = workspace.tabs.find(
      (t) => t.entityType === entityName && t.entityId === _entityId.value,
    )
    if (tab) workspace.markDirty(tab.id, dirty)
  }

  function setEntity(data: Record<string, unknown> | null) {
    entity.value = data ? cloneDeep(data) : null
    initEntity.value = data ? cloneDeep(data) : null
    _entityId.value = data ? String((data as Record<string, unknown>).id ?? '') : null

    if (data && _entityId.value) {
      editBuffer.initBuffer(_bufferKey(), entityName, _entityId.value, data)

      // Update workspace tab label with actual entity name (replaces truncated ID fallback)
      const label = (data.name as string) || (data.system_name as string) || ''
      if (label) {
        const tab = workspace.tabs.find(
          (t) => t.entityType === entityName && t.entityId === _entityId.value,
        )
        if (tab) workspace.updateTabLabel(tab.id, label)
      }
    }
  }

  function updateProperty({ key, value }: { key: string; value: unknown }) {
    if (!entity.value) return
    entity.value = { ...entity.value, [key]: value }
    _syncToBuffer()
    _syncDirtyToWorkspace()
  }

  function updateNestedProperty({ path, value }: { path: string; value: unknown }) {
    if (!entity.value) return
    const clone = cloneDeep(entity.value)
    lodashSet(clone, path, value)
    entity.value = clone
    _syncToBuffer()
    _syncDirtyToWorkspace()
  }

  const isChanged = computed(() => {
    if (!_entityId.value) {
      if (!initEntity.value) return false
      return !isEqual(entity.value, initEntity.value)
    }
    return editBuffer.isDirty(_bufferKey())
  })

  function revert() {
    if (_entityId.value) {
      editBuffer.revertBuffer(_bufferKey())
      const draft = editBuffer.getDraft(_bufferKey())
      if (draft) entity.value = cloneDeep(draft)
    } else {
      entity.value = initEntity.value ? cloneDeep(initEntity.value) : null
    }
    _syncDirtyToWorkspace()
  }

  function setInit() {
    initEntity.value = entity.value ? cloneDeep(entity.value) : null
    if (_entityId.value) {
      editBuffer.commitBuffer(_bufferKey())
    }
    _syncDirtyToWorkspace()
  }

  function getNestedValue(path: string) {
    return entity.value ? lodashGet(entity.value, path) : undefined
  }

  function getDiff(): Record<string, unknown> {
    if (!_entityId.value) return {}
    return editBuffer.getDiff(_bufferKey())
  }

  /** Build save payload: current entity minus read-only fields */
  function buildPayload(): Record<string, unknown> | null {
    if (!entity.value) return null
    const payload = { ...entity.value }
    for (const field of ENTITY_READ_ONLY_FIELDS) delete payload[field]
    return payload
  }

  function cleanup() {
    if (_entityId.value) {
      editBuffer.removeBuffer(_bufferKey())
    }
  }

  return {
    entity,
    initEntity,
    _entityId,
    isChanged,
    setEntity,
    updateProperty,
    updateNestedProperty,
    revert,
    setInit,
    getNestedValue,
    getDiff,
    buildPayload,
    cleanup,
    _syncToBuffer,
    _syncDirtyToWorkspace,
  }
}

export function createEntityDetailStore(entityName: string) {
  return defineStore(`${entityName}Detail`, () => {
    const base = createBaseState(entityName)

    return {
      entity: base.entity,
      initEntity: base.initEntity,
      isChanged: base.isChanged,
      setEntity: base.setEntity,
      updateProperty: base.updateProperty,
      updateNestedProperty: base.updateNestedProperty,
      revert: base.revert,
      setInit: base.setInit,
      getNestedValue: base.getNestedValue,
      getDiff: base.getDiff,
      buildPayload: base.buildPayload,
      cleanup: base.cleanup,
    }
  })
}

/**
 * Factory for entities with a variant system (rag, retrieval, prompts).
 * Variants are sub-objects in `entity.variants[]` identified by `variant` key.
 */
export function createVariantDetailStore(entityName: string) {
  return defineStore(`${entityName}Detail`, () => {
    const base = createBaseState(entityName)

    const selectedVariant = ref<string | null>(null)
    const testSetItem = ref<Record<string, unknown>>({})

    // Override setEntity to also initialize selectedVariant
    const baseSetEntity = base.setEntity
    function setEntity(data: Record<string, unknown> | null) {
      baseSetEntity(data)
      selectedVariant.value = (data as VariantEntityData | null)?.active_variant ?? null
    }

    function _asVariantEntity(val: Record<string, unknown> | null): VariantEntityData | null {
      return val as VariantEntityData | null
    }

    const activeVariant = computed(() => {
      const variants = _asVariantEntity(base.entity.value)?.variants
      return variants?.find((v) => v.variant === selectedVariant.value) ?? null
    })

    function updateNestedVariantProperty({ path, value }: { path: string; value: unknown }) {
      const variants = _asVariantEntity(base.entity.value)?.variants
      if (!variants) return
      const variant = variants.find((v) => v.variant === selectedVariant.value)
      if (!variant) return

      const keys = path.split('.')
      let target: Record<string, unknown> = variant
      for (let i = 0; i < keys.length - 1; i++) {
        if (!(keys[i] in target) || target[keys[i]] === null) {
          target[keys[i]] = {}
        }
        target = target[keys[i]] as Record<string, unknown>
      }
      const lastKey = keys[keys.length - 1]
      if (value === null) {
        delete target[lastKey]
      } else {
        target[lastKey] = value
      }
      base.entity.value = { ...base.entity.value! }
      base._syncToBuffer()
      base._syncDirtyToWorkspace()
    }

    function setSelectedVariant(variantKey: string | null) {
      selectedVariant.value = variantKey
    }

    function createVariant() {
      const entityData = _asVariantEntity(base.entity.value)
      if (!entityData) return
      const variants = entityData.variants ?? []
      const baseVariant = variants.find((v) => v.variant === selectedVariant.value)
      const maxNum = variants.reduce((max, v) => {
        const num = parseInt(String(v.variant).split('_')[1]) || 0
        return Math.max(max, num)
      }, 0)
      const newKey = `variant_${maxNum + 1}`
      const newVariant = baseVariant
        ? { ...cloneDeep(baseVariant), variant: newKey, description: '' }
        : { variant: newKey }
      variants.push(newVariant)
      entityData.variants = [...variants]
      selectedVariant.value = newKey
      base._syncToBuffer()
      base._syncDirtyToWorkspace()
    }

    function deleteVariant() {
      const entityData = _asVariantEntity(base.entity.value)
      if (!entityData) return
      const variants = entityData.variants ?? []
      if (variants.length <= 1) return
      const idx = variants.findIndex((v) => v.variant === selectedVariant.value)
      if (idx === -1) return
      const isActive = selectedVariant.value === entityData.active_variant
      variants.splice(idx, 1)
      const newIdx = idx === 0 ? 0 : idx - 1
      selectedVariant.value = String(variants[newIdx].variant)
      if (isActive) entityData.active_variant = selectedVariant.value
      entityData.variants = [...variants]
      base._syncToBuffer()
      base._syncDirtyToWorkspace()
    }

    function activateVariant() {
      const entityData = _asVariantEntity(base.entity.value)
      if (!entityData) return
      entityData.active_variant = selectedVariant.value
      base._syncToBuffer()
      base._syncDirtyToWorkspace()
    }

    // Override revert to also reset selectedVariant
    function revert() {
      base.revert()
      selectedVariant.value = (base.initEntity.value as VariantEntityData | null)?.active_variant ?? null
    }

    return {
      entity: base.entity,
      initEntity: base.initEntity,
      selectedVariant,
      activeVariant,
      testSetItem,
      isChanged: base.isChanged,
      setEntity,
      updateProperty: base.updateProperty,
      updateNestedProperty: base.updateNestedProperty,
      updateNestedVariantProperty,
      setSelectedVariant,
      createVariant,
      deleteVariant,
      activateVariant,
      revert,
      setInit: base.setInit,
      getDiff: base.getDiff,
      buildPayload: base.buildPayload,
      cleanup: base.cleanup,
    }
  })
}

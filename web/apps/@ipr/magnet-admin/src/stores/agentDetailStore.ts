/**
 * Pinia store replacing Vuex agentDetail module.
 * Extends the variant pattern with agent-specific state (activeTopic, conversation_id).
 */
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { cloneDeep, isEqual, set as lodashSet, get as lodashGet } from 'lodash'
import { useEditBufferStore } from './editBufferStore'
import { useWorkspaceStore } from './workspaceStore'

const ENTITY_NAME = 'agentDetail'
const READ_ONLY_FIELDS = ['id', 'created_at', 'updated_at', 'created_by', 'updated_by']

export const useAgentDetailStore = defineStore('agentDetail', () => {
  const editBuffer = useEditBufferStore()
  const workspace = useWorkspaceStore()

  const entity = ref<Record<string, any> | null>(null)
  const initEntity = ref<Record<string, any> | null>(null)
  const selectedVariant = ref<string | null>(null)
  const testSetItem = ref<Record<string, unknown>>({})
  const activeTopic = ref<Record<string, any> | null>(null)
  const conversationId = ref<string | null>(null)
  const _entityId = ref<string | null>(null)

  function _bufferKey(): string {
    return `${ENTITY_NAME}:${_entityId.value}`
  }

  function _syncToBuffer() {
    if (!entity.value || !_entityId.value) return
    editBuffer.replaceDraft(_bufferKey(), entity.value)
  }

  function _syncDirtyToWorkspace() {
    if (!_entityId.value) return
    const dirty = editBuffer.isDirty(_bufferKey())
    const tab = workspace.tabs.find(
      (t) => t.entityType === ENTITY_NAME && t.entityId === _entityId.value,
    )
    if (tab) workspace.markDirty(tab.id, dirty)
  }

  function setEntity(data: Record<string, any> | null) {
    entity.value = data ? cloneDeep(data) : null
    initEntity.value = data ? cloneDeep(data) : null
    selectedVariant.value = data?.active_variant ?? null
    testSetItem.value = {}
    activeTopic.value = null
    _entityId.value = data ? String(data.id ?? '') : null

    if (data && _entityId.value) {
      editBuffer.initBuffer(_bufferKey(), ENTITY_NAME, _entityId.value, data)
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

  /** Update at agent_detail top level (not within variant) */
  function updateHighLevelNestedProperty({ path, value }: { path: string; value: unknown }) {
    if (!entity.value) return
    const keys = path.split('.')
    let target: any = entity.value
    for (let i = 0; i < keys.length - 1; i++) {
      if (!(keys[i] in target) || target[keys[i]] === null) {
        target[keys[i]] = {}
      }
      target = target[keys[i]]
    }
    const lastKey = keys[keys.length - 1]
    if (value === null) {
      delete target[lastKey]
    } else {
      target[lastKey] = value
    }
    entity.value = { ...entity.value }
    _syncToBuffer()
    _syncDirtyToWorkspace()
  }

  const activeVariant = computed(() => {
    return entity.value?.variants?.find((v: any) => v.variant === selectedVariant.value) ?? null
  })

  /** Update nested within the active variant's .value object */
  function updateNestedVariantProperty({ path, value }: { path: string; value: unknown }) {
    const variant = entity.value?.variants?.find((v: any) => v.variant === selectedVariant.value)
    if (!variant) return
    const target = variant.value ?? variant
    const keys = path.split('.')
    let obj: any = target
    for (let i = 0; i < keys.length - 1; i++) {
      if (!(keys[i] in obj) || obj[keys[i]] === null) {
        obj[keys[i]] = {}
      }
      obj = obj[keys[i]]
    }
    const lastKey = keys[keys.length - 1]
    if (value === null) {
      delete obj[lastKey]
    } else {
      obj[lastKey] = value
    }
    entity.value = { ...entity.value! }
    _syncToBuffer()
    _syncDirtyToWorkspace()
  }

  /** Complex mutation: update a list item by system_name within the variant */
  function updateNestedListItemBySystemName({
    arrayPath,
    itemSystemName,
    subArrayKey,
    subItemSystemName,
    data,
  }: {
    arrayPath: string
    itemSystemName: string
    subArrayKey?: string
    subItemSystemName?: string
    data: Record<string, any>
  }) {
    const variant = entity.value?.variants?.find((v: any) => v.variant === selectedVariant.value)
    if (!variant) return

    const itemsArray = lodashGet(variant.value ?? variant, arrayPath)
    if (!Array.isArray(itemsArray)) return

    const item = itemsArray.find((el: any) => el.system_name === itemSystemName)
    if (!item) return

    if (subArrayKey && subItemSystemName) {
      const subItems = item[subArrayKey]
      if (!Array.isArray(subItems)) return
      const subItem = subItems.find((el: any) => el.system_name === subItemSystemName)
      if (!subItem) return
      Object.assign(item, { metadata: { ...item.metadata, modified_at: new Date().toISOString() } })
      Object.assign(subItem, { ...data, metadata: { ...subItem.metadata, modified_at: new Date().toISOString() } })
    } else {
      Object.assign(item, { ...data, metadata: { ...item.metadata, modified_at: new Date().toISOString() } })
    }
    entity.value = { ...entity.value! }
    _syncToBuffer()
    _syncDirtyToWorkspace()
  }

  function setSelectedVariant(key: string | null) {
    selectedVariant.value = key
  }

  function createVariant() {
    if (!entity.value) return
    const variants = entity.value.variants ?? []
    const base = variants.find((v: any) => v.variant === selectedVariant.value)
    const maxNum = variants.reduce((max: number, v: any) => Math.max(max, parseInt(String(v.variant).split('_')[1]) || 0), 0)
    const newKey = `variant_${maxNum + 1}`
    const newVariant = base ? { ...cloneDeep(base), variant: newKey, description: '' } : { variant: newKey }
    variants.push(newVariant)
    entity.value = { ...entity.value, variants: [...variants] }
    selectedVariant.value = newKey
    _syncToBuffer()
    _syncDirtyToWorkspace()
  }

  function deleteVariant() {
    if (!entity.value) return
    const variants = entity.value.variants ?? []
    if (variants.length <= 1) return
    const idx = variants.findIndex((v: any) => v.variant === selectedVariant.value)
    if (idx === -1) return
    const isActive = selectedVariant.value === entity.value.active_variant
    variants.splice(idx, 1)
    const newIdx = idx === 0 ? 0 : idx - 1
    selectedVariant.value = String(variants[newIdx].variant)
    if (isActive) entity.value.active_variant = selectedVariant.value
    entity.value = { ...entity.value, variants: [...variants] }
    _syncToBuffer()
    _syncDirtyToWorkspace()
  }

  function activateVariant() {
    if (!entity.value) return
    entity.value = { ...entity.value, active_variant: selectedVariant.value }
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
    selectedVariant.value = initEntity.value?.active_variant ?? null
    activeTopic.value = null
    _syncDirtyToWorkspace()
  }

  function setInit() {
    initEntity.value = entity.value ? cloneDeep(entity.value) : null
    if (_entityId.value) {
      editBuffer.commitBuffer(_bufferKey())
    }
    testSetItem.value = {}
    activeTopic.value = null
    _syncDirtyToWorkspace()
  }

  function getDiff(): Record<string, unknown> {
    if (!_entityId.value) return {}
    return editBuffer.getDiff(_bufferKey())
  }

  function buildPayload(): Record<string, unknown> | null {
    if (!entity.value) return null
    const payload = { ...entity.value }
    for (const field of READ_ONLY_FIELDS) delete payload[field]
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
    selectedVariant,
    activeVariant,
    testSetItem,
    activeTopic,
    conversationId,
    isChanged,
    setEntity,
    updateProperty,
    updateNestedProperty,
    updateHighLevelNestedProperty,
    updateNestedVariantProperty,
    updateNestedListItemBySystemName,
    setSelectedVariant,
    createVariant,
    deleteVariant,
    activateVariant,
    revert,
    setInit,
    getDiff,
    buildPayload,
    cleanup,
  }
})

import { ref } from 'vue'
import { cloneDeep, get as lodashGet } from 'lodash'
import { useVariantEntityDetail, type UseVariantEntityDetailOptions } from './useVariantEntityDetail'
import type { VariantEntity } from './useVariantEntityDetail'

export interface AgentEntity extends VariantEntity {
  [key: string]: unknown
}

/**
 * Composable for agents — extends useVariantEntityDetail with agent-specific operations:
 * - activeTopic / conversationId refs
 * - updateHighLevelNestedProperty (agent-level, not variant-level)
 * - updateNestedListItemBySystemName (complex variant mutation)
 */
export function useAgentEntityDetail(options?: UseVariantEntityDetailOptions) {
  const activeTopic = ref<Record<string, unknown> | null>(null)
  const conversationId = ref<string | null>(null)

  const base = useVariantEntityDetail<AgentEntity>('agents', {
    ...options,
    onBufferInit(data) {
      activeTopic.value = null
      conversationId.value = null
      options?.onBufferInit?.(data)
    },
  })

  /**
   * Update nested property at agent top-level (not within variant).
   * E.g. updateHighLevelNestedProperty('metadata.tags', [...])
   */
  function updateHighLevelNestedProperty(path: string, value: unknown) {
    const d = base.draft.value
    if (!d) return
    const keys = path.split('.')
    const clone = cloneDeep(d)
    let target: Record<string, unknown> = clone
    for (let i = 0; i < keys.length - 1; i++) {
      if (!(keys[i] in target) || target[keys[i]] === null || typeof target[keys[i]] !== 'object') {
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
    base.editBuffer.replaceDraft(base.bufferKey.value, clone)
  }

  /**
   * Complex mutation: update a list item matched by system_name within the active variant.
   * Supports nested sub-arrays via subArrayKey + subItemSystemName.
   * Updates metadata.modified_at timestamps automatically.
   */
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
    data: Record<string, unknown>
  }) {
    const d = base.draft.value
    if (!d?.variants) return
    const variantsList = d.variants as Record<string, unknown>[]
    const variantIdx = variantsList.findIndex((v) => v.variant === base.selectedVariant.value)
    if (variantIdx === -1) return

    const variant = cloneDeep(variantsList[variantIdx])
    const variantData = (variant.value ?? variant) as Record<string, unknown>
    const itemsArray = lodashGet(variantData, arrayPath) as Record<string, unknown>[] | undefined
    if (!Array.isArray(itemsArray)) return

    const item = itemsArray.find((el) => el.system_name === itemSystemName)
    if (!item) return

    if (subArrayKey && subItemSystemName) {
      const subItems = item[subArrayKey] as Record<string, unknown>[] | undefined
      if (!Array.isArray(subItems)) return
      const subItem = subItems.find((el) => el.system_name === subItemSystemName)
      if (!subItem) return
      Object.assign(item, { metadata: { ...(item.metadata as Record<string, unknown>), modified_at: new Date().toISOString() } })
      Object.assign(subItem, { ...data, metadata: { ...(subItem.metadata as Record<string, unknown>), modified_at: new Date().toISOString() } })
    } else {
      Object.assign(item, { ...data, metadata: { ...(item.metadata as Record<string, unknown>), modified_at: new Date().toISOString() } })
    }

    const allVariants = [...variantsList]
    allVariants[variantIdx] = variant
    base.editBuffer.updateDraft(base.bufferKey.value, 'variants', allVariants)
  }

  function revert() {
    base.revert()
    activeTopic.value = null
    conversationId.value = null
  }

  return {
    ...base,
    activeTopic,
    conversationId,
    updateHighLevelNestedProperty,
    updateNestedListItemBySystemName,
    revert,
  }
}

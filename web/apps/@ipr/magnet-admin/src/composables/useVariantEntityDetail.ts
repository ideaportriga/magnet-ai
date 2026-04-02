import { computed, ref, watch } from 'vue'
import { cloneDeep } from 'lodash'
import type { AllEntityQueries } from '@/queries/entities'
import type { BaseEntity } from '@/types'
import { useEntityDetailBase, type UseEntityDetailBaseOptions } from './useEntityDetailBase'

export interface VariantEntity extends BaseEntity {
  variants?: Record<string, unknown>[]
  active_variant?: string | null
}

export type UseVariantEntityDetailOptions = UseEntityDetailBaseOptions

/**
 * Composable for entities with a variant system (rag_tools, retrieval, promptTemplates, agents).
 *
 * Extends useEntityDetailBase with variant-specific operations:
 * - selectedVariant / activeVariant
 * - updateVariantField
 * - createVariant / deleteVariant / activateVariant
 */
export function useVariantEntityDetail<T extends VariantEntity>(
  entityKey: keyof AllEntityQueries,
  options?: UseVariantEntityDetailOptions,
) {
  const selectedVariant = ref<string | null>(null)
  const testSetItem = ref<Record<string, unknown>>({})

  const base = useEntityDetailBase<T>(entityKey, {
    ...options,
    onBufferInit(data) {
      selectedVariant.value = (data.active_variant as string) ?? null
      options?.onBufferInit?.(data)
    },
  })

  // Initialize selectedVariant when draft becomes available (covers keep-alive reactivation
  // and cases where the buffer already exists but selectedVariant was reset)
  watch(
    base.draft,
    (d) => {
      if (d && selectedVariant.value === null) {
        selectedVariant.value = (d.active_variant as string) ?? null
      }
    },
    { immediate: true },
  )

  // Variant accessors
  const activeVariant = computed(() => {
    const variantsList = base.draft.value?.variants as Record<string, unknown>[] | undefined
    return variantsList?.find((v) => v.variant === selectedVariant.value) ?? null
  })

  const variants = computed(() => {
    return (base.draft.value?.variants ?? []) as Record<string, unknown>[]
  })

  // Variant field updates
  function updateVariantField(path: string, value: unknown) {
    const d = base.draft.value
    if (!d?.variants) return
    const variantsList = [...(d.variants as Record<string, unknown>[])]
    const idx = variantsList.findIndex((v) => v.variant === selectedVariant.value)
    if (idx === -1) return
    const updatedVariant = cloneDeep(variantsList[idx])

    const keys = path.split('.')
    let target: Record<string, unknown> = updatedVariant
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

    variantsList[idx] = updatedVariant
    base.editBuffer.updateDraft(base.bufferKey.value, 'variants', variantsList)
  }

  function setSelectedVariant(variantKey: string | null) {
    selectedVariant.value = variantKey
  }

  function createVariant() {
    const d = base.draft.value
    if (!d) return
    const variantsList = [...(d.variants as Record<string, unknown>[] ?? [])]
    const baseVariant = variantsList.find((v) => v.variant === selectedVariant.value)
    const maxNum = variantsList.reduce((max, v) => {
      const num = parseInt(String(v.variant).split('_')[1]) || 0
      return Math.max(max, num)
    }, 0)
    const newKey = `variant_${maxNum + 1}`
    const newVariant = baseVariant
      ? { ...cloneDeep(baseVariant), variant: newKey, description: '' }
      : { variant: newKey }
    variantsList.push(newVariant)
    base.editBuffer.updateDraft(base.bufferKey.value, 'variants', variantsList)
    selectedVariant.value = newKey
  }

  function deleteVariant() {
    const d = base.draft.value
    if (!d) return
    const variantsList = [...(d.variants as Record<string, unknown>[] ?? [])]
    if (variantsList.length <= 1) return
    const idx = variantsList.findIndex((v) => v.variant === selectedVariant.value)
    if (idx === -1) return
    const isActive = selectedVariant.value === d.active_variant
    variantsList.splice(idx, 1)
    const newIdx = idx === 0 ? 0 : idx - 1
    selectedVariant.value = String(variantsList[newIdx].variant)
    if (isActive) {
      base.editBuffer.updateDraft(base.bufferKey.value, 'active_variant', selectedVariant.value)
    }
    base.editBuffer.updateDraft(base.bufferKey.value, 'variants', variantsList)
  }

  function activateVariant() {
    base.editBuffer.updateDraft(base.bufferKey.value, 'active_variant', selectedVariant.value)
  }

  function revert() {
    base.revert()
    const original = base.editBuffer.getOriginal(base.bufferKey.value)
    selectedVariant.value = (original as Record<string, unknown> | undefined)?.active_variant as string ?? null
  }

  return {
    // Server data
    data: base.data,
    // Form state
    draft: base.draft,
    id: base.id,
    bufferKey: base.bufferKey,
    isLoading: base.isLoading,
    isDirty: base.isDirty,
    // Variant state
    selectedVariant,
    activeVariant,
    variants,
    testSetItem,
    // Field updates
    updateField: base.updateField,
    updateFields: base.updateFields,
    updateVariantField,
    // Variant operations
    setSelectedVariant,
    createVariant,
    deleteVariant,
    activateVariant,
    // Save / Revert / Delete
    revert,
    save: base.save,
    remove: base.remove,
    refetch: base.refetch,
    buildPayload: base.buildPayload,
    // Advanced: direct access for extending composables
    editBuffer: base.editBuffer,
  }
}

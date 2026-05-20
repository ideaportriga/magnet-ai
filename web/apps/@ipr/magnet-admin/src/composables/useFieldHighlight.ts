/**
 * `useFieldHighlight` — small composable that tells a form field whether
 * it currently carries an unsaved change.
 *
 *   const { isChanged, isAiSuggested, tone } = useFieldHighlight(
 *     bufferKey, 'variants.0.value.settings.welcome_message'
 *   )
 *
 * `bufferKey` follows the convention used by `entityDetailStoreFactory`
 * (`<entityName>:<entityId>`). The composable returns reactive computeds
 * that re-evaluate whenever the editBuffer state changes.
 *
 * `tone` is provided as a convenience so the consuming component can do:
 *
 *   <q-input :class="{
 *     'field--ai': fieldHighlight.tone === 'ai',
 *     'field--manual': fieldHighlight.tone === 'manual',
 *   }" />
 */

import { computed, type ComputedRef } from 'vue'
import { useEditBufferStore } from '@/stores/editBufferStore'

export type HighlightTone = 'none' | 'manual' | 'ai'

export interface FieldHighlight {
  /** Path differs from the entity's original (== unsaved). */
  isChanged: ComputedRef<boolean>
  /** Path was set by the most recent AI suggestion. */
  isAiSuggested: ComputedRef<boolean>
  /** Highest-priority tone for the field. `'ai'` wins over `'manual'`. */
  tone: ComputedRef<HighlightTone>
}

export function useFieldHighlight(
  bufferKey: string,
  path: string,
): FieldHighlight {
  const buffer = useEditBufferStore()

  const isAiSuggested = computed(() =>
    buffer.getAiSuggestedPaths(bufferKey).has(path),
  )

  const isChanged = computed(() => buffer.getChangedPaths(bufferKey).has(path))

  const tone = computed<HighlightTone>(() => {
    if (isAiSuggested.value) return 'ai'
    if (isChanged.value) return 'manual'
    return 'none'
  })

  return { isChanged, isAiSuggested, tone }
}

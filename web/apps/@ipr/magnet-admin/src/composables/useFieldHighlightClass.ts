/**
 * Convenience wrapper over `useFieldHighlight` that returns a ready-to-bind
 * object of CSS classes. Drop directly into a form input:
 *
 *   <km-input v-model="draft.name" :class="highlightClasses" />
 *
 *   const highlightClasses = useFieldHighlightClass(bufferKey, 'name')
 *
 * Two classes are emitted (active at most one at a time):
 *   - `field--ai-suggested` — value differs from the previous draft
 *      and matches what the AI just suggested.
 *   - `field--unsaved`      — value differs from `original` (manual edit
 *      or AI suggestion the user kept).
 *
 * CSS for those classes lives in `assets/field-highlight.css` so it's
 * available everywhere without per-component plumbing.
 */

import { computed, type ComputedRef } from 'vue'
import { useFieldHighlight } from './useFieldHighlight'

export function useFieldHighlightClass(
  bufferKey: string,
  path: string,
): ComputedRef<Record<string, boolean>> {
  const { isChanged, isAiSuggested } = useFieldHighlight(bufferKey, path)
  return computed(() => ({
    'field--ai-suggested': isAiSuggested.value,
    'field--unsaved': isChanged.value,
  }))
}

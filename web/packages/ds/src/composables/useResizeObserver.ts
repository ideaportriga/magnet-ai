/**
 * Element-size observer — replacement for Quasar `<q-resize-observer>` and
 * `QResizeObserver`. Built on top of `@vueuse/core`'s `useResizeObserver`.
 *
 * Usage:
 *
 *   const root = ref<HTMLElement | null>(null)
 *   const { width, height } = useElementSize(root)
 */

import { useResizeObserver as vuseResizeObserver } from '@vueuse/core'
import { ref, type Ref } from 'vue'

export interface UseElementSizeReturn {
  width: Ref<number>
  height: Ref<number>
  /** Stops the underlying ResizeObserver. Call when the consumer unmounts. */
  stop: () => void
}

export function useElementSize(target: Ref<HTMLElement | null | undefined>): UseElementSizeReturn {
  const width = ref(0)
  const height = ref(0)

  const { stop } = vuseResizeObserver(target, (entries) => {
    const entry = entries[0]
    if (!entry) return
    const rect = entry.contentRect
    width.value = rect.width
    height.value = rect.height
  })

  return { width, height, stop }
}

/** Re-export the @vueuse primitive for callers that need the raw API. */
export { vuseResizeObserver as useResizeObserver }

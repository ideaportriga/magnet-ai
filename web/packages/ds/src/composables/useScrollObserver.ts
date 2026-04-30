/**
 * Scroll observer — replacement for Quasar `<q-scroll-observer>` /
 * `QScrollObserver`. Watches scroll position on a target element (or the
 * window when no target is given) and exposes reactive position values plus
 * direction.
 */

import { useEventListener } from '@vueuse/core'
import { ref, type Ref } from 'vue'

export type ScrollDirection = 'up' | 'down' | 'left' | 'right' | 'idle'

export interface UseScrollObserverReturn {
  scrollX: Ref<number>
  scrollY: Ref<number>
  directionY: Ref<ScrollDirection>
  directionX: Ref<ScrollDirection>
}

export function useScrollObserver(
  target?: Ref<HTMLElement | Window | null | undefined>,
): UseScrollObserverReturn {
  const scrollX = ref(0)
  const scrollY = ref(0)
  const directionX = ref<ScrollDirection>('idle')
  const directionY = ref<ScrollDirection>('idle')

  let lastX = 0
  let lastY = 0

  const handler = (event: Event) => {
    const el = event.target instanceof HTMLElement ? event.target : window
    const x = el === window ? window.scrollX : (el as HTMLElement).scrollLeft
    const y = el === window ? window.scrollY : (el as HTMLElement).scrollTop

    directionX.value = x === lastX ? 'idle' : x > lastX ? 'right' : 'left'
    directionY.value = y === lastY ? 'idle' : y > lastY ? 'down' : 'up'

    scrollX.value = x
    scrollY.value = y
    lastX = x
    lastY = y
  }

  useEventListener(target ?? (typeof window !== 'undefined' ? window : null), 'scroll', handler, {
    passive: true,
  })

  return { scrollX, scrollY, directionX, directionY }
}

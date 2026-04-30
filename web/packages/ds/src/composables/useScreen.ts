/**
 * Reactive viewport breakpoint helpers — replacement for Quasar's
 * `$q.screen` / `useQuasar().screen` API.
 *
 * Breakpoints align with the design-system spacing rather than Quasar's
 * (Quasar: xs<600 / sm<1024 / md<1440 / lg<1920 / xl≥1920). New breakpoints:
 *
 *   xs <  480   phone portrait
 *   sm <  768   phone landscape / small tablet
 *   md < 1024   tablet
 *   lg < 1280   small desktop
 *   xl < 1536   large desktop
 *  2xl ≥ 1536   wide desktop
 */

import { useMediaQuery } from '@vueuse/core'
import { computed, type ComputedRef } from 'vue'

export type DsBreakpoint = 'xs' | 'sm' | 'md' | 'lg' | 'xl' | '2xl'

const BREAKPOINTS: Record<DsBreakpoint, number> = {
  xs: 0,
  sm: 480,
  md: 768,
  lg: 1024,
  xl: 1280,
  '2xl': 1536,
}

export interface UseScreenReturn {
  /** Window width in CSS pixels. */
  width: ComputedRef<number>
  /** Active breakpoint (largest threshold the viewport exceeds). */
  breakpoint: ComputedRef<DsBreakpoint>
  /** True when viewport ≥ given breakpoint. Mirrors `$q.screen.gt.<bp>`. */
  isAtLeast: (bp: DsBreakpoint) => ComputedRef<boolean>
  /** True when viewport < given breakpoint. Mirrors `$q.screen.lt.<bp>`. */
  isLessThan: (bp: DsBreakpoint) => ComputedRef<boolean>
}

export function useScreen(): UseScreenReturn {
  const isLg = useMediaQuery(`(min-width: ${BREAKPOINTS.lg}px)`)
  const isMd = useMediaQuery(`(min-width: ${BREAKPOINTS.md}px)`)
  const isSm = useMediaQuery(`(min-width: ${BREAKPOINTS.sm}px)`)
  const isXl = useMediaQuery(`(min-width: ${BREAKPOINTS.xl}px)`)
  const is2xl = useMediaQuery(`(min-width: ${BREAKPOINTS['2xl']}px)`)

  const width = computed(() => {
    if (typeof window === 'undefined') return 0
    return window.innerWidth
  })

  const breakpoint = computed<DsBreakpoint>(() => {
    if (is2xl.value) return '2xl'
    if (isXl.value) return 'xl'
    if (isLg.value) return 'lg'
    if (isMd.value) return 'md'
    if (isSm.value) return 'sm'
    return 'xs'
  })

  const isAtLeast = (bp: DsBreakpoint): ComputedRef<boolean> =>
    computed(() => width.value >= BREAKPOINTS[bp])

  const isLessThan = (bp: DsBreakpoint): ComputedRef<boolean> =>
    computed(() => width.value < BREAKPOINTS[bp])

  return { width, breakpoint, isAtLeast, isLessThan }
}

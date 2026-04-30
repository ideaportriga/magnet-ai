/**
 * @ds composables barrel.
 *
 * Notify / Dialog / Loading composables are added in dedicated files when
 * the matching hosts come online (see `../hosts/`).
 */

export { useScreen } from './useScreen'
export type { DsBreakpoint, UseScreenReturn } from './useScreen'

export { useDarkMode } from './useDarkMode'
export type { DsThemeMode } from './useDarkMode'

export { useElementSize, useResizeObserver } from './useResizeObserver'
export type { UseElementSizeReturn } from './useResizeObserver'

export { useScrollObserver } from './useScrollObserver'
export type { ScrollDirection, UseScrollObserverReturn } from './useScrollObserver'

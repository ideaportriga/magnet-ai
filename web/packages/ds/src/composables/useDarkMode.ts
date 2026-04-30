/**
 * Dark mode toggle that syncs `data-theme` on `<html>` with localStorage and
 * the OS-level `prefers-color-scheme` media query.
 *
 * Replaces ad-hoc Quasar `Dark.set(...)` usage.
 */

import { useLocalStorage, usePreferredDark } from '@vueuse/core'
import { computed, watch } from 'vue'

export type DsThemeMode = 'light' | 'dark' | 'auto'

const STORAGE_KEY = 'ds:theme'

export function useDarkMode() {
  const stored = useLocalStorage<DsThemeMode>(STORAGE_KEY, 'auto')
  const prefersDark = usePreferredDark()

  const isDark = computed(() =>
    stored.value === 'dark' || (stored.value === 'auto' && prefersDark.value),
  )

  const apply = () => {
    if (typeof document === 'undefined') return
    const target = isDark.value ? 'dark' : 'light'
    document.documentElement.dataset.theme = target
    document.documentElement.style.colorScheme = target
    document.body.dataset.colorMode = target
  }

  watch(isDark, apply, { immediate: true })

  const setMode = (mode: DsThemeMode) => {
    stored.value = mode
  }

  const toggle = () => {
    setMode(isDark.value ? 'light' : 'dark')
  }

  return {
    mode: stored,
    isDark,
    setMode,
    toggle,
  }
}

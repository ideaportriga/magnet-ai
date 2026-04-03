/**
 * Vue 3 reactivity wrapper for Paraglide JS locale management.
 *
 * Paraglide JS manages locale persistence via its own strategy (cookie, etc.).
 * This composable adds Vue reactivity on top:
 * - Exposes the current locale as a reactive `ref`
 * - Provides a `setLocale` function that updates both Paraglide and Vue state
 *
 * Usage:
 *   import { useLocale } from '@shared/i18n/useLocale'
 *   const { locale, setLocale, locales } = useLocale()
 */

import { ref, readonly, type Ref, type DeepReadonly } from 'vue'

interface ParaglideRuntime {
  getLocale: () => string
  setLocale: (locale: string, options?: { reload?: boolean }) => void
  locales: readonly string[]
}

// Singleton reactive state shared across all component instances
let _locale: Ref<string> | null = null
let _runtime: ParaglideRuntime | null = null

/**
 * Initialise the locale system. Call once during app startup,
 * after Paraglide has been compiled (i.e. the runtime module is available).
 */
export function initLocale(runtime: ParaglideRuntime): void {
  _runtime = runtime
  // Paraglide resolves locale from its own strategy (cookie → globalVariable → baseLocale).
  // We just read the resolved value and make it reactive for Vue.
  _locale = ref(runtime.getLocale())
}

/**
 * Vue composable that provides reactive locale state.
 */
export function useLocale(): {
  locale: DeepReadonly<Ref<string>>
  setLocale: (newLocale: string) => void
  locales: readonly string[]
} {
  if (!_runtime || !_locale) {
    throw new Error('[i18n] initLocale() must be called before useLocale(). Did you forget to call it in main.js?')
  }

  const runtime = _runtime
  const locale = _locale

  function setLocale(newLocale: string) {
    if (!(runtime.locales as readonly string[]).includes(newLocale)) {
      console.warn(`[i18n] Unknown locale "${newLocale}". Available: ${runtime.locales.join(', ')}`)
      return
    }
    // Paraglide's setLocale persists to cookie automatically via its strategy.
    // { reload: false } prevents page reload — Vue reactivity handles re-rendering.
    runtime.setLocale(newLocale, { reload: false })
    locale.value = newLocale
  }

  return {
    locale: readonly(locale),
    setLocale,
    locales: runtime.locales,
  }
}

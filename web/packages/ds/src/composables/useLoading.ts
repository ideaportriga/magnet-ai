/**
 * `useLoading` — global loading overlay (replacement for Quasar's
 * `Loading.show()` / `Loading.hide()`).
 *
 *   const loading = useLoading()
 *   const hide = loading.show({ message: 'Saving…' })
 *   try { await save() } finally { hide() }
 *
 * Counter-based: many concurrent callers stay safe — the overlay disappears
 * only when every caller has hidden their request.
 */

import { showLoading, clearLoading, type LoadingShowOptions } from '../hosts/loadingStore'

export function useLoading() {
  return {
    show: (options?: LoadingShowOptions) => showLoading(options),
    /** Force-clear the overlay regardless of pending callers. Use sparingly. */
    clear: clearLoading,
  }
}

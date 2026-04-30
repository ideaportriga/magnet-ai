/**
 * Global loading overlay store. `useLoading().show()` increments a counter
 * and returns a `hide` function; the overlay stays visible until every
 * caller has hidden their request. This avoids the bug where two parallel
 * `show()`/`hide()` calls cancel each other.
 */

import { reactive, readonly } from 'vue'

interface LoadingState {
  pending: number
  message: string | null
}

const state = reactive<LoadingState>({ pending: 0, message: null })

export interface LoadingShowOptions {
  message?: string
}

export function showLoading(options: LoadingShowOptions = {}): () => void {
  state.pending += 1
  if (options.message != null) state.message = options.message
  let cleared = false
  return () => {
    if (cleared) return
    cleared = true
    state.pending = Math.max(0, state.pending - 1)
    if (state.pending === 0) state.message = null
  }
}

export function clearLoading(): void {
  state.pending = 0
  state.message = null
}

export const loadingState = readonly(state) as Readonly<LoadingState>

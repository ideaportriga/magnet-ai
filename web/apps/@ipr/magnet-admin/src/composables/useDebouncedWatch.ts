import { onBeforeUnmount, watch, type WatchSource, type WatchOptions } from 'vue'

/**
 * `watch()` + debounce + guaranteed teardown on unmount (§C.3).
 *
 * Replaces the pattern:
 *   watch(filter, refetch, { deep: true })
 * which fires refetch on every keystroke of a multi-field filter.
 *
 * Guarantees:
 * - At most one pending timer per instance.
 * - onBeforeUnmount clears the timer so the callback never fires after
 *   the component is gone (silent "Cannot read properties of undefined"
 *   bugs when the callback touches refs that got disposed).
 */
export function useDebouncedWatch<T>(
  source: WatchSource<T> | WatchSource<T>[],
  callback: (value: T, oldValue: T | undefined) => void,
  delayMs = 250,
  options: WatchOptions = { deep: true },
) {
  let timer: ReturnType<typeof setTimeout> | null = null

  const stop = watch(
    source as WatchSource<T>,
    (value, oldValue) => {
      if (timer) clearTimeout(timer)
      timer = setTimeout(() => {
        timer = null
        callback(value as T, oldValue as T | undefined)
      }, delayMs)
    },
    options,
  )

  onBeforeUnmount(() => {
    if (timer) clearTimeout(timer)
    stop()
  })

  return stop
}

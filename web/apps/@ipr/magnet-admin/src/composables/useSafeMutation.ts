/**
 * Wrap a TanStack Query `useMutation(...)` result with an always-safe
 * `run(vars)` that never throws, always resets loading state, and shows
 * a consistent notification on failure (§B.8).
 *
 * Typical bug this fixes:
 *   const { mutateAsync: createFoo } = queries.foo.useCreate()
 *   async function save() {
 *     saving.value = true
 *     const res = await createFoo(draft)   // throws on 500
 *     // saving.value stays `true` forever; user sees a disabled button.
 *     ...
 *   }
 *
 * After migration:
 *   const createFoo = useSafeMutation(queries.foo.useCreate(), {
 *     successMessage: m.notify_savedSuccessfully(),
 *   })
 *   async function save() {
 *     const { success, data } = await createFoo.run(draft)
 *     if (success) { /* happy path using `data` *‍/ }
 *   }
 *
 * `createFoo.isLoading` / `createFoo.error` are already reactive; no
 * manual `saving.value = false` in a `finally`, no silent swallow.
 *
 * Keep the underlying mutation object accessible as `.mutation` for the
 * rare cases where you need cache-aware helpers (`.reset()`, etc.).
 */

import { ref, type Ref } from 'vue'
import { useNotify } from './useNotify'

// Structural subset of TanStack's UseMutationReturnType we actually rely
// on; avoids coupling to a specific TanStack version's type.
interface MutationLike<TData, TVariables> {
  mutateAsync: (variables: TVariables) => Promise<TData>
}

export interface UseSafeMutationOptions<TData, TVariables> {
  /** Shown via notifySuccess on success. `null` disables. Default: no notification. */
  successMessage?: string | null
  /**
   * Shown via notifyError on failure. Overrides the thrown error's
   * `.message`. `null` disables the toast entirely (caller handles
   * the error). Default: use error's own `.message`.
   */
  errorMessage?: string | null
  /** Fallback if error has no usable `.message`. */
  defaultErrorMessage?: string
  /**
   * Called after success, before `run()` resolves. Awaited — useful for
   * router navigation, refetches, etc. Exceptions here bubble up through
   * the returned `{ success: true }` branch, so keep this side-effect
   * side of things resilient.
   */
  onSuccess?: (data: TData, variables: TVariables) => void | Promise<void>
  /**
   * Called on failure, *before* the default error notification. Return
   * `true` to suppress the default notification (useful when the caller
   * wants to render a field-level error instead of a toast).
   */
  onError?: (error: Error, variables: TVariables) => boolean | void | Promise<boolean | void>
}

export interface SafeMutationResult<TData> {
  success: boolean
  data?: TData
  error?: Error
}

export interface UseSafeMutationReturn<TData, TVariables> {
  /** True while the mutation is in flight. */
  isLoading: Ref<boolean>
  /** Last thrown error (cleared on next `run()` call). */
  error: Ref<Error | null>
  /** Safe wrapper — never throws, always resolves to a result tuple. */
  run: (variables: TVariables) => Promise<SafeMutationResult<TData>>
  /** Pass-through to the wrapped mutation object. */
  mutation: MutationLike<TData, TVariables>
}

export function useSafeMutation<TData, TVariables = unknown>(
  mutation: MutationLike<TData, TVariables>,
  options: UseSafeMutationOptions<TData, TVariables> = {},
): UseSafeMutationReturn<TData, TVariables> {
  const { notifySuccess, notifyError } = useNotify()
  const isLoading = ref(false)
  const error = ref<Error | null>(null)

  async function run(variables: TVariables): Promise<SafeMutationResult<TData>> {
    isLoading.value = true
    error.value = null
    try {
      const data = await mutation.mutateAsync(variables)
      if (options.successMessage) {
        notifySuccess(options.successMessage)
      }
      try {
        await options.onSuccess?.(data, variables)
      } catch (hookErr) {
        // Don't turn success into failure just because a UI side-effect
        // blew up; log so it's visible in dev but keep the mutation's
        // success contract stable.
        // eslint-disable-next-line no-console
        console.error('[useSafeMutation] onSuccess hook threw:', hookErr)
      }
      return { success: true, data }
    } catch (err) {
      const e = err instanceof Error ? err : new Error(String(err ?? 'Unknown error'))
      error.value = e
      let suppressDefault = false
      try {
        suppressDefault = Boolean(await options.onError?.(e, variables))
      } catch (hookErr) {
        // eslint-disable-next-line no-console
        console.error('[useSafeMutation] onError hook threw:', hookErr)
      }
      if (!suppressDefault && options.errorMessage !== null) {
        const msg =
          options.errorMessage ??
          e.message ??
          options.defaultErrorMessage ??
          'Operation failed'
        notifyError(msg)
      }
      return { success: false, error: e }
    } finally {
      isLoading.value = false
    }
  }

  return { run, isLoading, error, mutation }
}

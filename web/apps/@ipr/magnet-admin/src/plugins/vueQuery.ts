import {
  MutationCache,
  QueryCache,
  QueryClient,
  VueQueryPlugin,
  type VueQueryPluginOptions,
} from '@tanstack/vue-query'
import { useSharedAuthStore } from '@shared/stores/authStore'

function isUnauthorized(error: unknown): boolean {
  return (
    typeof error === 'object' &&
    error !== null &&
    'status' in error &&
    (error as { status: number }).status === 401
  )
}

function handleAuthError(error: unknown) {
  if (isUnauthorized(error)) {
    const authStore = useSharedAuthStore()
    authStore.setAuthenticated(false)
    authStore.clearUserInfo()
  }
}

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 60_000,
      refetchOnWindowFocus: false,
      retry: (failureCount, error) => {
        if (isUnauthorized(error)) return false
        return failureCount < 1
      },
    },
  },
  queryCache: new QueryCache({
    onError: handleAuthError,
  }),
  mutationCache: new MutationCache({
    onError: handleAuthError,
  }),
})

export const vueQueryPluginOptions: VueQueryPluginOptions = {
  queryClient,
}

export { VueQueryPlugin }

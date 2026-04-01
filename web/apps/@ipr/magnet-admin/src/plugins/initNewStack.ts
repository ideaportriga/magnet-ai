import type { App } from 'vue'
import { pinia } from './pinia'
import { VueQueryPlugin, vueQueryPluginOptions } from './vueQuery'
import { useAppStore } from '@/stores/appStore'
import { createEntityApis } from '@/api/entityApis'
import { initEntityQueries } from '@/queries/entities'
import { setEntityQueriesOptions } from '@/queries/createEntityQueries'
import { useSharedAuthStore } from '@shared/stores/authStore'

/**
 * Initializes the Pinia + TanStack Query stack.
 */
export async function initNewStack(app: App): Promise<void> {
  // 1. Install Pinia
  app.use(pinia)

  // 2. Install TanStack Vue Query
  app.use(VueQueryPlugin, vueQueryPluginOptions)

  // 3. Load config via Pinia appStore
  const appStore = useAppStore()
  const config = await appStore.loadConfig()

  // 4. Sync config to shared auth store (used by useAuth composable)
  const authStore = useSharedAuthStore()
  authStore.setConfig(config)
  authStore.globalLoading = false

  // 5. Wire global error handler for mutations
  setEntityQueriesOptions({
    onMutationError: (error: unknown, entityKey: string, operation: string) => {
      const isApiError = error && typeof error === 'object' && 'status' in error
      const message = error instanceof Error ? error.message : String(error)
      const body = isApiError ? (error as { body?: string }).body : undefined

      appStore.setErrorMessage({
        text: `Failed to ${operation} ${entityKey.replace(/_/g, ' ')}`,
        technicalError: body || message,
        stack: error instanceof Error ? error.stack : undefined,
        statusCode: isApiError ? (error as { status: number }).status : undefined,
        requestUrl: isApiError ? (error as { requestUrl?: string }).requestUrl : undefined,
      })
    },
  })

  // 6. Create typed API clients for all entities
  const apis = createEntityApis(config.api.aiBridge.urlAdmin, config.credentials)

  // 7. Initialize TanStack Query composables
  initEntityQueries(apis)

  // 8. Expose appStore.config as a global property
  app.config.globalProperties.$appConfig = appStore.config
}

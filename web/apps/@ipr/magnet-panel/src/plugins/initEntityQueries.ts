/**
 * Initialize TanStack Query entity queries for magnet-panel.
 * Reuses the shared API client and entity API factory from magnet-admin's packages.
 *
 * Call after config is loaded (baseUrl and credentials are known).
 */
import { createPanelEntityApis } from '@/api/entityApis'
import { initEntityQueries } from '@/queries/entities'
import { useMainStore } from '@/pinia/modules/main'
import { useAuth } from '@/pinia/modules/auth'
import { createAuthFetch } from '@shared/auth'

export function initPanelEntityQueries() {
  const mainStore = useMainStore()
  const authStore = useAuth()
  const baseUrl = mainStore.endpoint.admin
  const credentials = (mainStore.config?.credentials ?? 'include') as RequestCredentials

  const authBaseUrl = mainStore.config?.api?.aiBridge?.baseUrl ?? ''
  const authFetch = createAuthFetch(authBaseUrl, () => {
    authStore.authenticated = false
    authStore.userInfo = null
  })

  const apis = createPanelEntityApis(baseUrl, credentials, authFetch)
  return initEntityQueries(apis)
}

/**
 * Initialize TanStack Query entity queries for magnet-panel.
 * Reuses the shared API client and entity API factory from magnet-admin's packages.
 *
 * Call after config is loaded (baseUrl and credentials are known).
 */
import { createEntityApis } from '@/api/entityApis'
import { initEntityQueries } from '@/queries/entities'
import { useMainStore } from '@/pinia/modules/main'

export function initPanelEntityQueries() {
  const mainStore = useMainStore()
  const baseUrl = mainStore.endpoint.admin
  const credentials = (mainStore.config?.credentials ?? 'include') as RequestCredentials

  const apis = createEntityApis(baseUrl, credentials)
  return initEntityQueries(apis)
}

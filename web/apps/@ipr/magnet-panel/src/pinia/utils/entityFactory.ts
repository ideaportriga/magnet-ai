import { defineStore } from 'pinia'
import useMainStore from '@/pinia/modules/main'
import { fetchData } from '@shared'

export interface EntityState {
  items: any[]
  loading: boolean
  service: string
}

/**
 * Entity store factory.
 *
 * Creates a Pinia store that fetches entity lists.
 * TanStack Query is now available via `usePanelEntityQueries()` for components
 * that want reactive caching. This factory is kept for backward compatibility
 * with existing components that use `store.items` / `store.getItems()`.
 */
const entityFactory = (entity: string, additional: any) => {
  return defineStore(entity, {
    state: (): EntityState => ({
      items: [],
      loading: false,
      service: entity,
      ...(additional.state || {}),
    }),
    getters: {
      getBy:
        (state: { items: any[] }): any =>
        ({ key, value }: { key: string; value: string }) =>
          state.items.find((item) => item[key] === value),
      endpoint: (): string => {
        const store = useMainStore()
        return store.endpoint.admin
      },
      ...(additional.getters || {}),
    },
    actions: {
      async getItems() {
        // Try TanStack Query first if available
        try {
          const { usePanelEntityQueries } = await import('@/queries/entities')
          const queries = usePanelEntityQueries()
          const entityQueries = (queries as any)[entity]
          if (entityQueries) {
            // TQ is available — just invalidate/refetch the query
            const { useQueryClient } = await import('@tanstack/vue-query')
            const qc = useQueryClient()
            await qc.invalidateQueries({ queryKey: [entity] })
            // Also update local items from the TQ cache
            const cached = qc.getQueryData([entity, 'list', {}]) as any
            if (cached?.items) {
              this.$state.items = cached.items
            }
            return
          }
        } catch {
          // TQ not initialized yet, fall back to legacy fetch
        }

        // Legacy fetch path
        const mainStore = useMainStore()
        this.loading = true
        try {
          const response = await this.get()
          this.$state.items = response
        } catch (error: any) {
          mainStore.setErrorMessage(error)
        } finally {
          this.loading = false
        }
      },
      get: async function () {
        const mainStore = useMainStore()
        return await fetchData({
          credentials: mainStore.config?.credentials,
          endpoint: this.endpoint,
          service: this.service,
        })
          .then(async (response) => {
            const data = await response.json()
            if (response.ok) return data
            if (response.error) throw data
          })
          .catch((res) => {
            throw {
              technicalError: res?.error,
              text: `Error in getting [${this.service}] list`,
            }
          })
      },

      ...(additional.actions || {}),
    },
  })
}

export default entityFactory

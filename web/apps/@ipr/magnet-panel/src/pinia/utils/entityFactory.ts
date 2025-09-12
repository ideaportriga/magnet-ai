import { defineStore } from 'pinia'
import useMainStore from '@/pinia/modules/main'
import { fetchData } from '@shared'

export interface EntityState {
  items: any[]
  loading: boolean
  service: string
}

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

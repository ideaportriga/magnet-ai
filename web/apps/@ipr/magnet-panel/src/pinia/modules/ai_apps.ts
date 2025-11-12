import { defineStore } from 'pinia'
import { useMainStore } from '@/pinia'
import { fetchData } from '@shared'

interface AiAppState {
  app: any
  selectedTab: any | undefined
  selectedChild: any | undefined
}

const useAiApps = defineStore('ai_apps', {
  state: (): AiAppState => ({
    app: undefined,
    selectedTab: undefined,
    selectedChild: undefined,
  }),
  getters: {
    displayTab: (state): any => {
      if (state.selectedTab?.children) {
        return state.selectedChild
      }
      return state.selectedTab
    },
  },
  actions: {
    async getApp(system_name: string) {
      const mainStore = useMainStore()
      const response = await fetchData({
        endpoint: mainStore.endpoint.panel,
        service: `ai_apps/${system_name}`,
        credentials: mainStore.config?.credentials,
      })
      if (response.error) {
        this.app = null
      } else {
        this.app = await response.json()
        if (this.app.tabs?.length > 0) {
          this.selectedTab = this.app.tabs[0]
        }
      }
    },
    async getAgent(system_name: string) {
      const mainStore = useMainStore()
      const response = await fetchData({
        endpoint: mainStore.endpoint.panel,
        service: `ai_apps/agents/${system_name}`,
        credentials: mainStore.config?.credentials,
      })
      if (response.error) {
        this.selectedTab = undefined
      } else {
        const agent = await response.json()
        this.selectedTab = agent
      }
    },
    setSelectedTab(tab: any) {
      this.selectedTab = tab
    },
    setSelectedChild(index: number) {
      this.selectedChild = this.selectedTab.children[index]
    },
  },
})

export default useAiApps

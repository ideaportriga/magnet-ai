import { defineStore } from 'pinia'
import { fetchData } from '@shared'
import { useAuth } from '@/pinia'
import generateConfig from '@/pinia/utils/configGenerator'
declare global {
  interface Window {
    __vite_public_path__?: string
  }
}

interface MainState {
  config: Config | undefined
  errorMessage: { text: string; technicalError?: string } | undefined
  globalLoading: boolean
  sourceSystem: string | undefined
}

export interface Config {
  api: {
    aiBridge: {
      urlCommon: string
      urlAdmin: string
      urlUser: string
    }
    apiRaw: {
      baseUrl: string
    }
  }
  environment: string
  credentials: string
  panel: {
    baseUrl: string
  }
  admin: {
    baseUrl: string
  }
}

export const useMainStore = defineStore('main', {
  state: (): MainState => ({
    config: undefined,
    errorMessage: undefined,
    globalLoading: true,
    sourceSystem: undefined,
  }),

  getters: {
    baseUrl: (state): string => {
      if (!state.config) return ''
      return state.config?.api?.aiBridge?.urlCommon
    },
    endpoint(): { admin: string; panel: string } {
      return {
        admin: this.config?.api?.aiBridge?.urlAdmin ?? '',
        panel: this.config?.api?.aiBridge?.urlUser ?? '',
      }
    },
  },

  actions: {
    async loadConfig() {
      this.globalLoading = true
      try {
        const jsonConfigFileName = 'config/main.json'
        const response = await fetchData({
          endpoint: `${window.__vite_public_path__ ?? ''}${jsonConfigFileName}`,
        })

        if (response.ok) {
          this.config = generateConfig(await response.json())
          await useAuth().init(this.config)
        }
      } catch (error) {
        this.errorMessage = { text: 'Failed to load config' }
      } finally {
        this.globalLoading = false
      }
    },
    setErrorMessage(errorMessage: { text: string; technicalError: string }) {
      this.errorMessage = errorMessage
    },
  },
})

export default useMainStore

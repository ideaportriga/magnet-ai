import { defineStore } from 'pinia'
import { fetchData } from '@shared'
const LOCAL_STORAGE_KEY = 'userInfo'

type AuthConfig = {
  enabled: boolean
  provider: string
  popup: {
    width: string
    height: string
  }
}

interface AuthState {
  baseUrl: string | undefined
  authConfig: AuthConfig
  authenticated: boolean
  authCheckInProgress: boolean
  userInfo: any
  credentials: string
}

const useAuth = defineStore('auth', {
  state: (): AuthState => ({
    baseUrl: undefined,
    credentials: 'include',
    authConfig: {
      enabled: false,
      provider: '',
      popup: {
        width: '',
        height: '',
      },
    },
    authenticated: false,
    authCheckInProgress: false,
    userInfo: JSON.parse(localStorage.getItem(LOCAL_STORAGE_KEY) || '{}') || {},
  }),
  getters: {
    authEnabled: (state): boolean => {
      return state.authConfig.enabled
    },

    authRequired: (state): boolean => {
      return state.authConfig.enabled && !state.authenticated
    },
  },
  actions: {
    async init(config: any) {
      this.baseUrl = config.api.aiBridge.baseUrl
      this.authConfig = config.auth

      if (this.authRequired) {
        await this.getAuthData()
      }
    },
    async getAuthData() {
      this.authCheckInProgress = true
      const response = await fetch(`${this.baseUrl}/auth/me`, { credentials: 'include' })
      if (response.ok) {
        this.authenticated = true
        this.userInfo = await response.json()
      }
      this.authCheckInProgress = false
    },
    async completeAuth(body: any) {
      const response = await fetchData({
        method: 'POST',
        endpoint: `${this.baseUrl}/auth/complete`,
        credentials: this.credentials,
        headers: {
          'Content-Type': 'application/json',
        },
        body,
      })
      if (!response.ok) {
        // mainStore.setErrorMessage({
        //   technicalError: response?.error,
        //   text: `Error in completing auth`,
        // })
      }

      if (response.ok) {
        this.getAuthData()
        return true
      }
      return false
    },
  },
})

export default useAuth

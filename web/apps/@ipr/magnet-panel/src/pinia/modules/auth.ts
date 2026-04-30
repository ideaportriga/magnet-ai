import { defineStore } from 'pinia'
import { createAuthClient, type AuthClient, type UserInfo } from '@shared/auth'

type AuthConfig = {
  enabled: boolean
  provider: string
  providers?: Array<string | { name: string; type: string; displayName?: string }>
  signupEnabled?: boolean
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
  userInfo: UserInfo | null
  credentials: string
  mfaRequired: boolean
  client: AuthClient | null
}

const useAuth = defineStore('auth', {
  state: (): AuthState => ({
    baseUrl: undefined,
    credentials: 'include',
    authConfig: {
      enabled: false,
      provider: '',
      providers: [],
      signupEnabled: false,
      popup: {
        width: '',
        height: '',
      },
    },
    authenticated: false,
    authCheckInProgress: false,
    userInfo: null,
    mfaRequired: false,
    client: null,
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
      this.client = createAuthClient(this.baseUrl || '')

      if (!this.authEnabled) return
      // Run independently so a transient failure in one endpoint doesn't
      // leave the app stuck on the spinner. `getAuthData` already swallows
      // its own errors via try/finally; `loadProviders` has its own catch.
      await this.getAuthData()
      await this.loadProviders()
    },

    async loadProviders() {
      if (!this.client) return
      try {
        const list = await this.client.getProviders()
        this.authConfig.providers = list
      } catch { /* providers endpoint unavailable */ }
    },

    async getAuthData() {
      if (!this.client) return
      this.authCheckInProgress = true
      try {
        const userInfo = await this.client.me()
        if (userInfo) {
          this.authenticated = true
          this.userInfo = userInfo
        }
      } finally {
        // Guarantee the spinner clears even if `me()` throws — otherwise
        // App.vue would render `<km-loader>` forever.
        this.authCheckInProgress = false
      }
    },

    async loginLocal(email: string, password: string) {
      if (!this.client) return
      const result = await this.client.loginLocal(email, password)
      if (result.mfa_required) {
        this.mfaRequired = true
        return
      }
      this.mfaRequired = false
      this.authenticated = true
      await this.getAuthData()
    },

    async verifyMfa(code: string) {
      if (!this.client) return
      await this.client.verifyMfa(code)
      this.mfaRequired = false
      this.authenticated = true
      await this.getAuthData()
    },

    async signup(email: string, password: string, name?: string) {
      if (!this.client) return
      return await this.client.signup(email, password, name)
    },

    async logout() {
      if (!this.client) return
      await this.client.logout()
      this.authenticated = false
      this.userInfo = null
      this.mfaRequired = false
    },
  },
})

export default useAuth

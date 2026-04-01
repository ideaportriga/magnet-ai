import { defineStore } from 'pinia'
import { createAuthClient, type AuthClient, type UserInfo } from '@shared/auth'

type AuthConfig = {
  enabled: boolean
  provider: string
  providers?: string[]
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
      this.client = createAuthClient(this.baseUrl!)

      if (this.authEnabled) {
        await this.getAuthData()
      }
    },

    async getAuthData() {
      if (!this.client) return
      this.authCheckInProgress = true
      const userInfo = await this.client.me()
      if (userInfo) {
        this.authenticated = true
        this.userInfo = userInfo
      }
      this.authCheckInProgress = false
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

    async completeAuth(body: any) {
      if (!this.client) return false
      const ok = await this.client.completeOidc(body)
      if (ok) {
        await this.getAuthData()
        return true
      }
      return false
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

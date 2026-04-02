import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export interface AuthUserInfo {
  user_id?: string
  email?: string
  preferred_username?: string
  name?: string
  roles?: string[]
  is_verified?: boolean
  is_two_factor_enabled?: boolean
  last_login_at?: string
  oauth_accounts?: Array<{ provider: string; [key: string]: unknown }>
  [key: string]: unknown
}

export interface AuthAppConfig {
  auth?: {
    enabled?: boolean
    [key: string]: unknown
  }
  api?: {
    aiBridge?: {
      baseUrl?: string
      urlAdmin?: string
      [key: string]: unknown
    }
    [key: string]: unknown
  }
  credentials?: Record<string, unknown>
  [key: string]: unknown
}

/**
 * Shared auth store — used by both magnet-admin and magnet-panel.
 * Replaces the Vuex state that useAuth() previously depended on.
 */
export const useSharedAuthStore = defineStore('sharedAuth', () => {
  const authenticated = ref(false)
  const userInfo = ref<AuthUserInfo | null>(null)
  const globalLoading = ref(true)
  const errorMessage = ref<string | null>(null)

  // Config is injected from the app's own config store
  const config = ref<AuthAppConfig | null>(null)

  const authEnabled = computed(() => config.value?.auth?.enabled ?? true)
  const apiBaseUrl = computed(() => config.value?.api?.aiBridge?.baseUrl ?? '')

  function setConfig(cfg: AuthAppConfig) {
    config.value = cfg
  }

  function setAuthenticated(val: boolean) {
    authenticated.value = val
  }

  function setUserInfo(info: AuthUserInfo) {
    userInfo.value = info
  }

  function clearUserInfo() {
    userInfo.value = null
  }

  return {
    authenticated,
    userInfo,
    globalLoading,
    errorMessage,
    config,
    authEnabled,
    apiBaseUrl,
    setConfig,
    setAuthenticated,
    setUserInfo,
    clearUserInfo,
  }
})

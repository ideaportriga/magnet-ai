import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

/**
 * Shared auth store — used by both magnet-admin and magnet-panel.
 * Replaces the Vuex state that useAuth() previously depended on.
 */
export const useSharedAuthStore = defineStore('sharedAuth', () => {
  const authenticated = ref(false)
  const userInfo = ref(null)
  const globalLoading = ref(true)
  const errorMessage = ref(null)

  // Config is injected from the app's own config store
  const config = ref(null)

  const authEnabled = computed(() => config.value?.auth?.enabled ?? true)
  const apiBaseUrl = computed(() => config.value?.api?.aiBridge?.baseUrl ?? '')

  function setConfig(cfg) {
    config.value = cfg
  }

  function setAuthenticated(val) {
    authenticated.value = val
  }

  function setUserInfo(info) {
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

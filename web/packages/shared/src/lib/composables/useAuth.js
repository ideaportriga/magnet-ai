import { ref, computed } from 'vue'
import { useStore } from 'vuex'

export default function useAuth() {
  const store = useStore()

  const authEnabled = computed(() => store.getters.config.auth?.enabled ?? true)
  const authenticated = computed(() => store.getters.authenticated)
  const apiBaseUrl = store.getters.config.api.aiBridge.baseUrl

  const authRequired = computed(() => {
    return authEnabled.value && !authenticated.value
  })
  const authCheckInProgress = ref(false)

  async function getAuthData() {
    authCheckInProgress.value = true
    const response = await fetch(`${apiBaseUrl}/auth/me`, { credentials: 'include' })

    if (response.ok) {
      store.commit('set', { authenticated: true })

      const data = await response.json()

      store.commit('setUserInfo', data)

      console.log('User info:', data)
    }

    authCheckInProgress.value = false
  }

  async function logout() {
    const response = await fetch(`${apiBaseUrl}/auth/logout`, { method: 'POST', credentials: 'include' })

    if (response.ok) {
      store.commit('set', { authenticated: false })
    }
  }

  return {
    authCheckInProgress,
    authRequired,
    getAuthData,
    logout,
  }
}

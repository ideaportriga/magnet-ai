import { ref, computed } from 'vue'
import { useSharedAuthStore } from '../stores/authStore'
import { createAuthClient } from '../auth'

export default function useAuth() {
  const authStore = useSharedAuthStore()

  const authEnabled = computed(() => authStore.authEnabled)
  const authenticated = computed(() => authStore.authenticated)
  const apiBaseUrl = computed(() => authStore.apiBaseUrl)

  const authRequired = computed(() => {
    return authEnabled.value && !authenticated.value
  })
  const authCheckInProgress = ref(false)

  // Reactive auth client — recreated when baseUrl changes
  const client = computed(() => {
    const url = apiBaseUrl.value
    if (url == null) return null
    return createAuthClient(url)
  })

  async function getAuthData() {
    if (!client.value) return

    authCheckInProgress.value = true
    const userInfo = await client.value.me()

    if (userInfo) {
      authStore.setAuthenticated(true)
      authStore.setUserInfo(userInfo)
    }

    authCheckInProgress.value = false
  }

  async function loginLocal(email, password) {
    if (!client.value) throw new Error('Auth client not initialized')

    const result = await client.value.loginLocal(email, password)
    if (result.mfa_required) {
      return { mfaRequired: true }
    }
    authStore.setAuthenticated(true)
    await getAuthData()
    return { mfaRequired: false }
  }

  async function verifyMfa(code) {
    if (!client.value) throw new Error('Auth client not initialized')

    await client.value.verifyMfa(code)
    authStore.setAuthenticated(true)
    await getAuthData()
  }

  async function logout() {
    if (client.value) {
      await client.value.logout()
    }
    authStore.setAuthenticated(false)
    authStore.clearUserInfo()
  }

  return {
    authCheckInProgress,
    authRequired,
    authEnabled,
    authenticated,
    client,
    getAuthData,
    loginLocal,
    verifyMfa,
    logout,
  }
}

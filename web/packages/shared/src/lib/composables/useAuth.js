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
    const url = apiBaseUrl.value || ''
    return createAuthClient(url)
  })

  async function getAuthData() {
    authCheckInProgress.value = true
    const userInfo = await client.value.me()

    if (userInfo) {
      authStore.setAuthenticated(true)
      authStore.setUserInfo(userInfo)
    }

    authCheckInProgress.value = false
  }

  async function loginLocal(email, password) {
    const result = await client.value.loginLocal(email, password)
    if (result.mfa_required) {
      return { mfaRequired: true }
    }
    authStore.setAuthenticated(true)
    await getAuthData()
    return { mfaRequired: false }
  }

  async function verifyMfa(code) {
    await client.value.verifyMfa(code)
    authStore.setAuthenticated(true)
    await getAuthData()
  }

  async function logout() {
    await client.value.logout()
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

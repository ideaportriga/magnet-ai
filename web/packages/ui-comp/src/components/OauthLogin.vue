<template lang="pug">
.flex.flex-center.full-height
  .column.items-center.auth-container
    .row
      km-icon(:name='"magnet"', width='23', height='25')
      .km-heading-7.logo-text.q-ml-sm Magnet AI
    km-btn.q-mt-md(bg='primary', color='border', :label='loginButtonText', @click='login', :disable='loginInProgress')
</template>

<script>
import { ref, computed, onUnmounted, inject } from 'vue'
import { useAuth } from '@shared'

export default {
  emits: ['auth-completed'],
  setup(props, { emit }) {
    // Try Pinia appStore (magnet-admin), fall back to Vuex (magnet-panel)
    const appStore = inject('appStore', null)
    let config
    config = appStore?.config ?? {}

    const apiBaseUrl = config?.api?.aiBridge?.baseUrl ?? ''
    const oAuthProvider = config?.auth?.provider ?? 'Microsoft'
    const oAuthPopupWidth = config?.auth?.popup?.width ?? '600'
    const oAuthPopupHeight = config?.auth?.popup?.height ?? '400'
    const auth = useAuth()

    const loginWindow = ref()
    const loginInProgress = ref(false)
    const loginButtonText = computed(() => {
      return loginInProgress.value ? `Logging in with ${oAuthProvider} ...` : `Log in with ${oAuthProvider}`
    })
    const tokenReceived = ref(false)
    let loginWindowClosedCheckInterval

    function receiveMessageFromPopup(event) {
      const eventData = JSON.parse(event.data)

      window.removeEventListener('message', receiveMessageFromPopup)

      tokenReceived.value = true

      const fetchData = {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(eventData),
      }

      fetch(`${apiBaseUrl}/auth/complete`, fetchData).then((response) => {
        loginInProgress.value = false

        if (!response.ok) {
          throw new Error('Auth failed')
        }

        if (response.ok) {
          auth.getAuthData()
        }

        emit('auth-completed')
      })
    }

    onUnmounted(() => {
      window.removeEventListener('message', receiveMessageFromPopup)
      clearInterval(loginWindowClosedCheckInterval)
    })

    function login() {
      if (loginInProgress.value) {
        return
      }

      loginInProgress.value = true
      loginWindow.value = window.open(
        `${apiBaseUrl}/auth/login`,
        'popupLoginWithOAuthProvider',
        `width=${oAuthPopupWidth},height=${oAuthPopupHeight}`
      )

      window.addEventListener('message', receiveMessageFromPopup)

      loginWindowClosedCheckInterval = setInterval(() => {
        if (tokenReceived.value) {
          clearInterval(loginWindowClosedCheckInterval)
          return
        }

        if (loginWindow.value?.closed) {
          loginInProgress.value = false
          clearInterval(loginWindowClosedCheckInterval)
          window.removeEventListener('message', receiveMessageFromPopup)
        }
      }, 500)
    }

    return {
      loginButtonText,
      loginInProgress,
      login,
    }
  },
  computed: {},
  watch: {
    loading: {
      immediate: true,
      handler(val) {
        if (val) {
          this.$q.loading.show()
        } else {
          this.$q.loading.hide()
        }
      },
    },
  },
  created() {},
  methods: {},
}
</script>

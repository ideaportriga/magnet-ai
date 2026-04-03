<template lang="pug">
.full-height.full-width(:class='{ "no-wrap column": $route.query.viewMode === "panel" || ai_app }')
  //- Show spinner during initial config load or auth check
  template(v-if='initialLoading || authCheckInProgress')
    .flex.flex-center.full-height
      q-spinner(size='30px', color='primary')
  template(v-else-if='authRequired')
      template(v-if='authClient')
        auth-signup-page(
          v-if='authPage === "signup"',
          :auth-client='authClient',
          @navigate='authPage = $event'
        )
        auth-forgot-password(
          v-else-if='authPage === "forgot-password"',
          :auth-client='authClient',
          @navigate='authPage = $event'
        )
        auth-login-page(
          v-else,
          :auth-client='authClient',
          :providers='authProviders',
          :signup-enabled='signupEnabled',
          :oidc-base-url='oidcBaseUrl',
          :popup-width='popupWidth',
          :popup-height='popupHeight',
          @success='onAuthCompleted',
          @navigate='authPage = $event'
        )
      oauth-login(v-else, @auth-completed='onAuthCompleted')
  template(v-else-if='!hasAdminAccess')
    .flex.flex-center.full-height
      .column.items-center.q-pa-xl(style='max-width: 480px')
        q-icon(name='fas fa-lock', size='48px', color='grey-5')
        .text-h6.q-mt-md.text-center Access restricted
        .text-body2.text-grey.q-mt-sm.text-center
          | Your account does not have sufficient permissions to access the admin panel.
          | Please contact your administrator to request access.
        .text-caption.text-grey.q-mt-md Logged in as {{ userDisplayName }}
        q-btn.q-mt-lg(
          outline,
          color='primary',
          label='Log out',
          no-caps,
          @click='handleLogout'
        )
  template(v-else)
    layout-default
  km-error-dialog(v-if='appStore.errorMessage')
  template(v-if='env === "development"')
    .fixed-bottom-right.q-pa-sm.row(:style='{ zIndex: 100 }')
</template>

<script>
import { useState } from '@shared'
import { useAuth } from '@shared'
import { getCurrentInstance, computed, ref } from 'vue'
import { useAppStore } from '@/stores/appStore'
import { useSharedAuthStore } from '@shared/stores/authStore'
import { queryClient } from '@/plugins/vueQuery'
import { entityKeys } from '@/queries/queryKeys'
import { getEntityApis, getApiClient } from '@/api/entityApis'
import { initializePlugins } from '@/config/collections/collections'
import AuthLoginPage from '@ui/components/auth/AuthLoginPage.vue'
import AuthSignupPage from '@ui/components/auth/AuthSignupPage.vue'
import AuthForgotPassword from '@ui/components/auth/AuthForgotPassword.vue'

export default {
  components: { AuthLoginPage, AuthSignupPage, AuthForgotPassword },
  setup() {
    const loading = useState('globalLoading')
    const auth = useAuth()
    const appStore = useAppStore()
    const { appContext } = getCurrentInstance()

    // useAuth stores userInfo in sharedAuthStore — read from there
    const sharedAuth = useSharedAuthStore()

    const initialLoading = ref(true)
    const authPage = ref('login')

    const authClient = computed(() => auth.client.value)
    const authProviders = computed(() => appStore.config?.auth?.providers || [])

    const hasAdminAccess = computed(() => {
      const userInfo = sharedAuth.userInfo
      if (!userInfo) return false
      const roles = userInfo.roles || []
      return roles.includes('admin')
    })
    const userDisplayName = computed(() => {
      const u = sharedAuth.userInfo
      return u?.name || u?.email || u?.preferred_username || ''
    })

    async function handleLogout() {
      await auth.logout()
    }
    const signupEnabled = computed(() => appStore.config?.auth?.signupEnabled || false)
    const oidcBaseUrl = computed(() => appStore.config?.api?.aiBridge?.baseUrl || '')
    const popupWidth = computed(() => appStore.config?.auth?.popup?.width || '600')
    const popupHeight = computed(() => appStore.config?.auth?.popup?.height || '400')

    return {
      initialLoading,
      authPage,
      authClient,
      hasAdminAccess,
      userDisplayName,
      handleLogout,
      authProviders,
      signupEnabled,
      oidcBaseUrl,
      popupWidth,
      popupHeight,
      loading,
      appContext,
      appStore,
      sharedAuth,
      ...auth,
    }
  },
  computed: {
    ai_app() {
      return this.$route.query.ai_app || window?.magnetai_ai_app
    },
    openTest() {
      return true
    },
    theme() {
      return this.appContext.config.globalProperties.$theme ?? 'default'
    },
  },
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
  async created() {
    // Config is loaded by initNewStack (Pinia appStore.loadConfig) in main.js

    // Check if user already has a valid session (cookie)
    if (this.authEnabled) {
      // Try authClient first (available when baseUrl is set)
      await this.getAuthData()

      // Fallback for OIDC mode (empty baseUrl → authClient is null):
      // call /auth/me directly to restore session from HttpOnly cookies.
      if (!this.authenticated && !this.authClient) {
        try {
          const baseUrl = this.appStore?.config?.api?.aiBridge?.baseUrl ?? ''
          const resp = await fetch(`${baseUrl}/auth/me`, { credentials: 'include' })
          if (resp.ok) {
            const userInfo = await resp.json()
            this.sharedAuth.setAuthenticated(true)
            this.sharedAuth.setUserInfo(userInfo)
          }
        } catch {
          // No valid session
        }
      }
    }

    this.initialLoading = false

    if (!this.authRequired && this.hasAdminAccess) {
      await this.loadData()
    }
  },

  methods: {
    async loadData() {
      const apis = getEntityApis()
      const client = getApiClient()

      // Prefetch plugins first (needed for dynamic forms)
      await queryClient.fetchQuery({
        queryKey: entityKeys.plugins.list({}),
        queryFn: () => apis.plugins.list(),
      })

      // Initialize plugins configuration for collections (uses data from cache)
      initializePlugins()

      // Prefetch catalog (lightweight list of all entities for dropdowns, filters, tab names)
      await queryClient.fetchQuery({
        queryKey: ['catalog'],
        queryFn: () => client.get('catalog'),
        staleTime: 5 * 60 * 1000,
      })
    },
    async onAuthCompleted() {
      await this.getAuthData()
      if (this.hasAdminAccess) {
        await this.loadData()
      }
    },
  },
}
</script>
